# Uteke Internals — Source-Verified (v0.7.3, Jul 2026)

Deep source code audit from `~/uteke/` Rust workspace. All line numbers verified.

## 1. Storage — SQLite + usearch

| Component | Detail |
|-----------|--------|
| **SQLite lib** | `rusqlite` v0.40, `bundled` feature (no system SQLite) |
| **DB path** | `~/.uteke/uteke.db` (env: `UTEKE_HOME`, code: `lib.rs:188-198`) |
| **Vector index** | `~/.uteke/uteke_index.usearch` + `.keys` sidecar (code: `vector.rs:48-54`) |
| **Schema version** | CURRENT = 14 (code: `store.rs`, 14 migrations) |
| **Main tables** | `memories` (20+ cols), `memory_tags` (junction), `graph_nodes`, `graph_edges`, `memory_edges`, `timeline_events`, `documents`, `rooms`, `room_memories` |
| **FTS5** | `memories_fts` (columns: content, tags, namespace, memory_type) + `documents_fts` |

## 2. Embedding — EmbeddingGemma Q4 ONNX 768d

Source: `embed/engine.rs`

| Property | Value | Source |
|----------|-------|--------|
| Model | `embeddinggemma-300m-ONNX` | `engine.rs:12` |
| HF repo | `onnx-community/embeddinggemma-300m-ONNX` | `engine.rs:19` |
| Dimensions | **768** | `engine.rs:16` `const MODEL_DIMS` |
| Max seq len | 2048 tokens | `engine.rs:17` |
| ONNX Runtime | `ort` v2.0.0-rc.12, `download-binaries` feature | `Cargo.toml` |
| Tokenizer | `tokenizers` v0.23 (HuggingFace) | `Cargo.toml` |
| Pooling | Uses `output[1]` (sentence_embedding, already mean-pooled) | `engine.rs:152-153` |
| Normalization | L2 normalized after extraction | `engine.rs:161-167` |
| Download | One-time from `huggingface.co`, SHA256 verified, atomic write | `engine.rs:216-257` |
| Mutex | Tokenizer + session both wrapped in `Mutex` for `&self` trait | `engine.rs:42-45` |

**Key ONNX inference pattern** (engine.rs:141-168):
```
inputs: input_ids (1, seq_len, i64), attention_mask (1, seq_len, i64)
outputs: [0] = last_hidden_state (1, seq_len, 768), [1] = sentence_embedding (1, 768)
We use output[1] — already pooled. L2 normalize → return 768d f32 vector.
```

## 3. Vector Search — usearch (HNSW)

Source: `memory/vector.rs`

| Property | Value |
|----------|-------|
| Library | `usearch` v2 (Cargo.toml) |
| Algorithm | HNSW (module doc: "Persistent vector index using usearch (HNSW)") |
| Metric | `MetricKind::Cos` (cosine distance) |
| Quantization | `ScalarKind::F32` |
| Persistence | Disk-based `.usearch` file + `.keys` sidecar |
| Startup | Load from disk ~5ms, no rebuild |
| Insert/delete | Incremental, no rebuild |
| Cross-process lock | `fs2::FileExt` exclusive lock on `.usearch` file (vector.rs:4-6, 352-376) |
| Atomic saves | Buffer serialization → temp file → POSIX rename (vector.rs:158-184) |
| ef parameter | **NOT exposed** — Rust bindings don't pass `ef` to usearch v2.25.3 (vector.rs:274) |
| Default dims | `const DEFAULT_DIMS: usize = 768;` (vector.rs:26) |

## 4. Salience + Recency (NOT traditional auto-decay)

Source: `salience_recency.rs`

### Salience (how much memory matters)

```rust
// salience_recency.rs:71-81
access_freq = log10(access_count.max(1)) / 3.0  // clamped 0..1
importance = memory.importance (stored, 0..1)
pinned_bonus = 0.2 if pinned else 0.0
salience = importance * 0.5 + access_freq * 0.3 + pinned_bonus  // clamped 0..1
```

### Recency (exponential decay, per-type time constant)

```rust
// salience_recency.rs:105-110
recency = exp(-age_days / half_life_days(memory_type))
```

| Memory Type | τ (days) | Notes |
|-------------|----------|-------|
| `decision`, `preference` | 365 | Evergreen — very slow decay |
| `fact`, `reference` | 180 | Moderate decay |
| `insight` | 240 | Below fact/reference — slower than expected |
| `event` | 30 | Fast decay — time-bound |
| `note`, `procedure`, `context`, unknown | 90 | Default fallback |

Source: `salience_recency.rs:89-98` (`type_half_life_days()`)

### Application

Both axes are **opt-in per query** (default weights = 0.0). Applied AFTER RRF scoring as additive boosts (operations.rs:592-608). Cannot dominate embedding similarity — designed as tie-breakers.

### Aging (separate from recency scoring)

`memory/aging.rs` is a manual cleanup tool based on hard age thresholds + access count, NOT exponential decay. `find_aged()` and `cleanup_aged()` delete memories older than N days with access_count ≤ threshold. No periodic auto-decay job exists.

