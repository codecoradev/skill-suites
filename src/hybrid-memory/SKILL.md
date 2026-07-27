---
name: hybrid-memory
version: 6.0.0
license: MIT
metadata:
  hermes:
    tags: [memory, sqlite, uteke, lifecycle]
---

# Hybrid Memory — SQLite + Uteke

Two-layer memory with 4-tier lifecycle. SQLite for structured data (entities, staging, metadata). Uteke for semantic search (recall, remember, contradiction detection).

## Architecture

```
┌──────────────────┬──────────────────────────┐
│  SQLite          │  Uteke                   │
│  (structured)    │  (semantic)              │
│  - entities      │  - recall (~50ms warm)   │
│  - relationships │  - remember              │
│  - staging       │  - search                │
│  - decay tracking│  - tags, namespaces      │
│  Sub-ms queries  │  - contradiction detect  │
└──────────────────┴──────────────────────────┘
```

SQLite handles shared cross-agent knowledge (entity graph). Uteke handles per-agent personal memory. Namespace isolation is strict — no cross-namespace search by design.

## 4-Tier Lifecycle

```
Working (ephemeral)  →  Session (staging)  →  Knowledge (permanent)  →  Forgotten
TTL 24h                 SQLite table           Uteke namespace           soft-deleted
access_count tracked    access_count ≥ 3       frequency-tracked         confidence < 0.1
                        to promote up          + daily decay
```

| Transition | Trigger | Mechanism |
|-----------|---------|-----------|
| Working → Session | `access_count ≥ 3` at TTL purge | Promote to `knowledge_pending` instead of delete |
| Session → Knowledge | `access_count ≥ 5` AND `age ≥ 7 days` | Cron stores to Uteke (frequency = quality) |
| Knowledge → Forgotten | `confidence < 0.1` AND `reinforcement_count = 0` | Daily decay: confidence -= 0.05/week |

**Confidence model:** initial 0.5 (auto) or 0.8 (manual). Each search hit: confidence = min(1.0, current + 0.1 x (1 - current)). Decay: 0.05 per week.

**Session tier in SQLite (not Uteke):** embedding is expensive, session volume is small, SQL promotion queries are instant. Embed once on promotion.

## Quick Start

### knowledge Tool (Plugin)

```
knowledge(action="search_knowledge", query="API deployment")
knowledge(action="get_entity", name="my-project")
knowledge(action="remember", content="Insight...", tags=["project"])
knowledge(action="promote", session_id="task_123")
knowledge(action="working_set", session_id="task_001", context={"goal": "..."})
knowledge(action="working_get", session_id="task_001")
knowledge(action="stats")
```

### Uteke CLI / HTTP

```bash
uteke remember "Deploy uses Docker Compose" --tags deploy
uteke recall "how to deploy" --namespace my-agent

# HTTP
POST http://localhost:8767/search
Authorization: Bearer $UTEKE_TOKEN
{"query": "deploy", "limit": 5}
```

## SQLite Schema

### knowledge_pending (Session Staging)

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | UUID |
| content | TEXT | Memory text |
| entity_type | TEXT | fact, procedure, preference, etc |
| tags_json | TEXT | JSON array |
| submitted_at | TEXT | ISO timestamp |
| access_count | INTEGER | Search hits (promotion signal) |
| confidence | REAL | 0.0-1.0 |
| decay_rate | REAL | 0.05/week default |
| status | TEXT | pending, promoted, decayed |

### knowledge_metadata (Knowledge Tracking)

| Column | Type | Description |
|--------|------|-------------|
| point_id | TEXT | PK, UUID |
| access_count | INTEGER | Total hits |
| confidence | REAL | 0.0-1.0 |
| decay_rate | REAL | Weekly decay |
| last_accessed_at | TEXT | ISO timestamp |
| source_agent | TEXT | Originating agent |

### entities / relationships

Entity graph for cross-agent shared knowledge. Column: `entity_type` (not `type`). Relationships: `subject_id`/`object_id` (not `source_id`/`target_id`).

## Uteke HTTP API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Server health |
| `/recall` | POST | Semantic recall |
| `/search` | POST | Keyword search |
| `/remember` | POST | Store memory |
| `/list` | POST | List by tag |
| `/forget?id=` | DELETE | Delete memory |
| `/stats` | GET | Statistics |
| `/namespaces` | GET | List namespaces |

## Auto-Recall and Auto-Extract

Two shell hooks automate memory. Install from `extensions/` directory.

**uteke-recall** (`pre_llm_call`): searches Uteke before each LLM call, injects relevant memories. Project-aware, skips cron/short messages.

**uteke-extract** (`on_session_finalize`): extracts takeaways when session ends, stores in Uteke. Structured extraction (headers, bullets, key-values), auto-tags with project.

## Maintenance

| Job | Purpose |
|-----|---------|
| Lifecycle Manager (20:00) | Session → knowledge promotion + decay sweep |
| Memory Maintenance (21:00) | Cleanup + consolidation |

```
knowledge(action="stats")  # health check
curl -sf http://localhost:8767/health  # Uteke health
```

## Gotchas

- `remember` always writes SQLite first, then Uteke. Never loses data.
- `search_knowledge` searches both tiers. Hits auto-increment `access_count`.
- Column names: `entity_type` (not `type`), `subject_id`/`object_id`. Use `PRAGMA table_info()` before writing.
- Uteke namespace defaults to empty, not "all". Always pass `--namespace`.
- `recall --json` nests under `memory` key: `[{"memory": {"content": "..."}, "score": 0.72}]`.
- Batch limits: max 30 items, 8s delay between batches.
- Agents skip Uteke recall at session start. Actively call `uteke recall` for prior work.

## References

- [sqlite-schema.md](references/sqlite-schema.md) — Verified column lists
- [uteke-recall-hook.md](references/uteke-recall-hook.md) — Hook setup and troubleshooting
