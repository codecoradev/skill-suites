# Embedding Dimension Strategy — Locked Decision (Jul 2026)

## Context

Analysis of embedding dimensions across the CodeCora ecosystem (cora-code, uteke) to determine optimal dimensionality for current and future phases.

## Model Comparison

| Model | Full Dims | Matryoshka Dims | Used In | Code-Specific? |
|-------|-----------|-----------------|---------|---------------|
| **EmbeddingGemma Q4** | 768d | 128, 256, 512, 768 | uteke (full 768d, no truncation) | No — general purpose |
| **Voyage-4-Nano** | 2048d | 256, 512, 1024, 2048 | — (planned for cora-code Phase 5) | Yes — code-optimized |
| **Static tokens** (hashing trick) | 256d | N/A (not a model) | cora-code Phase 3 | N/A — pseudo-random projections |

## Key Fact: Matryoshka = Prefix Truncation

Matryoshka Representation Learning (MRL) trains models so the first N dimensions carry the most information. Truncating from 2048→256 means taking the first 256 dimensions, not compressing. Quality drop is minimal (~2-5% NDCG) because the model is trained to concentrate importance in early dimensions.

## Locked Decisions

### D1: Static tokens stay at 256d forever (not configurable)

256 is intrinsic to the hashing trick algorithm (`tokens.rs`). It's not a knob — changing it produces more noise dimensions, not better quality. Making it configurable is YAGNI. This is documented in `cora-code` skill pitfalls.

### D2: Phase 5 uses Voyage Matryoshka 256d (not 1024d)

**Reasoning:**
1. **Same usearch index file** — swap `embed_code()` from hash to Voyage truncated prefix, zero infra change
2. **Massive quality jump** — pseudo-random noise → real contextual embedding at same 256 dims
3. **No schema migration** — `embedding_dims` stays 256, `DEFAULT_DIMS` stays 256
4. **Model size unchanged** — 340M params ONNX ~1.4GB regardless of truncate dim
5. **Future upgrade path** — if 512d needed, create separate `cora_index_512.usearch` file

### D3: Uteke stays at EmbeddingGemma 768d (no change)

Different product, different vector space. Phase 4 cora↔uteke integration sends text via HTTP API, not vectors. Each system embeds with its own model. No need to align dimensions.

**Uteke dimension config exists but has NO Matryoshka truncation.** `EmbeddingConfig.dims` in `uteke.toml` (default 0 = use model default = 768). Setting `dims=256` would crash — ONNX outputs 768d but usearch would expect 256d. The `dims` field only affects usearch init and OpenAI API calls, NOT ONNX output truncation.

### D4: Voyage-4-Nano over EmbeddingGemma for code

Voyage Nano is code-optimized (benchmarked on code retrieval tasks, part of Voyage 4 series). EmbeddingGemma is general-purpose. For `cora brain` code search, Voyage is the right choice. uteke keeps EmbeddingGemma for general memory.

## Performance Benchmarks (real, measured Jul 2026)

**Environment:** local machine, debug build, ~1,700 symbols (cora-code repo).

| Operation | Time | Per-item | Notes |
|-----------|------|----------|-------|
| **Hash embed 1 vector** | — | **0.7μs** | FNV-1a + bag-of-words, pure Rust. NOT 100ms. |
| **Hash embed 1K vectors** | 0.68ms | 0.7μs | |
| **Full index rebuild** (1,734 sym) | **5.3s** | ~3ms/sym | Includes tree-sitter parse + SQLite write + hash embed + usearch insert |
| **Brain search (1 query, cold)** | **42ms** | 42ms | Includes process spawn + hash embed query + usearch KNN + FTS5 + RRF |
| **Brain search (100 batch)** | 4.9s | 49ms/query | 100× process spawn overhead |

### Warm Search Breakdown (real, measured Jul 2026)

| Command | Latency | What it does |
|---------|---------|-------------|
| `cora --version` | 4.5ms | Process spawn only |
| `cora explore "X" --json` | 6.6ms | SQLite graph query |
| `cora callers "X" --json` | 9.3ms | SQLite graph + tree-sitter |
| `cora impact "X" --json` | 9.5ms | SQLite graph traversal |
| `cora brain "X" --json` | **37ms** (warm) / **52ms** (cold) | FTS5 + usearch + graph + RRF |

**Brain search bottleneck breakdown (37ms warm):**

```
brain search 37ms
├─ Process spawn       4.5ms  (12%)
├─ SQLite open+init     2ms   (5%)
├─ FTS5 text search     3ms   (8%)
├─ Hash embed query   0.001ms  (0%)  ← negligible
├─ usearch KNN        ~25ms   (68%)  ← BOTTLENECK
└─ RRF fusion + JSON    2ms   (5%)
```

