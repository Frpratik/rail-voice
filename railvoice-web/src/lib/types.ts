export interface Station {
  id: string;
  code: string;
  name: string;
  name_hi?: string | null;
  name_mr?: string | null;
  sequence_order: number;
  latitude: number;
  longitude: number;
  division?: { code: string; name: string } | null;
  open_issue_count?: number | null;
}

export interface Category {
  id: string;
  code: string;
  name: string;
  icon?: string | null;
}

export interface Photo {
  id: string;
  url: string;
  mime_type: string;
  file_size_bytes: number;
  scan_status: string;
  sort_order: number;
  kind?: "evidence" | "resolution";
  created_at: string;
}

export interface Comment {
  id: string;
  issue_id: string;
  body: string;
  parent_id?: string | null;
  is_hidden: boolean;
  created_at: string;
  author: {
    id: string | null;
    display_name: string;
    is_anonymous: boolean;
  };
}

export interface NotificationItem {
  id: string;
  type: string;
  title: string;
  body: string;
  issue_id?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface Issue {
  id: string;
  issue_number: string;
  title: string | null;
  description: string;
  status: string;
  severity: number;
  is_emergency: boolean;
  support_count: number;
  comment_count: number;
  category: Category | null;
  location: {
    station: { code: string; name: string; id?: string };
    platform?: { number: number; name?: string } | null;
    train_number?: string | null;
    coach_number?: string | null;
    pnr_number?: string | null;
    berth_number?: string | null;
    upcoming_station_code?: string | null;
    latitude?: number | null;
    longitude?: number | null;
  };
  creator?: { id: string; display_name: string; is_anonymous: boolean } | null;
  assignee?: { id: string; display_name?: string } | null;
  photos?: Photo[];
  department?: string | null;
  merged_into_id?: string | null;
  sla_due_at?: string | null;
  overdue?: boolean;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
  closed_at?: string | null;
}

export interface TimelineEvent {
  id: string;
  event_type: string;
  from_status: string | null;
  to_status: string | null;
  remarks: string | null;
  visibility: string;
  created_at: string;
}

export interface User {
  id: string;
  display_name: string;
  is_verified: boolean;
  is_anonymous?: boolean;
  roles: string[];
  persona?: "passenger" | "station_admin" | "main_admin";
  persona_label?: string;
}

export interface ApiEnvelope<T> {
  data: T;
  meta?: { correlation_id?: string; timestamp?: string };
}

export interface DashboardData {
  kpis: {
    open_issues: number;
    in_progress: number;
    resolved_today: number;
    avg_resolution_hours: number | null;
    sla_breaches: number;
    emergency_open: number;
  };
  top_issues: Issue[];
}

export interface Officer {
  id: string;
  display_name: string;
  roles: string[];
}

export interface IssueViewer {
  signed_in: boolean;
  is_creator: boolean;
  supported: boolean;
  flagged: boolean;
  can_withdraw: boolean;
  can_confirm: boolean;
  following: boolean;
  my_rating: number | null;
  can_rate: boolean;
  rating: { average: number | null; count: number };
}

export interface FlagItem {
  id: string;
  reason: string;
  note: string | null;
  created_at: string | null;
  resolved_at: string | null;
  resolution: string | null;
  reporter: string | null;
  target: "issue" | "comment";
  comment_body: string | null;
  issue: {
    id: string;
    issue_number: string;
    title: string | null;
    status: string;
    station: string | null;
  };
}

export interface StationScore {
  code: string;
  name: string;
  reports: number;
  open: number;
  fixed: number;
  fix_rate: number | null;
  avg_fix_hours: number | null;
  avg_rating: number | null;
}

export interface Transparency {
  days: number;
  total_reports: number;
  open: number;
  fixed: number;
  fix_rate: number | null;
  stations: StationScore[];
}

export interface Reputation {
  reports: number;
  backed: number;
  comments: number;
  fixed: number;
  points: number;
  badges: { code: string; name: string; description: string }[];
}

export interface Analytics {
  days: number;
  total: number;
  trend: { date: string; created: number; resolved: number }[];
  by_category: { name: string; count: number }[];
  by_department: { name: string; count: number }[];
  by_station: { code: string; name: string; total: number; open: number; overdue: number }[];
  avg_resolution_hours: number | null;
  sla_met_percent: number | null;
  recurring: { station: string; category: string; count: number }[];
}

export interface AuditItem {
  at: string | null;
  kind: string;
  action: string;
  actor: string | null;
  target: string | null;
  success: boolean;
  ip: string | null;
}