## 5. Dream Cycle

Source: `dream.rs`

6-phase pipeline, all local, zero LLM, dependency-ordered:

| Phase | Description | Mutates? |
|-------|-------------|----------|
| **Lint** | Validate memory_type values (SQL COUNT) | No |
| **Backlinks** | Rebuild `referenced_by` edges | Yes |
| **Dedup** | Merge near-duplicates (cosine threshold 0.92) | Yes (if dry_run=false) |
| **Orphans** | Detect disconnected memories (no edges, access=0, importance<0.3) | No (detection only) |
| **Compact** | Prune deprecated memories >30 days old | Yes |
| **Verify** | Schema + index consistency check | No |

Phases always execute in canonical order regardless of user input order. Dry-run supported.

## 6. 2-Layer Retrieval: Vector + FTS5 BM25 with RRF

Source: `operations.rs:743-845`

### RRF Implementation

```rust
const RRF_K: u32 = 60;  // operations.rs:751

// For each vector result at rank r:
rrf_score += 1.0 / (60.0 + r as f64 + 1.0)

// For each FTS5 result at rank r:
rrf_score += 1.0 / (60.0 + r as f64 + 1.0)

// Normalize: max_rrf = 2.0 / (60.0 + 1.0)
// normalized = (score / max_rrf).clamp(0.0, 1.0)
```

### Search Strategies

| Strategy | Description | Code |
|----------|-------------|------|
| `Vector` | Cosine similarity only | `recall()` |
| `Fts5` | BM25 only (with token fallback if phrase empty) | `recall_fts5_only()` |
| `Hybrid` | RRF merge of vector + FTS5 | `recall_rrf()` |
| `Graph` | Hybrid RRF + graph-signal reranking | `recall_rrf()` + `rerank_with_graph()` |

### FTS5 Details (fts5.rs)

- Phrase search: query wrapped in double quotes
- Token fallback: split query into 2+ char tokens, join with OR, limit 10 tokens
- Ranks by FTS5 `bm25` (negative values, lower = better match)
- Filters: namespace, deprecated=0, tag (post-filter in RRF path)
- memory_type column added to FTS5 index in migration v14 (#662)

### Recall Cache

- TTL-based LRU, keyed by (query_hash, namespace, limit, strategy)
- max_entries=256, ttl_secs=300
- `min_score` NOT part of cache key — re-applied after lookup
- Salience/recency boosts applied AFTER caching

## 7. Offline Status

**With default ONNX backend (after one-time model download): 100% offline runtime.**

Online calls that exist:
1. **Model download** (one-time): `huggingface.co` via `reqwest::blocking` — cached at `~/.uteke/models/embeddinggemma-q4/`
2. **OpenAI backend** (opt-in): POST to OpenAI-compatible API when `backend=openai`
3. **Ollama backend** (opt-in): POST to local Ollama server when `backend=ollama`
4. **Fallback embedder** (opt-in): Wraps ONNX + optional cloud fallback — only with `[embed_fallback]` config

`reqwest` is a **hard dependency** (Cargo.toml line 27) — always compiled in, even when unused.

## 8. Room-Based Coordination

Source: `memory/rooms.rs`, `rooms.rs` (lib.rs)

| Table | Schema |
|-------|--------|
| `rooms` | id TEXT PK, title TEXT, namespace TEXT NOT NULL, created_at, updated_at |
| `room_memories` | room_id + memory_id (composite PK), author TEXT NOT NULL, role TEXT DEFAULT 'participant', joined_at TEXT NOT NULL |

Features: create_room, get_room, list_rooms, room_stats, link_memory_to_room, recall_room (chronological + semantic), room_summary (LLM-free topic clustering via tag co-occurrence), room_document generation. Cross-namespace: rooms can contain memories from any namespace.

## 9. Knowledge Graph (Dual System)

Source: `graph.rs`, `edges.rs`, `graph_rerank.rs`

### System 1: Memory Edges (auto-wired)
- `memory_edges` table: typed edges between memories (references, supersedes, replies_to, tagged_as, similar_to, possible_duplicate)
- Auto-generated from content patterns: `[[slug]]`, `@tag`, `^uuid`, `><uuid`
- Backlinks auto-generated via `BACKLINKED_EDGE_TYPES`

### System 2: Graph Nodes/Edges (rich entity graph)
- `graph_nodes` + `graph_edges` tables
- BFS neighbor traversal, shortest path, triple queries
- Supports weighted edges, entity types, properties JSON

### Graph Reranking (post-RRF)
- Computes signals: edge_count, neighbor_count, edge_type_diversity, incoming/outgoing
- Additive + log-scaled boosts — isolated memories untouched, connected memories drift upward
- Only for `RecallStrategy::Graph`

### Multi-hop Traversal
- `recall_related()`: initial hybrid recall → BFS with `score * 0.8` decay per hop
- `get_related()`: UNION of edge table (O(log n)) + legacy metadata scan (O(n) — known bottleneck, pitfall #58)
