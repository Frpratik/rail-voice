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
  priority_score: number;
  trending_score: number;
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
  resolution_photo_url?: string | null;
  resolution_verification_score?: number | null;
  resolution_status?: string | null;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
  closed_at?: string | null;
}

export interface SimilarIssue {
  id: string;
  issue_number: string;
  title: string | null;
  description_preview: string;
  similarity: number;
  support_count: number;
  status: string;
  created_at: string;
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

export interface DuplicateCheckResult {
  has_similar: boolean;
  threshold: number;
  similar_issues: SimilarIssue[];
  recommendation: string;
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

export interface ManagedUser {
  id: string;
  display_name: string;
  email: string | null;
  mobile_last4: string | null;
  avatar_url: string | null;
  preferred_language: string;
  is_verified: boolean;
  is_anonymous: boolean;
  is_active: boolean;
  is_locked: boolean;
  locked_at: string | null;
  locked_reason: string | null;
  must_change_password: boolean;
  has_password: boolean;
  status: string;
  roles: string[];
  persona: string;
  persona_label: string;
  assigned_station: { id: string; code: string; name: string } | null;
  assigned_station_id: string | null;
  created_at: string | null;
  updated_at: string | null;
  last_login_at: string | null;
  deleted_at: string | null;
  activity_summary: {
    issues_created: number;
    supports: number;
    comments: number;
  };
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
}

export interface UserAuditRow {
  id: string;
  created_at: string | null;
  action: string;
  actor_name: string | null;
  target_user_name: string | null;
  previous_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
}
export interface VendorContract {
  id: string;
  vendor_name: string;
  contract_code: string;
  station_id?: string;
  category_id?: string;
  penalty_per_sla_hour: number;
  max_penalty_cap: number;
  is_active: boolean;
  created_at: string;
}

export interface VendorPenaltyNote {
  id: string;
  contract_id: string;
  issue_id: string;
  penalty_amount: number;
  clause_reference: string;
  status: string;
  pdf_url?: string;
  created_at: string;
}

export interface VendorScorecardItem {
  contract: VendorContract;
  total_penalty_deducted: number;
  pending_penalties: number;
  sla_breaches_count: number;
  resolved_issues_count: number;
}

export interface VendorScorecardResponse {
  items: VendorScorecardItem[];
}

export interface StationGeoFeatureProperties {
  station_id: string;
  code: string;
  name: string;
  health_score: number;
  active_issues_count: number;
  critical_issues_count: number;
  status_summary: Record<string, number>;
}

export interface StationGeoFeature {
  type: 'Feature';
  geometry: {
    type: 'Point';
    coordinates: [number, number];
  };
  properties: StationGeoFeatureProperties;
}

export interface StationHeatmapResponse {
  type: 'FeatureCollection';
  features: StationGeoFeature[];
}
