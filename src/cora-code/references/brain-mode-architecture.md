# Brain Mode Architecture — Research & Design Reference

Compiled from deep-dive research (Jul 2026). Covers embedding model analysis, CBM reference architecture, and implementation plan.

## 1. Codebase-Memory-MCP (CBM) — Reference Architecture

**Repo:** [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) — 33.3K stars, pure C, MIT license.

### The Secret Sauce: Static Token Embeddings

CBM does NOT run nomic-embed-code (7B) at runtime. Instead:

1. **One-time extraction** (`scripts/extract_nomic_vectors.py`):
   - Load full nomic-embed-code (7B)
   - Filter vocabulary → 40,856 code-relevant tokens (alphanumeric + underscore only)
   - Per-token inference → 40,856 × 768 dim float vectors
   - Int8 quantization + unit-vector normalization
   - Simulated attention (K=32 neighbors, 3 iterations, α=0.3 blend)
   - Mean centering (remove anisotropy)
   - Output: `code_vectors.bin` (~12MB) + `code_tokens.txt`

2. **Runtime** (C implementation):
   - **Bag-of-tokens**: tokenize code → lookup per-token static vectors → average → cosine similarity
   - Zero model weights, zero ONNX runtime, zero GPU
   - Files: `vendored/nomic/code_vectors.bin`, `code_tokens.h`, `code_tokens.txt`, `code_vectors_blob.S`

### CBM Knowledge Graph

**Node types:** Project, Package, Folder, File, Module, Class, Function, Method, Interface, Enum, Type, Route, Resource

**Edge types:** CALLS, IMPORTS, DEFINES, IMPLEMENTS, INHERITS, HTTP_CALLS, DATA_FLOWS, SIMILAR_TO, SEMANTICALLY_RELATED

**Storage:** SQLite (RAM-first pipeline with LZ4 + in-memory SQLite). Linux kernel 28M LOC = 3 min.

**Tree-sitter:** 158 languages, 159 pre-generated parsers vendored as C.

**Team sharing:** `.codebase-memory/graph.db.zst` — compressed graph artifact, commit to repo, teammates skip reindex.

**15 MCP tools:** `index_repository`, `search_graph`, `trace_path`, `detect_changes`, `query_graph` (Cypher), `get_architecture`, `semantic_query`, `search_code`, `manage_adr`, etc.

**Token savings:** 5 structural queries = ~3,400 tokens vs ~412,000 via file-by-file — **99.2% reduction**.

## 2. Embedding Model Deep Dive

### Nomic-Embed-Code (Static Token Source)

| Spec | Value |
|------|-------|
| Full model | 7B params (Qwen2.5-Coder-7B base) |
| Extracted tokens | 40,856 code-relevant |
| Output dimensions | 768d (int8 quantized) |
| License | Apache-2.0 |
| Training languages | Python, Java, Ruby, PHP, JavaScript, Go |
| Full model benchmark | SOTA on CodeSearchNet (outperforms Voyage Code 3, OpenAI Embed 3 Large) |

**Key insight:** The 7B model knowledge is baked into the static token vectors. Even though runtime is bag-of-tokens (no positional context), the code-specific training means each token vector captures deep code semantics.

### Voyage-4-Nano (ONNX Full Inference)

