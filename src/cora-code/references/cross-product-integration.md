# Cross-Product Integration: Separate DBs + SQLite ATTACH

**Decision:** Jul 22, 2026. Approved by team.

## Architecture

Each CodeCora product owns its own SQLite DB under `~/.codecora/{product}/`. Cross-product queries use SQLite `ATTACH DATABASE` — no data duplication, no schema coupling.

## Why Not Shared DB?

Shared DB (cora-code writes to uteke.db directly) was considered but rejected because:
- cora-code must work WITHOUT uteke (CI, users without uteke)
- Schema coupling — uteke migrations would break cora-code
- Lock contention when both write simultaneously

## Phase-by-Phase Integration

| Phase | cora-code writes | cora-code reads | Uteke involvement |
|-------|------------------|-----------------|-------------------|
| **2** | `~/.codecora/cora-code/graph.db` | — | None |
| **3** | graph.db + embeddings | graph.db | None |
| **4** | graph.db | `~/.codecora/uteke/uteke.db` (ATTACH) | cora push patterns to uteke |
| **Future** | — | `~/.codecora/trapfall/trapfall.db` | uteke read cora graph |

## ATTACH Pattern (Phase 4)

```rust
// From cora-code, read uteke memories:
conn.execute_batch(
    "ATTACH DATABASE '/home/user/.codecora/uteke/uteke.db' AS uteke;"
)?;

// Join code graph + uteke memories in single query
let sql = r#"
    SELECT cs.name, cs.file_path, m.content
    FROM code_symbols cs
    JOIN uteke.graph_nodes gn ON gn.label = cs.name
    JOIN uteke.memories m ON m.id = gn.memory_id
    WHERE cs.project = 'cora-code'
      AND m.namespace = 'cto'
"#;
```

Key rules:
- **Read-only** on attached DBs — never write to another product's DB
- **Graceful degradation** — if uteke.db doesn't exist or ATTACH fails, skip enrichment, don't error
- **Path resolution** — always use `dirs::home_dir().join(".codecora/uteke/uteke.db")`, not hardcoded paths

## Uteke Schema Relevant for Integration

From uteke-core `memory/store.rs`:

```sql
-- Entity graph (generic, already exists)
graph_nodes (id TEXT PK, label TEXT, entity_type TEXT, properties_json TEXT, memory_id TEXT FK, created_at TEXT)
graph_edges (id TEXT PK, source_id TEXT FK, target_id TEXT FK, relation TEXT, weight REAL, created_at TEXT, UNIQUE source/target/relation)

-- Semantic memories
memories (id TEXT PK, content TEXT, namespace TEXT, memory_type TEXT, ...)
memory_tags (memory_id TEXT FK, tag TEXT)

-- Documents (for code patterns, RFCs)
documents (id TEXT PK, slug TEXT, content TEXT, namespace TEXT, ...)
```

Cora-code can leverage `graph_nodes` for entity linking and `memories` for project knowledge.

## Uteke Docker Consideration

Docker uteke uses `UTEKE_HOME=/data`, so uteke.db is NOT at `~/.codecora/uteke/` in Docker. For cross-product integration in Docker, the cora-code container would need to either:
1. Use uteke HTTP API (already works — `localhost:8767`)
2. Mount the same volume

Recommendation: Use HTTP API for cross-product communication in Docker, ATTACH for bare metal only.