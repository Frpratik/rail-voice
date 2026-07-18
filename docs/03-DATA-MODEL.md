# 3. Data Model

## 3.1 Overview

Relational schema on PostgreSQL with **pgvector** embeddings on `issues`. Migrations:

| Revision | Purpose |
|----------|---------|
| `001` | Initial schema + `CREATE EXTENSION vector` |
| `002` | `issues.assignee_id`, `issues.assigned_at`; notifications → issues FK |

Source: `railvoice-backend/alembic/versions/`, models under `railvoice-backend/app/models/`.

## 3.2 Entity relationship (simplified)

```
Zone 1──* Division 1──* Station 1──* Platform
                │
                └──* Issue *──1 IssueCategory (optional parent category)
                      │
                      ├──* IssuePhoto
                      ├──* Comment
                      ├──* IssueSupport
                      ├──* IssueTimelineEvent
                      ├── creator → User
                      └── assignee → User

User *──* Role (via user_roles, optional location scope)
User 1──* RefreshToken | OtpRequest | Notification
```

## 3.3 Core tables

### Location

| Table | Purpose |
|-------|---------|
| `zones` | Railway zone (seed: WR) |
| `divisions` | Division under zone (seed: Mumbai / MUM) |
| `stations` | 29 WR stations Churchgate→Virar |
| `platforms` | Optional platform per station |
| `issue_categories` | Hierarchical categories |

### Identity

| Table | Purpose |
|-------|---------|
| `users` | Passengers, anon, officials (`mobile_hash`, `email`, `google_id`, `anonymous_session_id`) |
| `roles` | RBAC codes + levels |
| `user_roles` | Assignment; optional `location_type` / `location_id` |
| `refresh_tokens` | Opaque refresh hash + `family_id` for rotation |
| `otp_requests` | Hashed OTP, attempts, expiry |

### Issues

| Table | Purpose |
|-------|---------|
| `issues` | Report body, status, scores, embedding vector, assignee |
| `issue_supports` | Unique (issue, user) |
| `issue_timeline_events` | Audit trail + visibility |
| `issue_photos` | Storage keys, mime, scan_status |
| `comments` | Threadable via `parent_id` |
| `notifications` | In-app alerts |
| `system_config` | JSON config keys |

## 3.4 Issue status lifecycle

Statuses (enum `IssueStatus`):  
`submitted` → `under_review` / `verified` / `rejected` / `spam` → `assigned` / `forwarded_*` → `action_started` → `work_in_progress` → `waiting_for_material` → `completed` → `verified_complete` → `closed`

Admin transitions enforced by matrix in `app/api/v1/admin.py` (`VALID_TRANSITIONS`).

Terminal: `closed`, `rejected`, `spam`, `duplicate_merged`, `withdrawn`.

## 3.5 Roles & levels

| Code | Level | Official API? | Ops UI link? |
|------|-------|---------------|--------------|
| `passenger` | 10 | No | No |
| `volunteer` | 20 | Yes | No (API only) |
| `station_moderator` | 30 | Yes | Yes |
| `station_manager` | 40 | Yes | Yes |
| `divisional_officer` | 50 | Yes | Yes |
| `railway_admin` | 60 | Yes | Yes |
| `super_admin` | 70 | Yes | Yes |

Seeded super admin mobile (hashed): **`+919999999999`** with role `super_admin`.

## 3.6 Important issue columns

| Column | Notes |
|--------|-------|
| `issue_number` | e.g. `RV-WR-2026-000001` |
| `embedding` | `vector(1536)` (config dimension) |
| `priority_score` / `trending_score` / `ai_priority_score` | Ranking |
| `spam_score` | Spam model |
| `is_public` | False when spam-held |
| `assignee_id` / `assigned_at` | Ops assignment |
| `divergence_reason` | Force-create rationale |
| `edit_window_expires_at` | Post-create edit window |

## 3.7 Seed data

`python -m app.scripts.seed` (also free-tier boot):

- Zone WR, Division MUM, 29 stations  
- Roles + categories  
- SystemConfig thresholds  
- Super admin user if missing  

## 3.8 Indexes & uniqueness (highlights)

- Unique: `stations.code`, `users.mobile_hash` / `email` / `google_id` / `anonymous_session_id`, `issues.issue_number`, `issue_supports(issue_id,user_id)`, `refresh_tokens.token_hash`
- Vector similarity queries filter by `station_id` and exclude terminal statuses for duplicates
