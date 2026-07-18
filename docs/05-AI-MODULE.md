# 5. AI Module

Location: `railvoice-backend/app/ai/`

## 5.1 Purpose

On issue create (and related flows), RailVoice runs a **synchronous AI pipeline** so free-tier deploys work without Celery workers. Background Celery jobs optionally recompute trending/priority and store notifications.

## 5.2 Pipeline (`pipeline.py`)

Order of analysis applied to a new issue:

1. **Embeddings** — vector for duplicate search + storage on `issues.embedding`  
2. **Categorizer** — category / subcategory codes  
3. **Severity** — integer 1–5 + emergency signals  
4. **Spam** — spam score; may auto-hold (`status=spam`, `is_public=false`)  
5. **Priority predictor** — `ai_priority_score` 0–1  
6. **Summarizer** — short title-like summary if needed  

Composite **priority_score** combines support, severity, freshness, trend, and AI weight (`priority.py`).

Config flag: `AI_SYNC_ON_CREATE` (default true).

## 5.3 Duplicate detection (`duplicate.py`)

- Scope: same `station_id`, exclude terminal statuses  
- Similarity: cosine on embeddings; local mode adds Jaccard hybrid  
- Thresholds:  
  - OpenAI path: `DUPLICATE_SIMILARITY_THRESHOLD` (default **0.82**)  
  - Local path: `LOCAL_DUPLICATE_SIMILARITY_THRESHOLD` (default **0.45**)  
- API: `POST /issues/check-duplicates` before create; create returns **409** if similars exist and `force_create` is false  

## 5.4 Embeddings (`embeddings.py`)

| Mode | When | Behavior |
|------|------|----------|
| OpenAI | `OPENAI_API_KEY` set | `text-embedding-3-small`, 1536 dims |
| Local | No key | Deterministic / synonym-aware local vectors for demos |

## 5.5 Other modules

| Module | Output |
|--------|--------|
| `categorizer.py` | Category prediction from keywords/rules |
| `severity.py` | Severity + emergency cues |
| `spam.py` | Spam/fake scores vs `SPAM_AUTO_HOLD_THRESHOLD` (0.85) |
| `priority_predictor.py` | AI priority + emergency flag |
| `priority.py` | Weighted composite score × 100 |
| `trending.py` | Velocity-based trending 0–1 |
| `summarizer.py` | ≤160 char extractive summary |
| `search.py` | Hybrid semantic + keyword RRF |
| `daily_summary.py` | Official daily narrative/stats |
| `image_validator.py` | jpeg/png/webp, size bounds |

## 5.6 Background jobs (optional Celery)

| Task | Interval | Role |
|------|----------|------|
| `recalc_priority_scores` | 15 min | Refresh priority |
| `recalc_trending_scores` | 15 min | Refresh trending |
| `generate_daily_ai_summary` | 24 h | Daily summary |
| `send_notification` | on demand | Persist notification |

With `CELERY_ENABLED=false`, broker is memory/eager; free Render does not run worker/beat.

## 5.7 Evaluation

- Unit tests: `tests/test_ai.py`  
- Pair eval: `tests/test_ai_eval.py` + `fixtures/ai_duplicate_pairs.json`  
- Documented targets: `tests/TEST_PLAN.md`
