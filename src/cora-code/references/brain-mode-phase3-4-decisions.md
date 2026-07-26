# Brain Mode Architecture — Phase 3/4 Decisions (Jul 2026)

Supersedes the generic Phase 3/4/5 descriptions in `brain-mode-architecture.md`.
This file captures the **locked-in decisions** from the user-engineer analysis.

## Locked Decisions

| # | Decision | Rationale |
|---|----------|----------|
| 1 | Vector storage = **usearch** (not SQLite BLOB) | User directive. Proven in uteke (production). ANN O(log n), incremental, 100K+ scale. |
| 2 | Hybrid scoring = **RRF** (k=60) | User agrees. Same formula as uteke `doc_search_hybrid()`. |
| 3 | Embedding timing = **index-time** | User agrees. Reference: uteke's `remember()` flow. |
| 4 | Uteke integration = **HTTP API only** (not ATTACH for vectors) | Discovered: ATTACH cannot access usearch files (C library, not SQLite). |
| 5 | Phase 5 = **DEFERRED** | Low ROI. Static tokens ~80% quality. 1.5-2GB RAM blocker. |

## Phase 3 — IMPLEMENTED (PR #362, Jul 2026)

### Storage Layout

```
~/.codecora/cora-code/
├── graph.db                # SQLite: symbols, edges, projects, files
├── cora_index.usearch      # HNSW: symbol embeddings (256d static, or 1024d future)
└── cora_index.keys         # Key mapping sidecar: usearch_key<TAB>symbol_id
```

### CodeVectorIndex (`src/index/vector.rs`, 384 lines)

Pattern from uteke `crates/uteke-core/src/memory/vector.rs`, simplified:
maps usearch u64 key ↔ symbol DB `i64` ID (not UUID string).

```rust
pub struct CodeVectorIndex {
    index: Index,                      // usearch HNSW
    key_to_symbol: HashMap<u64, i64>, // usearch key → symbol DB id
    symbol_to_key: HashMap<i64, u64>, // symbol DB id → usearch key
    next_key: u64,
    path: Option<PathBuf>,            // ~/.codecora/cora-code/cora_index.usearch
    dirty: bool,
    _lock_file: Option<File>,         // fs2 exclusive lock
}
```

Dependencies: `usearch = "2"`, `fs2 = "0.4"`.

Key methods: `load_or_create(path, dims)`, `insert(symbol_id, &[f32])`, `search(query, k)`, `remove(symbol_id)`, `save()`. Auto-reserves capacity on insert. Save uses buffer serialization + atomic rename + `.keys` sidecar.

### Brain Search (`src/index/brain.rs`, 257 lines)

```
embed_project(conn, vector_idx, project_id)
  → SELECT id, name, kind, signature FROM symbols WHERE project_id = ?
  → for each: embed_code(name + " " + signature) → 256d f64 → f32 → insert to vector_idx
  → UPDATE projects SET last_embedded_at = NOW() WHERE id = ?

brain_search(conn, vector_idx, project_id, query, limit)
  → Signal 1: fts5_search() — FTS5 MATCH, top 50, rank-based
  → Signal 2: vector_search() — embed query, usearch KNN top 50, cosine distance → similarity
  → Signal 3: graph_proximity_search() — BFS depth-2 from top-5 FTS hits
  → RRF fusion: score(id) = Σ 1/(60 + rank_i)  per signal
  → sort by fused score desc, truncate to limit
  → enrich each result with (name, kind, file, line, signature) from symbols table
```

### RRF Fusion (3 signals)

```
Signal 1: FTS5 keyword search → Vec<(symbol_id, rank)>
Signal 2: usearch KNN search  → Vec<(symbol_id, distance)>
Signal 3: Graph proximity     → Vec<(symbol_id, rank)>

Fusion: score(id) = Σ 1/(k + rank_i(id))  where k=60
```

Reference implementation: uteke `doc_search_hybrid()` in `crates/uteke-core/src/lib.rs:1385`.

### Schema v4 Migration

```sql
ALTER TABLE projects ADD COLUMN embedding_tier TEXT NOT NULL DEFAULT 'static';
ALTER TABLE projects ADD COLUMN embedding_dims INTEGER NOT NULL DEFAULT 256;
ALTER TABLE projects ADD COLUMN embedding_model TEXT NOT NULL DEFAULT 'static-tokens';
ALTER TABLE projects ADD COLUMN last_embedded_at TEXT;
```

NO separate `embeddings` table — vectors in usearch, metadata in existing `symbols` table.

### Index-Time Embedding Flow

```
cora index
  → extract symbols (tree-sitter / regex)
  → store symbols/edges to SQLite
  → embed_project(conn, vector_idx, project_id)
      → SELECT id, name, kind, signature FROM symbols WHERE project_id = ?
      → for each: embed_code(name + " " + signature) → Vec<f32>
      → CodeVectorIndex.insert(symbol_id, &embedding)
  → CodeVectorIndex.save()  // persist .usearch + .keys files
```

### CLI: `cora brain <query>`

Flags: `--json`, `--limit N` (default 20). Opens vector index, runs `brain_search()`, formats output.

### MCP Tool: `cora.brain_search`

Input: `{ query: string, limit?: number }`. Returns JSON array of results with score, signals, file, line, etc.

## Phase 4 Architecture

### Why HTTP API Not ATTACH

```
SQLite ATTACH:     graph.db ←ATTACH→ uteke.db  ✅ (SQLite tables only)
SQLite ATTACH:     graph.db ←ATTACH→ uteke_index.usearch  ❌ (not a SQLite DB)
uteke HTTP API:    cora-code --HTTP--> localhost:8767  ✅ (accesses SQLite + usearch)
```

The uteke server owns both `uteke.db` AND `uteke_index.usearch`. Only the server can
do vector search. HTTP API is the only way for cora-code to access uteke vectors.

### `cora brain --learn` Flow

```
cora review --learn
  → extract findings from review result
  → for each finding:
      POST localhost:8767/recall  (namespace=default, room=cora-code)
      tags: [cora-code, code-pattern, <severity>]
```

### Cross-Project Recall (Optional Enrichment)

```
cora brain <query>
  → local search: FTS5 + usearch + graph → RRF ranked results
  → optional: GET localhost:8767/search?q=<query>&namespace=default
  → if uteke available: present cross-project patterns as additional section
  → if uteke unavailable: silent degradation (no error)
```

## Phase 5 — Why Deferred

| Metric | Static (Phase 3) | + Voyage-4-Nano |
|--------|-------------------|------------------|
| Quality | Baseline (~80%) | +15-25% |
| RAM | ~30MB | +1.5-2GB |
| Index time (1695 syms) | ~0.2s | ~6 min |
| Binary size impact | 0 | +~5MB (ort crate) |
| First-use download | None | ~1.4GB model |

Trigger to revisit: user explicit request, or `cora review --brain` quality insufficient.