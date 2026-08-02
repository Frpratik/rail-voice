import type {
  ApiEnvelope,
  Comment,
  DashboardData,
  DuplicateCheckResult,
  Issue,
  ManagedUser,
  NotificationItem,
  Officer,
  PaginationMeta,
  Photo,
  Station,
  TimelineEvent,
  User,
  UserAuditRow,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === "development"
    ? "http://localhost:8000/api/v1"
    : "/api/v1");

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("refresh_token");
}

function ensureAnonymousSession(): string {
  if (typeof window === "undefined") return "";
  let anon = localStorage.getItem("anonymous_session_id");
  if (!anon) {
    anon = crypto.randomUUID();
    localStorage.setItem("anonymous_session_id", anon);
  }
  return anon;
}

let refreshPromise: Promise<string | null> | null = null;

async function doRefreshToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      credentials: "include",
    });

    if (!res.ok) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      }
      return null;
    }

    const body = await res.json();
    const data = body?.data;
    if (data?.access_token) {
      if (typeof window !== "undefined") {
        localStorage.setItem("access_token", data.access_token);
        if (data.refresh_token) {
          localStorage.setItem("refresh_token", data.refresh_token);
        }
      }
      return data.access_token as string;
    }
  } catch {
    // Ignore network error during silent refresh
  }
  return null;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { _isRetry?: boolean } = {}
): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  const isFormData =
    typeof FormData !== "undefined" && options.body instanceof FormData;

  if (options.body != null && !isFormData && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  } else if (method !== "GET" && method !== "HEAD") {
    headers["X-Anonymous-Session"] = ensureAnonymousSession();
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });

  if (res.status === 204) {
    return undefined as T;
  }

  const body = await res.json().catch(() => ({}));

  if (!res.ok) {
    if (
      res.status === 401 &&
      !options._isRetry &&
      !path.startsWith("/auth/otp") &&
      !path.startsWith("/auth/refresh")
    ) {
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        if (!refreshPromise) {
          refreshPromise = doRefreshToken().finally(() => {
            refreshPromise = null;
          });
        }
        const newToken = await refreshPromise;
        if (newToken) {
          return apiFetch<T>(path, {
            ...options,
            headers: {
              ...(options.headers as Record<string, string>),
              Authorization: `Bearer ${newToken}`,
            },
            _isRetry: true,
          });
        }
      }
    }

    const detail = body.detail ?? body.error;
    const message =
      typeof detail === "string"
        ? detail
        : detail?.message ?? "Request failed";
    const code = typeof detail === "object" ? detail?.code : undefined;
    throw new ApiError(message, res.status, code, detail);
  }

  return body as T;
}

