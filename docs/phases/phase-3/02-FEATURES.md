# Phase 3 — Feature Design

## Durable media

`StorageService` branches on `STORAGE_BACKEND`:

- `local` — filesystem under `LOCAL_STORAGE_PATH` (default)
- `s3` — boto3 put_object to bucket (works with AWS S3, Cloudflare R2, MinIO via `S3_ENDPOINT`)

Public URL:

- local: `{PUBLIC_BASE_URL}/media/{key}`
- s3: `{S3_PUBLIC_BASE_URL}/{key}` or virtual-hosted style when unset

## Admin merge

```
POST /api/v1/admin/issues/{primary_id}/merge
{
  "duplicate_ids": ["uuid", ...],
  "remarks": "Same bin missing, consolidate"
}
```

Rules:

- Primary must exist and not already be `duplicate_merged`
- Each duplicate must exist, not equal primary, not already merged
- Duplicate → `status=duplicate_merged`, `merged_into_id=primary`, `is_public=false`
- Unique supports transferred to primary; `support_count` recalculated
- Timeline `merged` on primary + each duplicate
- Notify duplicate creators

## Location scope

Active `user_roles.location_type` + `location_id`:

| type | Filter |
|------|--------|
| `station` | `issues.station_id IN (...)` |
| `division` | `issues.division_id IN (...)` |
| `zone` | `issues.zone_id IN (...)` |

Unscoped official roles (`super_admin`, or null location) see all. Applied to dashboard, queue, spam queue, exports.

## SLA

Severity → hours (settings):

| Severity | Default hours |
|----------|---------------|
| 1 (critical) | 4 |
| 2 | 12 |
| 3 | 24 |
| 4 | 48 |
| 5 | 72 |

- `avg_resolution_hours` = mean(`resolved_at - created_at`) for resolved/closed in last 90 days  
- `sla_breaches` = count of **open** issues where `now > created_at + sla(severity)`

## Search UI

Home page search box → `GET /search?q=` → result cards linking to issue detail.
