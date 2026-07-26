# Uteke SQLite Schema Audit (Jul 14, 2026)

Source-verified from direct SQLite inspection of `memories` table schema, indexes, FTS5 config, and trigger setup.

## Current Indexes on `memories`

| Index | Column | Type | Status |
|-------|--------|------|--------|
| `sqlite_autoindex_memories_1` | `id` (PK) | Unique | ✅ |
| `idx_memories_tags` | `tags` | B-tree | ⚠️ JSON text — inefficient for exact match |
| `idx_memories_created` | `created_at` | B-tree | ✅ |
| `idx_memories_namespace` | `namespace` | B-tree | ✅ |
| `idx_memories_deprecated` | `deprecated` | B-tree | ✅ |
| `idx_memories_slug` | `slug` | Partial (WHERE slug IS NOT NULL) | ✅ |
| **MISSING** | `memory_type` | — | ❌ Full scan for `WHERE memory_type = 'decision'` |
| **MISSING** | `importance` | — | ❌ Full scan for `WHERE importance > 0.5` |
| **MISSING** | `pinned` | — | ❌ Full scan for `WHERE pinned = 1` |
| **MISSING** | `memory_type` in FTS5 | — | ❌ Can't `MATCH 'memory_type:decision'` |
| **MISSING** | `metadata` in FTS5 | — | ❌ Can't `MATCH 'metadata:entity:flux'` |

## FTS5 Configuration

```sql
CREATE VIRTUAL TABLE memories_fts USING fts5(
    content, tags, namespace,   -- 3 columns ONLY
    content='memories'
);
```

**Triggers:** Auto-sync INSERT/UPDATE/DELETE to FTS5 (verified: memories count = memories_fts count = 16,574). Triggers handle content column rebuild on UPDATE.

**What FTS5 CAN search:** `MATCH 'keyword'`, `MATCH 'tags:codecoradev'`, `MATCH 'namespace:cmo'`, combined `MATCH 'drawover AND tags:codecoradev'`.

**What FTS5 CANNOT search:** `metadata`, `memory_type`, `source`, `source_type`, `content_type`, `slug`.

## JSON1 Extension (Available)

SQLite `json_extract()` works on `metadata TEXT` column:

```sql
-- Query by metadata key-value
SELECT id, content FROM memories 
WHERE json_extract(metadata, '$.platform') = 'threads'
  AND namespace = 'cmo';

-- Query by metadata with numeric comparison
SELECT id, content, json_extract(metadata, '$.likes') as likes
FROM memories
WHERE CAST(json_extract(metadata, '$.likes') AS INTEGER) > 50
ORDER BY likes DESC;

-- Query by entity (common pattern from CLI memories)
SELECT id, content FROM memories
WHERE json_extract(metadata, '$.entity') = 'flux2-klein-4b';
```

**Performance:** `json_extract` = full table scan (no expression index). At 17K rows, acceptable (<100ms). At 100K+, needs expression index:
```sql
CREATE INDEX idx_mem_meta_platform ON memories((json_extract(metadata, '$.platform')));
```

## memory_type Distribution

| Type | Count |
|------|-------|
| fact | 15,760 |
| event | 227 |
| preference | 177 |
| insight | 115 |
| decision | 150 |
| procedure | 62 |
| context | 59 |
| note | 22 |
| reference | 2 |

## Recommended Index Additions

```sql
CREATE INDEX idx_memories_type ON memories(memory_type);
CREATE INDEX idx_memories_importance ON memories(importance);
CREATE INDEX idx_memories_pinned ON memories(pinned);
```

These would enable efficient filtering by type, importance range, and pinned status.

## Dual Storage: Tags

Tags stored in TWO places:
1. `memories.tags` — JSON array string `["tag1","tag2"]` — FTS5 tokenizes this
2. `memory_tags` — normalized `(memory_id, tag)` table with proper index

For exact tag match: use `memory_tags` table (indexed). For FTS keyword: use `memories_fts`.

## Direct SQLite Query Patterns for Social Media

```python
import sqlite3, json, uuid, datetime

DB = "~/.uteke/uteke.db"

def store_post(content, tags, metadata, namespace="cmo"):
    """Insert with full metadata — bypasses API meta bug."""
    conn = sqlite3.connect(DB)
    mid = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn.execute("""INSERT INTO memories (id, content, tags, metadata, namespace, 
                       memory_type, importance, created_at, updated_at, source_type)
                   VALUES (?,?,?,?,?,?,?,?,datetime('now'),datetime('now'),'user')""",
                (mid, content, json.dumps(tags), json.dumps(metadata), namespace, "fact", 0.5))
    for tag in tags:
        conn.execute("INSERT OR IGNORE INTO memory_tags VALUES (?,?)", (mid, tag))
    conn.commit(); conn.close()
    return mid

def query_posts(platform=None, account=None, status=None, namespace="cmo", limit=20):
    """Structured query on metadata + tags."""
    conn = sqlite3.connect(DB)
    conditions = ["namespace = ?", "deprecated = 0"]
    params = [namespace, 0]
    if platform:
        conditions.append("json_extract(metadata, '$.platform') = ?")
        params.append(platform)
    if account:
        conditions.append("json_extract(metadata, '$.account') = ?")
        params.append(account)
    if status:
        conditions.append("json_extract(metadata, '$.status') = ?")
        params.append(status)
    
    rows = conn.execute(
        f"SELECT id, content, metadata, tags, created_at FROM memories WHERE {' AND '.join(conditions)} ORDER BY created_at DESC LIMIT ?",
        params + [limit]
    ).fetchall()
    conn.close()
    return rows

def top_posts_by_metric(metric="likes", namespace="cmo", limit=10):
    """Rank by metadata numeric field."""
    conn = sqlite3.connect(DB)
    rows = conn.execute(f"""
        SELECT id, content, json_extract(metadata, '$.likes') as metric
        FROM memories
        WHERE json_extract(metadata, '$.{metric}') IS NOT NULL
          AND namespace = ?
        ORDER BY CAST(json_extract(metadata, '$.{metric}') AS INTEGER) DESC
        LIMIT ?
    """, (namespace, limit)).fetchall()
    conn.close()
    return rows
```

## Tables Overview

| Table | Rows | Purpose |
|-------|------|---------|
| `memories` | ~17K | Core memory store |
| `memories_fts` | ~17K (synced) | FTS5 keyword search index |
| `memory_tags` | ~30K+ | Normalized tag index |
| `memory_edges` | varies | Memory-to-memory relationships |
| `graph_nodes` | varies | Entity graph |
| `graph_edges` | varies | Entity relationships |
| `rooms` | varies | Discussion rooms |
| `room_memories` | varies | Room ↔ memory junction |
| `documents` | varies | Wiki/knowledge base |
| `document_chunks` | varies | Document chunks for embedding |
| `timeline_events` | varies | Memory event history |
| `schema_version` | 1 | DB version tracking |
