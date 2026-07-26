# Uteke Architecture Deep Dive

**Source:** Codebase analysis session 2026-06-09, updated 2026-06-28
**Source version:** v0.5.0 (latest release, June 27, 2026)

## Workspace Structure

```
~/uteke/
├── Cargo.toml              # Workspace: resolver="2", members=[uteke-core, uteke-cli]
├── crates/
│   ├── uteke-core/         # Core engine library (SQLite + ONNX/OpenAI/Ollama + usearch + FTS5 + Graph)
│   └── uteke-cli/          # CLI binary (clap, 14+ command modules + extract.rs)
├── tests/                  # Integration tests
├── docs/                   # VitePress website
├── install.sh              # curl | sh installer
├── Dockerfile              # Docker support
└── CHANGELOG.md            # Keep a Changelog format
```

## Core Crate Module Map (uteke-core)

```
crates/uteke-core/src/
├── lib.rs                  # Public API: Uteke struct, ensure_embedder(), config resolution
├── operations.rs           # High-level operations (remember, recall, forget, doc_search, etc.)
├── types.rs                # DoctorReport, VerifyReport, RepairReport, EmbeddingSettings
├── error.rs                # Error enum with sanitized messages
├── consolidate.rs          # Near-duplicate memory merging
├── import_export.rs        # JSONL import/export
├── maintenance.rs          # Doctor, verify, repair operations
├── chunker.rs              # Markdown chunker for document engine
├── edges.rs                # Entity graph + backlinks + batch edge insert
├── graph.rs                # Entity graph adjacency + traversal
├── graph_rerank.rs         # Graph-augmented reranking for recall
├── salience_recency.rs     # Dual-axis time/usage boost for recall
├── recall_cache.rs         # Dedup cache for repeated queries
├── embed/
│   ├── mod.rs              # Module exports + validate_base_url + Embedder re-exports
│   ├── embed_trait.rs      # Embedder trait (embed, dims, max_seq_len, name)
│   ├── engine.rs           # ONNX EmbeddingGemma Q4 (768d, max_seq_len=2048 as of v0.5.0)
│   ├── openai.rs           # OpenAI-compatible embedding backend (text-embedding-3-small)
│   └── ollama.rs           # Ollama embedding backend (nomic-embed-text)
└── memory/
    ├── mod.rs              # Re-exports + VectorIndex
    ├── store.rs            # Store struct — SQLite + vector dual-write
    ├── schema.rs           # SQLite schema creation + migration framework
    ├── crud.rs             # Basic CRUD + search_content (LIKE)
    ├── types.rs            # Memory, MemoryTier, SearchResult, StoreStats, etc.
    ├── tags.rs             # Tag management via json_each() queries
    ├── vector.rs           # usearch HNSW index with disk persistence
    ├── aging.rs            # Time-based tier classification (hot/warm/cold)
    ├── bulk.rs             # Bulk delete operations (by tag, cold, all)
    ├── fts5.rs             # FTS5 virtual table for text search
    ├── documents.rs        # Document engine — hierarchical docs + chunk-level embedding
    └── rooms.rs            # Room-based namespace isolation
```

## Key Architecture Decisions

