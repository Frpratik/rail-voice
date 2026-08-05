export interface OfflineReportItem {
  id: string;
  title: string;
  description: string;
  station_id: string;
  category_code?: string;
  photoBlob?: Blob;
  createdAt: number;
  status: 'queued' | 'syncing' | 'failed';
  errorMessage?: string;
}

const DB_NAME = 'railvoice_offline_db';
const DB_VERSION = 1;
const STORE_NAME = 'queued_reports';

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.indexedDB) {
      reject(new Error('IndexedDB is not supported in this environment'));
      return;
    }
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function saveOfflineReport(item: OfflineReportItem): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req = store.put(item);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function getOfflineReports(): Promise<OfflineReportItem[]> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });
  } catch {
    return [];
  }
}

export async function removeOfflineReport(id: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req = store.delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function drainOfflineQueue(
  apiBaseUrl: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
): Promise<{ synced: number; failed: number }> {
  const items = await getOfflineReports();
  if (items.length === 0) return { synced: 0, failed: 0 };

  let synced = 0;
  let failed = 0;

  for (const item of items) {
    try {
      item.status = 'syncing';
      await saveOfflineReport(item);

      const payload = {
        title: item.title,
        description: item.description,
        station_id: item.station_id,
        category_code: item.category_code || undefined,
        force_create: true,
        divergence_reason: 'Submitted via Offline-First PWA Background Sync',
      };

      const res = await fetch(`${apiBaseUrl}/issues`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': item.id,
        },
        body: JSON.stringify(payload),
      });

      if (res.ok || res.status === 201) {
        const json = await res.json();
        const createdIssueId = json.data?.issue?.id;

        // If photo exists, upload photo
        if (item.photoBlob && createdIssueId) {
          const formData = new FormData();
          formData.append('file', item.photoBlob, 'offline_photo.jpg');
          await fetch(`${apiBaseUrl}/issues/${createdIssueId}/photos`, {
            method: 'POST',
            body: formData,
          });
        }

        await removeOfflineReport(item.id);
        synced++;
      } else {
        const errJson = await res.json().catch(() => ({}));
        item.status = 'failed';
        item.errorMessage = errJson.detail || `Server HTTP ${res.status}`;
        await saveOfflineReport(item);
        failed++;
      }
    } catch (err: unknown) {
      item.status = 'failed';
      item.errorMessage = err instanceof Error ? err.message : 'Network sync failed';
      await saveOfflineReport(item);
      failed++;
    }
  }

  return { synced, failed };
}