| Spec | Value |
|------|-------|
| Params | 340M (180M non-embed + 160M embed) |
| Architecture | Qwen3ForCausalLM (bidirectional attention) |
| Context | 32,000 tokens |
| Dimensions | 1024 default (Matryoshka: 256/512/1024/2048) |
| ONNX size | ~1.41 GB |
| License | Apache-2.0 |
| Quantization | QAT — supports float32/int8/uint8/binary output |
| Code-specific | General + code capable (not code-only) |
| Open-weight | Yes, at [voyageai/voyage-4-nano](https://huggingface.co/voyageai/voyage-4-nano) |
| ONNX | at [onnx-community/voyage-4-nano-ONNX](https://huggingface.co/onnx-community/voyage-4-nano-ONNX) |

**Key feature:** Shared embedding space with entire Voyage 4 series — can use voyage-4-large for indexing and voyage-4-nano for local queries.

**Config.json details:**
```json
{
  "architectures": ["Qwen3ForCausalLM"],
  "hidden_size": 1024,
  "num_hidden_layers": 12,
  "num_attention_heads": 16,
  "num_key_value_heads": 8,
  "max_position_embeddings": 40960,
  "use_bidirectional_attention": true,
  "vocab_size": 151936
}
```

### Jina-Embeddings-v2-Base-Code (fastembed-rs native)

| Spec | Value |
|------|-------|
| Params | 161M |
| Context | 8,192 (ALiBi extrapolation) |
| Dimensions | 768 |
| License | Apache-2.0 |
| Languages | 30 programming languages + English |
| fastembed-rs | ✅ Already supported (`EmbeddingModel::JinaEmbeddingsV2BaseCode`) |
| ONNX | ✅ Available via Xenova/Transformers.js ecosystem |

### fastembed-rs — Rust Embedding Library

**Repo:** [Anush008/fastembed-rs](https://github.com/Anush008/fastembed-rs) — 968 stars, v5.17.3

- Uses `ort` (ONNX Runtime) + `huggingface/tokenizers`
- Auto-downloads models on first use, cached locally
- Supports: BGE, nomic-embed-text, Jina Code, EmbeddingGemma, Snowflake Arctic, Qwen3, CLIP, rerankers
- Feature flags for candle backend (Qwen3, nomic-v2-moe)
- `FASTEMBED_CACHE_DIR` or `HF_HOME` for cache control

## 3. Comparison Table: All Options for cora-code

| Aspect | nomic-embed-code static | Voyage-4-Nano ONNX | Jina Code (fastembed) | EmbeddingGemma (uteke) |
|--------|------------------------|-------------------|----------------------|----------------------|
| Inference quality | Bag-of-tokens (good) | Full contextual (best) | Full contextual (good) | Full contextual (general) |
| Model size at runtime | ~12 MB | ~1.41 GB | ~330 MB | ~150 MB |
| Memory usage | ~12 MB | ~1.5-2 GB | ~400 MB | ~200 MB |
| Latency per embed | ~0.1ms | ~100-500ms | ~50-200ms | ~30-100ms |
| External deps | None | `ort` crate | `fastembed` crate | Already in uteke |
| Code-specific | ✅ Yes (7B code model) | General + code | ✅ Yes (code-trained) | ❌ General |
| Context awareness | ❌ Bag-of-tokens | ✅ 32K positional | ✅ 8K positional | ✅ 2K positional |
| License | Apache-2.0 | Apache-2.0 | Apache-2.0 | Apache-2.0 |
| One-time cost | 6-10h CPU / GPU | None | None | None |

## 4. Implementation Phases

### Phase 0: Rename cora-cli → cora-code ✅ DONE (Jul 2026)
- GitHub repo `codecoradev/cora-cli` → `codecoradev/cora-code` (PR #353 merged, 10/10 CI green)
- Crate name `cora-code`, all docs/CI/install scripts/VitePress config updated
- Cargo.lock regenerated, `cargo check` clean
- GitHub auto-redirects old URLs (301)
- Binary stays `cora`, local dir `<your-project-dir>
- cora-code memories saved to uteke room `cora-code` (namespace: `cto`)

### Phase 1: Static Token Embedding
- Fork CBM extraction script → `scripts/extract_code_tokens.py`
- Run extraction → `code_vectors.bin` + `code_tokens.rs`
- Implement bag-of-tokens in `src/embed/tokens.rs`
- Bundle via `include_bytes!` or git-lfs
- Add THIRD_PARTY.md (nomic-embed-code Apache-2.0)

### Phase 2: Knowledge Graph + Tree-sitter
- `tree-sitter` crate + grammar bindings (Rust, Go, Python, TS first)
- Upgrade `index/extract.rs` → tree-sitter AST
- SQLite graph schema: `nodes` + `edges` tables
- `cora index` / `cora graph query` / `cora trace` / `cora arch` subcommands
- Change detection: `cora index --diff` → impact analysis

### Phase 3: Brain Mode Embedding Integration
- Embedding config in `.cora.yaml`: tier selection
- Vector storage (SQLite int8 vectors or pass to uteke)
- `cora brain <query>` — hybrid search
- `cora review --brain` — auto-enrich context
- `cora impact <file>` — change impact

### Phase 4: Uteke Integration Upgrade
- `cora brain --learn` → push patterns to uteke
- Cross-project recall via uteke
- `.cora/graph.db.zst` for team sharing
- `cora serve --mcp` → MCP tools for AI agents

### Phase 5: Voyage-4-Nano ONNX (Optional)
- Add `ort` dependency
- Download ONNX model on first use (fastembed pattern)
- Wrapper in `src/embed/voyage.rs`
- MRL dimension support (256/512/1024/2048)

## 5. Key External References

- [CBM repo](https://github.com/DeusData/codebase-memory-mcp)
- [CBM THIRD_PARTY.md](https://github.com/DeusData/codebase-memory-mcp/blob/main/THIRD_PARTY.md) — vendoring details
- [CBM extraction script](https://github.com/DeusData/codebase-memory-mcp/blob/main/scripts/extract_nomic_vectors.py) — 528 lines
- [CBM nomic NOTICE](https://github.com/DeusData/codebase-memory-mcp/blob/main/vendored/nomic/NOTICE) — derivation procedure
- [nomic-embed-code model](https://huggingface.co/nomic-ai/nomic-embed-code) — 7B, Apache-2.0
- [Voyage-4-Nano](https://huggingface.co/voyageai/voyage-4-nano) — 340M, Apache-2.0
- [Voyage-4-Nano ONNX](https://huggingface.co/onnx-community/voyage-4-nano-ONNX) — 1.41GB ONNX
- [Voyage docs](https://docs.voyageai.com/docs/embeddings) — model specs
- [Jina Code v2](https://huggingface.co/jinaai/jina-embeddings-v2-base-code) — 161M, 8K context
- [fastembed-rs](https://github.com/Anush008/fastembed-rs) — Rust ONNX embedding library
