import type {
  ApiEnvelope,
  Comment,
  DashboardData,
  DuplicateCheckResult,
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

function ensureAnonymousSession(): string {
  if (typeof window === "undefined") return "";
  let anon = localStorage.getItem("anonymous_session_id");
  if (!anon) {
    anon = crypto.randomUUID();
    localStorage.setItem("anonymous_session_id", anon);
  }
  return anon;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
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
    officers: () =>
      apiFetch<ApiEnvelope<{ items: Officer[] }>>("/admin/officers"),
    downloadPdf: () => downloadAuthed("/admin/reports/issues.pdf", "railvoice-issues.pdf"),
    downloadXlsx: () =>
      downloadAuthed("/admin/reports/issues.xlsx", "railvoice-issues.xlsx"),
  },
};