### 1. Embedding: Multi-Backend (v0.5.0)
- **Default:** ONNX EmbeddingGemma Q4 (768d) — local, free, auto-download
- **OpenAI:** `text-embedding-3-small` (1536d) — via `[embedding]` config or `UTEKE_EMBEDDING_*` env
- **Ollama:** `nomic-embed-text` (768d) — via `[embedding] backend = "ollama"`
- **Selection:** `ensure_embedder()` lazy init dispatches based on `embedder_backend` string
- **Max seq length:** 2048 tokens (v0.5.0 upgrade from 256)
- **Dims mismatch detection:** Refuses to mix vectors from different backends in one index (#337)

### 2. Embedder Trait Pattern
```rust
pub trait Embedder: Send + Sync {
    fn embed(&self, text: &str) -> Result<Vec<f32>, Error>;
    fn dims(&self) -> usize;
    fn max_seq_len(&self) -> usize;
    fn name(&self) -> &str;
}
```
All backends implement this. Uteke wraps in `Mutex<Box<dyn Embedder>>` for thread safety.

### 3. Config Resolution Pattern (CLI flag > env > toml > default)
```rust
EmbeddingSettings::resolve_with_defaults(input)
  → UTEKE_EMBEDDING_API_KEY > OPENAI_API_KEY > input.api_key
  → empty env var does NOT clobber non-empty config (CodeCora finding)
```
Same pattern used for extraction config, fallback config.

### 4. Vector Index: usearch HNSW
- **Library:** `usearch` v2
- **Persistence:** `.usearch` file + `.keys` sidecar for key→UUID mapping
- **Metrics:** Cosine similarity
- **Operations:** Incremental insert/delete, no rebuild needed
- **Startup:** Loads from disk in ~5ms
- **Keys:** `"mem:{uuid}"` for memories, `"chunk:{uuid}"` for document chunks

### 5. SQLite Schema (v11 as of v0.5.0)
- **Schema versioning:** `schema_version` table + migration framework
- **Tag storage:** JSON array in column, queried via `json_each()`
- **Dual-write:** SQLite first, then vector index
- **FTS5:** `memories_fts` virtual table for text search
- **Documents:** `documents` (full content) + `document_chunks` (chunked + embedded)

### 6. Document Engine (v0.5.0)
- Hierarchical docs with depth-10 support (#438)
- Materialized path for O(1) subtree queries
- Auto-chunk via `chunk_markdown(content, max_chars)`
- Each chunk → embed → `document_chunks` + vector index
- Hybrid search: FTS5 + vector → RRF fusion (k=60)
- Commands: `uteke doc create/get/list/search/move/delete/export`

### 7. LLM Fact Extraction (v0.5.0, PR #477)
- `uteke import --extract` — opt-in, offline-first
- OpenAI-compatible chat-completions endpoint
- Distills noisy text into atomic facts (max 20 per doc)
- Config: `[extraction]` section or `UTEKE_EXTRACTION_*` env vars
- API key falls back to embedding/OPENAI_API_KEY
- Source: `crates/uteke-cli/src/extract.rs` (399 LOC)

### 8. Entity Graph + Reranking
- `memory_edges` table with backlink enforcement (#350)
- `add_memory_edges_batch()` — atomic tx batch insert
- Graph-augmented reranking for recall (configurable weights)

### 9. Error Handling
- `Error` enum with sanitized user-friendly messages
- `Error::embed()`, `Error::db()`, `Error::validation()` constructors
- Internal details NOT exposed to users

## Key Constants

```rust
pub const MAX_CONTENT_LENGTH: usize = 10_000;   // 10K chars per memory
pub const MAX_TAGS_COUNT: usize = 20;            // 20 tags max per memory
pub const MAX_TAG_LENGTH: usize = 50;            // 50 chars per tag
pub const MAX_PAYLOAD_SIZE: usize = 1_048_576;   // 1MB server payload
// Extract defaults
const DEFAULT_MAX_FACTS: usize = 20;             // max facts per document
const REQUEST_TIMEOUT_SECS: u64 = 120;           // extraction timeout
// Embed defaults
const MAX_SEQ_LEN: usize = 2048;                 // ONNX max tokens (v0.5.0)
const MODEL_DIMS: usize = 768;                  // EmbeddingGemma Q4
```

## Build Profile (Release)

```toml
[profile.release]
opt-level = "z"       # Optimize for size
lto = true            # Link-time optimization
codegen-units = 1     # Single unit for better LTO
strip = true          # Strip debug symbols
panic = "abort"       # Smaller panic handler
```

## Dependencies (uteke-core, v0.5.0)

| Crate | Version | Purpose |
|-------|---------|---------|
| `rusqlite` | 0.40 (bundled) | SQLite storage |
| `usearch` | 2 | HNSW vector index |
| `ort` | 2.0.x | ONNX Runtime for embedding |
| `reqwest` | 0.12 (rustls) | HTTP clients (embed + extract) |
| `tokenizers` | 0.21+ | Text tokenization |
| `serde`/`serde_json` | 1/1 | Serialization |
| `uuid` | 1 (v4) | Memory IDs |
| `chrono` | 0.4 | Timestamps |
| `sha2` | — | Model checksum verification |

## Key Limitations (v0.5.0)

| Limitation | Detail |
|-----------|--------|
| **No batch/directory import** | `uteke import` accepts single file or stdin only. See `batch-import-design.md` for planned v0.6.0. |
| **No embed fallback** | Local ONNX fail = error. No auto-switch to cloud. See `batch-import-design.md`. |
| **No parallel extraction** | Sequential only. See `batch-import-design.md` for planned `--extract-parallel`. |
| **Extraction = API required** | `--extract` needs OpenAI-compatible endpoint. Cannot extract offline. |
| **Document import = single file** | `uteke doc create` accepts one file at a time. No batch directory mode. |