async function downloadAuthed(path: string, filename: string) {
  const headers: Record<string, string> = {};
  const token = getAccessToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    headers,
    credentials: "include",
  });
  if (!res.ok) throw new ApiError("Download failed", res.status);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export const api = {
  stations: {
    list: (params?: { zone_code?: string; search?: string }) => {
      const q = new URLSearchParams();
      if (params?.zone_code) q.set("zone_code", params.zone_code);
      if (params?.search) q.set("search", params.search);
      const qs = q.toString();
      return apiFetch<ApiEnvelope<Station[]>>(`/stations${qs ? `?${qs}` : ""}`);
    },
    get: (code: string) =>
      apiFetch<ApiEnvelope<Station>>(`/stations/${code}`),
  },

  auth: {
    requestOtp: (mobile: string) =>
      apiFetch<ApiEnvelope<{ message: string; mock_otp?: string }>>(
        "/auth/otp/request",
        { method: "POST", body: JSON.stringify({ mobile }) }
      ),
    verifyOtp: (mobile: string, otp: string) =>
      apiFetch<
        ApiEnvelope<{
          access_token: string;
          refresh_token?: string;
          expires_in: number;
          user: User;
        }>
      >("/auth/otp/verify", {
        method: "POST",
        body: JSON.stringify({ mobile, otp }),
      }),
    google: (payload: {
      id_token: string;
      email?: string;
      name?: string;
      google_id?: string;
      avatar_url?: string;
    }) =>
      apiFetch<
        ApiEnvelope<{
          access_token: string;
          refresh_token?: string;
          expires_in: number;
          user: User;
        }>
      >("/auth/google", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    refresh: () =>
      apiFetch<
        ApiEnvelope<{
          access_token: string;
          refresh_token?: string;
          expires_in: number;
          user: User;
        }>
      >("/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh_token: getRefreshToken() }),
      }),
    anonymous: () =>
      apiFetch<
        ApiEnvelope<{
          anonymous_session_id: string;
          limits: { issues_per_24h: number; issues_remaining: number };
        }>
      >("/auth/anonymous", { method: "POST" }),
    logout: () => apiFetch<void>("/auth/logout", { method: "POST" }),
  },

  issues: {
    list: (params?: { station_code?: string; sort?: string; limit?: number }) => {
      const q = new URLSearchParams();
      if (params?.station_code) q.set("station_code", params.station_code);
      if (params?.sort) q.set("sort", params.sort);
      if (params?.limit) q.set("limit", String(params.limit));
      const qs = q.toString();
      return apiFetch<
        ApiEnvelope<{
          items: Issue[];
          pagination: { has_more: boolean; total_count: number };
        }>
      >(`/issues${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) =>
      apiFetch<
        ApiEnvelope<{
          issue: Issue;
          timeline: TimelineEvent[];
          comments: Comment[];
        }>
      >(`/issues/${id}`),
    checkDuplicates: (data: {
      description: string;
      station_id: string;
      title?: string;
    }) =>
      apiFetch<ApiEnvelope<DuplicateCheckResult>>("/issues/check-duplicates", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    create: (data: Record<string, unknown>) =>
      apiFetch<ApiEnvelope<{ issue: Issue }>>("/issues", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    support: (id: string) =>
      apiFetch<
        ApiEnvelope<{
          issue_id: string;
          support_count: number;
          message: string;
        }>
      >(`/issues/${id}/support`, { method: "POST" }),
    listComments: (id: string) =>
      apiFetch<ApiEnvelope<Comment[]>>(`/issues/${id}/comments`),
    addComment: (id: string, body: string, parent_id?: string) =>
      apiFetch<ApiEnvelope<Comment>>(`/issues/${id}/comments`, {
        method: "POST",
        body: JSON.stringify({ body, parent_id }),
      }),
    uploadPhoto: async (id: string, file: File) => {
      const form = new FormData();
      form.append("file", file);
      return apiFetch<ApiEnvelope<Photo>>(`/issues/${id}/photos`, {
        method: "POST",
        body: form,
      });
    },
  },

  notifications: {
    list: () =>
      apiFetch<
        ApiEnvelope<{ items: NotificationItem[]; unread_count: number }>
      >("/notifications"),
    markRead: (id: string) =>
      apiFetch<ApiEnvelope<NotificationItem>>(`/notifications/${id}/read`, {
        method: "PATCH",
      }),
    markAllRead: () =>
      apiFetch<ApiEnvelope<{ marked: number }>>("/notifications/read-all", {
        method: "POST",
      }),
  },

  admin: {
    dashboard: () => apiFetch<ApiEnvelope<DashboardData>>("/admin/dashboard"),
    issues: (status?: string) => {
      const q = status ? `?status_filter=${status}` : "";
      return apiFetch<ApiEnvelope<{ items: Issue[] }>>(`/admin/issues${q}`);
    },
    updateStatus: (id: string, data: { status: string; remarks: string }) =>
      apiFetch<ApiEnvelope<unknown>>(`/admin/issues/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ ...data, visibility: "public" }),
      }),
    assign: (id: string, data: { assignee_id: string; remarks: string }) =>
      apiFetch<ApiEnvelope<unknown>>(`/admin/issues/${id}/assign`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    escalate: (
      id: string,
      data: { target: "station_manager" | "division" | "zone"; remarks: string }
    ) =>
      apiFetch<ApiEnvelope<unknown>>(`/admin/issues/${id}/escalate`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    merge: (
      primaryId: string,
      data: { duplicate_ids: string[]; remarks: string }
    ) =>
      apiFetch<ApiEnvelope<{ issue: Issue }>>(`/admin/issues/${primaryId}/merge`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    officers: () =>
      apiFetch<ApiEnvelope<{ items: Officer[] }>>("/admin/officers"),
    downloadPdf: () => downloadAuthed("/admin/reports/issues.pdf", "railvoice-issues.pdf"),
    downloadXlsx: () =>
      downloadAuthed("/admin/reports/issues.xlsx", "railvoice-issues.xlsx"),
    notifyMain: (remarks?: string) =>
      apiFetch<ApiEnvelope<{ notified: number; open_issues: number; scope: string }>>(
        "/admin/reports/notify-main",
        {
          method: "POST",
          body: JSON.stringify({
            remarks: remarks || "Station report ready for review",
          }),
        }
      ),
    users: {
      list: (params?: Record<string, string | number | boolean | undefined>) => {
        const q = new URLSearchParams();
        if (params) {
          Object.entries(params).forEach(([k, v]) => {
            if (v !== undefined && v !== "" && v !== null) q.set(k, String(v));
          });
        }
        const qs = q.toString();
        return apiFetch<ApiEnvelope<{ items: ManagedUser[]; pagination: PaginationMeta }>>(
          `/admin/users${qs ? `?${qs}` : ""}`
        );
      },
      create: (data: {
        mobile: string;
        display_name: string;
        email?: string;
        role_code: string;
        station_id?: string | null;
        generate_password?: boolean;
      }) =>
        apiFetch<ApiEnvelope<{ user: ManagedUser; temporary_password: string | null }>>(
          "/admin/users",
          { method: "POST", body: JSON.stringify(data) }
        ),
      get: (id: string) =>
        apiFetch<ApiEnvelope<ManagedUser>>(`/admin/users/${id}`),
      update: (id: string, data: { display_name?: string; email?: string; preferred_language?: string }) =>
        apiFetch<ApiEnvelope<ManagedUser>>(`/admin/users/${id}`, {
          method: "PATCH",
          body: JSON.stringify(data),
        }),
      activate: (id: string) =>
        apiFetch<ApiEnvelope<ManagedUser>>(`/admin/users/${id}/activate`, { method: "POST" }),
      deactivate: (id: string) =>
        apiFetch<ApiEnvelope<ManagedUser>>(`/admin/users/${id}/deactivate`, { method: "POST" }),
      lock: (id: string, reason?: string) =>
        apiFetch<ApiEnvelope<ManagedUser>>(`/admin/users/${id}/lock`, {
          method: "POST",
          body: JSON.stringify({ reason }),
        }),
      unlock: (id: string) =>
        apiFetch<ApiEnvelope<ManagedUser>>(`/admin/users/${id}/unlock`, { method: "POST" }),
      resetPassword: (id: string) =>
        apiFetch<ApiEnvelope<{ temporary_password: string; user: ManagedUser }>>(
          `/admin/users/${id}/reset-password`,
          { method: "POST" }
        ),
      assignRole: (id: string, data: { role_code: string; station_id?: string | null }) =>
        apiFetch<ApiEnvelope<ManagedUser>>(`/admin/users/${id}/assign-role`, {
          method: "POST",
          body: JSON.stringify(data),
        }),
      assignStation: (id: string, station_id: string | null) =>
        apiFetch<ApiEnvelope<ManagedUser>>(`/admin/users/${id}/assign-station`, {
          method: "POST",
          body: JSON.stringify({ station_id }),
        }),
      softDelete: (id: string) =>
        apiFetch<ApiEnvelope<ManagedUser>>(`/admin/users/${id}`, { method: "DELETE" }),
      restore: (id: string) =>
        apiFetch<ApiEnvelope<ManagedUser>>(`/admin/users/${id}/restore`, { method: "POST" }),
      audits: (id: string) =>
        apiFetch<ApiEnvelope<{ items: UserAuditRow[] }>>(`/admin/users/${id}/audits`),
      bulkDeactivate: (user_ids: string[]) =>
        apiFetch<ApiEnvelope<{ updated: number; errors: string[] }>>(
          `/admin/users/bulk/deactivate`,
          { method: "POST", body: JSON.stringify({ user_ids }) }
        ),
      bulkLock: (user_ids: string[], reason?: string) =>
        apiFetch<ApiEnvelope<{ updated: number; errors: string[] }>>(
          `/admin/users/bulk/lock`,
          { method: "POST", body: JSON.stringify({ user_ids, reason }) }
        ),
    },
  },

  me: {
    get: () => apiFetch<ApiEnvelope<ManagedUser>>("/me"),
    update: (data: { display_name?: string; email?: string; preferred_language?: string }) =>
      apiFetch<ApiEnvelope<User>>("/me", {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    changePassword: (data: { current_password?: string; new_password: string }) =>
      apiFetch<ApiEnvelope<{ message: string }>>("/me/change-password", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    uploadAvatar: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const token =
        typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const base = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
      const res = await fetch(`${base}/me/avatar`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.error?.message || err?.detail || "Upload failed");
      }
      return res.json() as Promise<ApiEnvelope<{ avatar_url: string }>>;
    },
  },

  search: {
    text: (q: string, params?: { station_id?: string; limit?: number }) => {
      const qs = new URLSearchParams({ q });
      if (params?.station_id) qs.set("station_id", params.station_id);
      if (params?.limit) qs.set("limit", String(params.limit));
      return apiFetch<
        ApiEnvelope<{
          results: { issue: Issue; relevance_score: number; match_type: string }[];
        }>
      >(`/search?${qs}`);
    },
  },
};
