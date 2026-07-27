# SQLite Schema — Memory Tables in `hermes_memory.db`

Verified via `PRAGMA table_info()`. Always verify before writing queries.

## `knowledge_pending` — Session Tier Staging

| Column | Type | Default | Notes |
|--------|------|---------|-------|
| id | TEXT | PK | UUID v4 |
| point_id | TEXT | NULL | Links to Uteke memory (set on promote) |
| topic | TEXT | NOT NULL | Short topic label |
| content | TEXT | NOT NULL | Full content body |
| agent | TEXT | `unknown` | Source agent name |
| category | TEXT | `general` | Content category |
| status | TEXT | `pending` | `pending` → `promoted` / `deleted` |
| submitted_at | TEXT | NOT NULL | ISO timestamp |
| reviewed_at | TEXT | NULL | ISO timestamp (when reviewed) |
| reviewed_by | TEXT | NULL | Who reviewed |
| review_note | TEXT | NULL | Review notes |
| vector | BLOB | NULL | Pre-computed embedding (optional) |
| tags_json | TEXT | NULL | JSON array of tag strings |
| access_count | INT | `0` | Number of search hits |
| reinforcement_count | INT | `0` | Manual reinforcement count |
| confidence | REAL | `0.5` | Current confidence score |
| decay_rate | REAL | `0.05` | Confidence decay per sweep |
| last_accessed_at | TEXT | NULL | ISO timestamp (last search hit) |

## `knowledge_metadata` — Knowledge Tier Tracking

| Column | Type | Default | Notes |
|--------|------|---------|-------|
| point_id | TEXT | PK | Uteke memory UUID |
| access_count | INT | `0` | Search hit count |
| reinforcement_count | INT | `0` | Manual reinforcement |
| confidence | REAL | `0.8` | Current confidence |
| decay_rate | REAL | `0.02` | Decay rate per sweep |
| last_accessed_at | TEXT | NULL | ISO timestamp |
| created_at | TEXT | NOT NULL | ISO timestamp |
| source_agent | TEXT | `unknown` | Originating agent |

No `status` column. Decay = delete row + archive to `knowledge_decayed`.

## `knowledge_decayed` — Forgotten Tier Archive

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PK | Archive entry UUID |
| original_point_id | TEXT | Original memory point ID |
| original_tier | TEXT | Source tier |
| topic | TEXT | Topic from pending table |
| content_preview | TEXT | First 200 chars |
| category | TEXT | Content category |
| source_agent | TEXT | Originating agent |
| decay_reason | TEXT | Why it was decayed |
| decayed_at | TEXT | ISO timestamp |
| confidence | REAL | Confidence at decay time |
| access_count | INT | Access count at decay time |
| reinforcement_count | INT | Reinforcement at decay time |
| decay_rate | REAL | Decay rate at decay time |

## Lifecycle Thresholds

| Transition | Threshold | Source |
|-----------|----------|--------|
| Session → Knowledge | `access_count >= 5` AND `submitted_at <= 7 days ago` OR `reinforcement_count >= 1` | Cron |
| Knowledge → Forgotten | `confidence < 0.1` AND `reinforcement_count <= 0` | Decay sweep |
| Stale Pending Cleanup | `access_count < 3` AND `submitted_at > 30 days ago` AND `status = pending` | Cron |
| Natural Confidence Decay | `confidence -= decay_rate` for items with `last_accessed_at > 14 days ago` | Sweep |
| Confidence Floor | `max(0.05, confidence - decay_rate)` | Prevents instant decay |

## Schema Pitfalls

1. `knowledge_pending.submitted_at` — NOT `created_at`
2. `knowledge_metadata.point_id` — NOT `id`. PK is `point_id`
3. `knowledge_metadata` has NO `status` column — decay = DELETE + archive
4. `knowledge_metadata.confidence` default is 0.8 — NOT 0.5. Only `knowledge_pending` defaults to 0.5
5. `knowledge_metadata.decay_rate` default is 0.02 — NOT 0.05
6. `knowledge_pending.reinforcement_count` can be fractional
