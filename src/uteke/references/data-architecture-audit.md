# Uteke Data Architecture Audit

Comprehensive audit of entity relationships, recall strategies, and scalability. Verified Jul 15, 2026 against v0.7.3 source (schema v14).

## Entity Relationship Map

```
┌──────────┐     room_memories      ┌──────────┐
│  ROOMS   │◄──────────────────────►│ MEMORIES │
│          │  (room_id, memory_id,  │          │
│  - id    │   author, role)        │  - id    │──► memory_edges ◄──┐
│  - title │                        │  - slug  │    (auto-wired)     │
│  - ns    │                        │  - embed │◄──► memory_tags    │
└──────────┘                        │  - meta  │                    │
                                    │  - type  │──► graph_nodes ◄──┐
                                    │  - imp   │    (memory_id FK) │
                                    │  - pin   │                    │
                                    └────┬─────┘               ┌──┴──────────┐
                                         │                     │ GRAPH       │
                                    memory metadata           │ graph_nodes │
                                    ("relationships" [])      │ graph_edges │
                                    (legacy edge system)      └─────────────┘

┌──────────────┐     document_chunks   ┌──────────────┐
│  DOCUMENTS   │◄─────────────────────►│  DOC_CHUNKS  │
│              │  (1:N with embedding) │              │
│  - id/slug   │                       │  - embed BLOB│
│  - hierarchy │  (parent_id, path,   │  - heading   │
│  - depth=10  │   sort_order)         │  - content   │
│  - version   │                       └──────────────┘
└──────────────┘     NO FK to memories
```

## Entity Relationships

| From → To | Mechanism | FK? | Status |
|-----------|-----------|-----|--------|
| Room → Memory | `room_memories` junction | ✅ ON DELETE CASCADE | ✅ |
| Memory → Memory (edges) | `memory_edges` table | ✅ ON DELETE CASCADE | ✅ |
| Memory → Memory (legacy) | `metadata.relationships` JSON | ❌ Soft ref by ID | ⚠️ Dual system |
| Memory → Tags | `memory_tags` junction | ✅ ON DELETE CASCADE | ✅ |
| Memory → graph_nodes | `graph_nodes.memory_id` FK | ✅ ON DELETE SET NULL | ✅ |
| graph_nodes → graph_edges | `graph_edges.source_id/target_id` FK | ✅ ON DELETE CASCADE | ✅ |
| Document → doc_chunks | `doc_chunks.document_id` FK | ✅ ON DELETE CASCADE | ✅ |
| **Memory ↔ Document** | **None** | ❌ | 🚨 Missing |
| **Room → Document** | **None** | ❌ | 🚨 Missing |
| graph_nodes ↔ Document | None | ❌ | By design |

## Dual Edge System (graph.rs)

Two coexisting systems for memory-to-memory relationships:

1. **Table-based (`memory_edges`)** — v0.2.0+, indexed SQL, O(log n). Auto-wired from content patterns: `[[slug]]`→references, `@tag`→tagged_as, `^uuid`→supersedes, `><uuid`→replies_to. Backlinks auto-generated (referenced_by).
2. **Metadata-based (`metadata.relationships` JSON)** — v0.1.0+, unindexed, O(n) scan. Legacy.

`get_related()` in `graph.rs:133-167` does a **UNION** of both sources. The metadata reverse scan (line 153-165) calls `self.store.load_all(None)?` — **O(n) full table scan for every call**.

## Recall Strategies & Relevance Ranking

| Method | Strategy | Complexity | Signals |
|--------|----------|------------|---------|
| `recall()` | Vector (usearch HNSW) | O(k·log n) | Cosine similarity + salience + recency + graph rerank |
| `recall_hybrid()` | Vector + FTS5 + RRF merge | O(k·log n) + O(FTS) | RRF fusion |
| `recall_context()` | Hybrid + depth expansion | O(k·log n) + O(d²) | Multi-hop traversal (0.8 decay/hop) |
| `search()` | FTS5 keyword | O(text scan) | BM25 |
| `recall_room()` | Fetch room IDs → hybrid → post-filter | O(room_size) | Hybrid scores |
| `recall_room_semantic()` | Over-fetch hybrid → filter to room | O(k·log n) | Hybrid, capped at 200 |
| `recall_related()` | Initial recall → graph BFS | O(k·log n) + O(edges) | Embedding + relationships |
| `recall_unified()` | Memory + Document hybrid → RRF | O(k·log n) + O(doc) | RRF cross-type |
| `recall_at_time()` | Recall with temporal filter | O(k·log n) | Cosine + valid_from/valid_until |

### Reranking Pipeline

```
embedding similarity → salience boost → recency boost → graph rerank → min_score filter → limit
```

All boosts are **additive**, never dominate embedding score. Default weights: 0.1-0.15.

## Scalability at Scale

| Component | Mechanism | Limitation |
|-----------|-----------|------------|
| Vector recall | usearch HNSW O(k·log n) | Memory-based, ~400MB at 100K memories |
| FTS5 text search | SQLite FTS5 BM25 | ✅ Handles millions of rows |
| RRF merge | In-memory O(k·log n) | ✅ Efficient |
| Graph BFS | Indexed SQL via memory_edges | ✅ Indexed |
| Room recall | Over-fetch + post-filter | ⚠️ Hard cap 200 |
| Document search | Chunk-level embedding | ✅ Scalable |
| **`get_related()` reverse scan** | **O(n) full table scan** | 🚨 **Bottleneck at scale** |

## Known Issues (Jul 2026)

### 1. `get_related()` O(n) reverse scan (🚨 High priority)
- `graph.rs:153-165` — `self.store.load_all(None)?` scans ALL memories for reverse metadata edges
- Degrades linearly with memory count
- Fix: Remove reverse scan, rely on indexed `memory_edges` table only

### 2. Room operations: 0 tests (🟡 Medium)
- `memory/rooms.rs` and `rooms.rs` have zero test functions
- CRUD + recall + summary + document — all untested
- Regression risk

### 3. Memory ↔ Document: no relationship (🟢 Low)
- Entities live in separate worlds
- `recall_unified(all)` merges via RRF but has no link semantics
- Convention: store doc slug in memory metadata as workaround

### 4. Dual edge system creates confusion
- Table-based edges (auto-wired) vs metadata-based (legacy)
- Both systems exist for backward compat
- Recommendation: deprecate metadata edges, migrate to table-only

## access_count Coverage (verified)

All recall paths that increment `access_count`:

| Function | touch_access? | Location |
|----------|:---:|----------|
| `recall()` | ✅ | operations.rs |
| `recall_hybrid()` | ✅ | via `_merge_rrf()` |
| `recall_context()` | ✅ | operations.rs |
| `recall_at_time()` | ✅ | via `recall()` internally |
| `get()` | ✅ | operations.rs |
| `search()` | ✅ | operations.rs (fixed PR #687) |

## UnifiedSearchResult Fields (v0.7.3+)

Since PR #688, `UnifiedSearchResult` includes all memory detail fields:

**Memory results:** `memory_type`, `namespace`, `source`, `source_type`, `importance`, `pinned`, `access_count`, `last_accessed`, `created_at`, `updated_at` — all populated from Memory struct.

**Document results:** All memory-specific fields are `None` (omitted via `skip_serializing_if`).

**CLI output:** `print_unified_human()` shows type, source, importance, pinned 📌, access count.