Bottleneck is usearch KNN (~25ms for 1,734 vectors, 256d, cosine). Hash embed is negligible (0.7μs). For agent usage (50 queries/session), total search overhead ≈ 1.8 seconds.

### `--memory` / `--learn` vs Phase 4 (distinct features)

**Uteke docs hidden (Jul 2026):** README + 4 docs files + install-bundle.sh had all uteke references removed (176 lines, 6 files). Code still compiles. See `cora-code-dev` skill for details.

README "Uteke Memory Integration" section **was removed** — it referred to **existing** `cora review --memory --learn` feature (`src/engine/memory.rs`). This is NOT Phase 4. Two separate integrations:

| Feature | Status | Integration |
|---------|--------|-------------|
| `cora review --memory` | ✅ Ships now | cora subprocess calls `uteke` CLI for recall before review |
| `cora review --memory --learn` | ✅ Ships now | Same + saves findings to uteke after review |
| `cora brain --learn` (Phase 4) | 🔜 Planned | Push code patterns to uteke via HTTP API |
| Cross-project uteke recall in `brain` (Phase 4) | 🔜 Planned | uteke HTTP `/search` enrichment |

**Voyage ONNX estimates (Phase 5, NOT current):**

| Operation | Estimated | Notes |
|-----------|-----------|-------|
| Voyage embed 1 vector | **~100ms** | ONNX inference, single-threaded |
| Voyage embed 1K vectors | ~100s | Can be parallelized with rayon |
| Full reindex 5K symbols | ~8 min | One-time migration cost |
| Incremental (10 changed files) | ~1s | Daily use after initial migration |

**Critical distinction:** 100ms/vector is the ONNX inference cost for Voyage (Phase 5). Current static hash is ~0.7μs/vector — **150,000× faster**. This is why static tokens are the default.

## Dimension Change Migration Design (Phase 5)

### Problem

`CodeVectorIndex::load_or_create(path, dims)` in `vector.rs`:
- If usearch file is empty → creates new index with `dims` parameter ✅
- If usearch file exists → `load_from_file()` → **ignores `dims` parameter entirely** ⚠️

Changing dims in config would load old-dims index, then crash on dimension mismatch when inserting vectors.

### Required Fix

```rust
pub fn load_or_create(path: &Path, dims: usize) -> Result<Self> {
    // ... acquire file lock ...
    let mut idx = if lock_file.metadata()?.len() == 0 {
        Self::new(dims)?
    } else {
        let loaded = Self::load_from_file(&mut lock_file, path)?;
        if loaded.index.dimensions() != dims {
            tracing::warn!(
                old_dims = loaded.index.dimensions(),
                new_dims = dims,
                "Vector dimension changed — deleting index and re-creating"
            );
            drop(loaded);
            std::fs::write(path, []).context("truncate usearch file")?;
            Self::new(dims)?
        } else {
            loaded
        }
    };
    idx.path = Some(path.to_path_buf());
    idx._lock_file = Some(lock_file);
    Ok(idx)
}
```

### When Reindex Is Required

| Change | Reindex? | Index file action |
|--------|----------|-------------------|
| Tier change (static → voyage, same 256d) | **Yes** (different vector space) | Overwrite in-place (same dims) |
| Dims change (256 → 512) | **Yes** | Delete + recreate (different dims) |
| Dims change (512 → 256) | **Yes** | Delete + recreate |
| Code changed (`cora index`) | **No** (incremental) | Add/update only changed symbols |
| Voyage model version update | **Yes** (vector space may differ) | Overwrite in-place |

## Migration Path (Phase 5 Implementation)

```
Current (Phase 3):          Phase 5:                     Future (opt):
Static Hash 256d      →    Voyage MRL 256d          →   Voyage MRL 512d
EMBEDDING_DIM=256           truncate_dim=256               truncate_dim=512
1 index file                 1 index file (same!)           2nd index file
```

Implementation: swap `embed_code()` in `embed/mod.rs` to call Voyage ONNX instead of hashing trick, truncate output to first 256 dims. Everything else (usearch, schema, RRF, brain.rs) stays unchanged.

## Sources

- Voyage-4-Nano HF: https://huggingface.co/voyageai/voyage-4-nano
- Voyage-4 blog: https://blog.voyageai.com/2026/01/15/voyage-4/
- EmbeddingGemma docs: https://ai.google.dev/gemma/docs/embeddinggemma
- Matryoshka paper: https://arxiv.org/abs/2205.13147
