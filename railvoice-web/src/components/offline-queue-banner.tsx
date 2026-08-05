'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { WifiOff, RefreshCw, CheckCircle, Layers, Trash2 } from 'lucide-react';
import { getOfflineReports, drainOfflineQueue, removeOfflineReport, OfflineReportItem } from '@/lib/offline-queue';

export function OfflineQueueBanner() {
  const [isOnline, setIsOnline] = useState(() => typeof window !== 'undefined' ? navigator.onLine : true);
  const [queue, setQueue] = useState<OfflineReportItem[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [showDrawer, setShowDrawer] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);

  const refreshQueue = useCallback(async () => {
    const items = await getOfflineReports();
    setQueue(items);
  }, []);

  const handleSync = useCallback(async () => {
    if (isSyncing || queue.length === 0) return;
    setIsSyncing(true);
    setSyncStatus('Syncing offline reports...');
    try {
      const result = await drainOfflineQueue();
      if (result.synced > 0) {
        setSyncStatus(`Successfully uploaded ${result.synced} offline report(s)!`);
      } else if (result.failed > 0) {
        setSyncStatus(`Failed to upload ${result.failed} report(s).`);
      }
      await refreshQueue();
    } catch (err: unknown) {
      setSyncStatus(`Sync error: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsSyncing(false);
    }
  }, [isSyncing, queue.length, refreshQueue]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    setTimeout(() => {
      void refreshQueue();
    }, 0);

    const handleOnline = () => {
      setIsOnline(true);
      handleSync();
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    const handleSWMessage = (event: MessageEvent) => {
      if (event.data?.type === 'SYNC_OFFLINE_QUEUE') {
        handleSync();
      }
    };

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', handleSWMessage);
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.removeEventListener('message', handleSWMessage);
      }
    };
  }, [handleSync, refreshQueue]);

  if (isOnline && queue.length === 0 && !syncStatus) {
    return null;
  }

  return (
    <div className="sticky top-0 z-50 w-full border-b border-amber-500/20 bg-slate-950/95 backdrop-blur-md px-4 py-2 text-xs font-medium text-slate-200">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          {!isOnline ? (
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse">
              <WifiOff className="h-3.5 w-3.5" />
            </div>
          ) : queue.length > 0 ? (
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              <Layers className="h-3.5 w-3.5" />
            </div>
          ) : (
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              <CheckCircle className="h-3.5 w-3.5" />
            </div>
          )}

          <div>
            <span className="font-semibold text-slate-100">
              {!isOnline
                ? '⚡ Offline Mode'
                : queue.length > 0
                ? `${queue.length} Report(s) Queued Offline`
                : 'Connection Restored'}
            </span>
            <span className="ml-2 text-slate-400 hidden sm:inline">
              {!isOnline
                ? 'Reports captured now will auto-sync when cellular signal resumes.'
                : syncStatus || 'Connected to Indian Railways grid.'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {queue.length > 0 && (
            <button
              onClick={() => setShowDrawer(!showDrawer)}
              className="rounded-lg bg-slate-800/80 px-2.5 py-1 text-slate-300 hover:bg-slate-800 transition-colors border border-slate-700"
            >
              {showDrawer ? 'Hide Queue' : `View Queue (${queue.length})`}
            </button>
          )}

          {isOnline && queue.length > 0 && (
            <button
              onClick={handleSync}
              disabled={isSyncing}
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1 text-white hover:bg-indigo-500 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-3 w-3 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isSyncing ? 'Syncing...' : 'Sync Now'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Offline Queue Drawer */}
      {showDrawer && queue.length > 0 && (
        <div className="mx-auto max-w-7xl mt-3 border-t border-slate-800 pt-3 pb-1 space-y-2">
          {queue.map((item) => (
            <div
              key={item.id}
              className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/90 p-3"
            >
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-200">{item.title}</span>
                  <span
                    className={`rounded px-1.5 py-0.5 text-[10px] uppercase font-bold ${
                      item.status === 'syncing'
                        ? 'bg-amber-500/20 text-amber-400'
                        : item.status === 'failed'
                        ? 'bg-rose-500/20 text-rose-400'
                        : 'bg-indigo-500/20 text-indigo-400'
                    }`}
                  >
                    {item.status}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-1">{item.description}</p>
                {item.errorMessage && <p className="text-[10px] text-rose-400">{item.errorMessage}</p>}
              </div>

              <button
                onClick={async () => {
                  await removeOfflineReport(item.id);
                  refreshQueue();
                }}
                className="p-1.5 text-slate-500 hover:text-rose-400 transition-colors"
                title="Discard Draft"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
