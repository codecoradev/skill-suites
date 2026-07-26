# FTS5 Hybrid Search — Design + Implementation

Source: Design from CTO session 2026-06-10. **NOW IMPLEMENTED (v0.7.3, Jul 2026).** Source-verified implementation details in [`references/source-verified-internals.md`](source-verified-internals.md).

> ⚠️ **This file is the pre-implementation design doc.** The actual implementation differs:
> - FTS5 table uses `content='memories', content_rowid='rowid'` (NOT `content_rowid='id'`)
> - FTS5 columns include `memory_type` (added migration v14, #662)
> - RRF k=60 is hardcoded as `const RRF_K: u32 = 60` (not configurable)
> - Over-fetch is `limit * 3` (not `limit * 2`)
> - Token fallback exists (split into 2+ char tokens, OR-joined, max 10)
> - Normalization: `(score / max_rrf).clamp(0.0, 1.0)` where `max_rrf = 2/(k+1)`
> - Salience/recency boosts applied post-RRF (opt-in per query)
> - 4 strategies: Vector, Fts5, Hybrid, Graph (graph = hybrid + graph-rerank)

## Why FTS5 + Vector Hybrid?

Sibyl-Memory scored 95.6% on LongMemEval #2 using **FTS5 only** (zero embeddings, sub-ms recall). This proves FTS5 is extremely effective for structured/exact-match queries. However, vector search wins on conceptual/semantic queries.

**Industry standard:** Reciprocal Rank Fusion (RRF) to merge both result sets. Used by Elasticsearch, Pinecone, Weaviate.

| Query Type | FTS5 | Vector | Hybrid (RRF) |
|------------|------|--------|-------------|
| "deploy staging" (exact match) | ✅ Sub-ms | ✅ ~30ms | ✅ Best |
| "release to production" ↔ "deploy staging" (semantic) | ❌ | ✅ | ✅ |
| "bug-42" (ID lookup) | ✅ Exact | ⚠️ Might miss | ✅ |
| "architecture decision REST" | ⚠️ Partial | ✅ Conceptual | ✅ Best |

## Implementation Design (Uteke #250)

### Schema Changes

```sql
-- New FTS5 virtual table alongside existing memories table
CREATE VIRTUAL TABLE memories_fts USING fts5(
    content,
    tags,        -- comma-separated tags
    namespace,
    content='memories',
    content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER memories_fts_insert AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, content, tags, namespace)
    VALUES (new.id, new.content, new.tags, new.namespace);
END;

CREATE TRIGGER memories_fts_delete AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content, tags, namespace)
    VALUES ('delete', old.id, old.content, old.tags, old.namespace);
END;

CREATE TRIGGER memories_fts_update AFTER UPDATE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content, tags, namespace)
    VALUES ('delete', old.id, old.content, old.tags, old.namespace);
    INSERT INTO memories_fts(rowid, content, tags, namespace)
    VALUES (new.id, new.content, new.tags, new.namespace);
END;
```

### Recall Flow (Dual-Search + RRF)

```rust
fn recall_hybrid(query: &str, limit: usize) -> Vec<Memory> {
    // 1. Vector search (existing)
    let vector_results = vector_search(query, limit * 2); // over-fetch
    
    // 2. FTS5 search (new)
    let fts_results = fts5_search(query, limit * 2); // over-fetch
    
    // 3. Reciprocal Rank Fusion
    let merged = rrf_merge(vector_results, fts_results, k=60);
    
    // 4. Return top-N
    merged.into_iter().take(limit).collect()
}

fn rrf_merge(vector: Vec<ScoredMemory>, fts: Vec<ScoredMemory>, k: usize) -> Vec<Memory> {
    let mut scores: HashMap<u64, f64> = HashMap::new();
    
    for (rank, item) in vector.iter().enumerate() {
        *scores.entry(item.id).or_default() += 1.0 / (k + rank + 1) as f64;
    }
    
    for (rank, item) in fts.iter().enumerate() {
        *scores.entry(item.id).or_default() += 1.0 / (k + rank + 1) as f64;
    }
    
    // Sort by combined score, return memories
    // Items appearing in both sets get boosted
}
```

### CLI Flags

```bash
uteke recall "deploy"                 # Default: hybrid (FTS5 + vector)
uteke recall "deploy" --search vector # Vector only (semantic)
uteke recall "deploy" --search fts    # FTS5 only (exact/keyword)
uteke recall "deploy" --search like   # Legacy LIKE (backward compat)
```

## RRF Parameter Tuning

- `k=60` is the standard default (used by Elasticsearch, most academic papers)
- Lower k = more weight to top results from each ranker
- Higher k = more uniform blending
- Uteke should expose `k` as config: `search.rrf_k = 60`

## Current State (Pre-Implementation)

- `search_content` in `store.rs` uses `LIKE '%keyword%'` — weakest search method
- `recall` uses vector search via usearch — strong for semantic, misses exact matches
- No FTS5 virtual table exists yet
- Tracked in issue #250, labeled `v0.0.12`

## Migration Strategy

1. Add FTS5 table creation to `schema.rs` init
2. Build trigger for new memories (insert/update/delete)
3. One-time backfill: `INSERT INTO memories_fts SELECT id, content, tags, namespace FROM memories`
4. Add `--search` flag to CLI recall command
5. Default to hybrid, allow fallback to vector-only
