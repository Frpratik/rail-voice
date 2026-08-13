import type {
  ApiEnvelope,
  Comment,
  DashboardData,
  Issue,
  NotificationItem,
  Officer,
  Photo,
  Station,
  TimelineEvent,
  User,
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

  users: {
    me: () => apiFetch<ApiEnvelope<User>>("/users/me"),
  },

  issues: {
    list: (params?: {
      station_code?: string;
      status?: string;
      sort?: "most_supported" | "newest";
      limit?: number;
    }) => {
      const q = new URLSearchParams();
      if (params?.station_code) q.set("station_code", params.station_code);
      if (params?.status) q.set("status", params.status);
      if (params?.sort) q.set("sort", params.sort);
      if (params?.limit) q.set("limit", String(params.limit));
      const qs = q.toString();
      return apiFetch<
        ApiEnvelope<{
          items: Issue[];
          pagination: {
            next_cursor: string | null;
            has_more: boolean;
            total_count?: number;
          };
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

    create: (payload: {
      description: string;
      station_id: string;
      title?: string;
      category_id?: string;
      platform_id?: string;
      train_number?: string;
      coach_number?: string;
      pnr_number?: string;
      berth_number?: string;
      upcoming_station_code?: string;
      is_emergency?: boolean;
      latitude?: number;
      longitude?: number;
    }) =>
      apiFetch<ApiEnvelope<{ issue: Issue }>>("/issues", {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    support: (id: string) =>
      apiFetch<
        ApiEnvelope<{
          issue_id: string;
          support_count: number;
          subscribed_to_updates: boolean;
          message: string;
        }>
      >(`/issues/${id}/support`, { method: "POST" }),

    listMine: (params?: { limit?: number }) => {
      const q = new URLSearchParams();
      if (params?.limit) q.set("limit", String(params.limit));
      const qs = q.toString();
      return apiFetch<
        ApiEnvelope<{
          items: Issue[];
          pagination: {
            next_cursor: string | null;
            has_more: boolean;
            total_count?: number;
          };
        }>
      >(`/issues/mine${qs ? `?${qs}` : ""}`);
    },

    uploadPhoto: (issueId: string, file: File) => {
      const form = new FormData();
      form.append("file", file);
      return apiFetch<ApiEnvelope<Photo>>(`/issues/${issueId}/photos`, {
        method: "POST",
        body: form,
      });
    },
  },

  comments: {
    list: (issueId: string) =>
      apiFetch<ApiEnvelope<{ items: Comment[] }>>(`/issues/${issueId}/comments`),

    create: (issueId: string, payload: { body: string; parent_id?: string }) =>
      apiFetch<ApiEnvelope<Comment>>(`/issues/${issueId}/comments`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },

  notifications: {
    list: () =>
      apiFetch<ApiEnvelope<{ items: NotificationItem[] }>>("/notifications"),

    markRead: (id: string) =>
      apiFetch<ApiEnvelope<NotificationItem>>(`/notifications/${id}/read`, {
        method: "POST",
      }),
  },

  admin: {
    dashboard: () =>
      apiFetch<ApiEnvelope<DashboardData>>("/admin/dashboard"),

    issues: (params?: { status_filter?: string; limit?: number }) => {
      const q = new URLSearchParams();
      if (params?.status_filter) q.set("status_filter", params.status_filter);
      if (params?.limit) q.set("limit", String(params.limit));
      const qs = q.toString();
      return apiFetch<ApiEnvelope<{ items: Issue[] }>>(`/admin/issues${qs ? `?${qs}` : ""}`);
    },

    updateStatus: (
      id: string,
      payload: { status: string; remarks: string; visibility?: string }
    ) =>
      apiFetch<
        ApiEnvelope<{
          issue: Issue;
          timeline_event: {
            id: string;
            from_status: string;
            to_status: string;
            created_at: string;
          };
        }>
      >(`/admin/issues/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),

    assign: (id: string, payload: { assignee_id: string; remarks: string }) =>
      apiFetch<ApiEnvelope<{ issue: Issue }>>(`/admin/issues/${id}/assign`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    escalate: (
      id: string,
      payload: { target: "station_manager" | "division" | "zone"; remarks: string }
    ) =>
      apiFetch<ApiEnvelope<{ issue: Issue }>>(`/admin/issues/${id}/escalate`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    officers: () =>
      apiFetch<ApiEnvelope<{ items: Officer[] }>>("/admin/officers"),

    exportXlsx: (params?: { station_code?: string; status_filter?: string }) => {
      const q = new URLSearchParams();
      if (params?.station_code) q.set("station_code", params.station_code);
      if (params?.status_filter) q.set("status_filter", params.status_filter);
      const qs = q.toString();
      return downloadAuthed(
        `/admin/reports/issues.xlsx${qs ? `?${qs}` : ""}`,
        "railvoice-issues.xlsx"
      );
    },

    exportPdf: (params?: { station_code?: string; status_filter?: string }) => {
      const q = new URLSearchParams();
      if (params?.station_code) q.set("station_code", params.station_code);
      if (params?.status_filter) q.set("status_filter", params.status_filter);
      const qs = q.toString();
      return downloadAuthed(
        `/admin/reports/issues.pdf${qs ? `?${qs}` : ""}`,
        "railvoice-issues.pdf"
      );
    },

    notifyMain: (remarks: string) =>
      apiFetch<ApiEnvelope<{ notified: number; open_issues: number; scope: string }>>(
        "/admin/reports/notify-main",
        {
          method: "POST",
          body: JSON.stringify({ remarks }),
        }
      ),
  },
};
