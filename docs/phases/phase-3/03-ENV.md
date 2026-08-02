# Phase 3 — Environment

```env
# Storage
STORAGE_BACKEND=local          # or s3
LOCAL_STORAGE_PATH=storage/uploads
PUBLIC_BASE_URL=http://localhost:8000

# S3 / R2 / MinIO
S3_ENDPOINT=                   # e.g. https://xxx.r2.cloudflarestorage.com
S3_BUCKET=railvoice
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_REGION=ap-south-1
S3_PUBLIC_BASE_URL=            # CDN or public bucket URL prefix

# SLA hours by severity (1=most urgent)
SLA_HOURS_SEVERITY_1=4
SLA_HOURS_SEVERITY_2=12
SLA_HOURS_SEVERITY_3=24
SLA_HOURS_SEVERITY_4=48
SLA_HOURS_SEVERITY_5=72
```

Free staging: keep `STORAGE_BACKEND=local`. Production/demo durability: set `s3` + R2 free tier.
