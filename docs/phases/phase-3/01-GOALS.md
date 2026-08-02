# Phase 3 — Goals

## Goals

| ID | Goal |
|----|------|
| G1 | Photos survive redeploys when `STORAGE_BACKEND=s3` |
| G2 | Officials can merge duplicate issues into a primary |
| G3 | Station/division/zone-scoped officers only see their issues |
| G4 | Dashboard shows real avg resolution time and SLA breaches |
| G5 | Passengers can search public issues from the home page |

## Acceptance

- [x] Local storage still works with `STORAGE_BACKEND=local`
- [x] S3 path uploads and returns a public/CDN URL when configured
- [x] Merge sets `duplicate_merged`, `merged_into_id`, transfers unique supports
- [x] Scoped moderator seed user only sees their station in admin queue
- [x] `avg_resolution_hours` and `sla_breaches` are computed (not hard-coded)
- [x] Home search returns hybrid search results
