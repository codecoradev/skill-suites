---
name: cora-code
description: |
  Cora Code — complete guide covering usage (review, scan, brain search, code intelligence)
  AND development (architecture, Brain Mode roadmap, embedding strategy, CI pitfalls, tree-sitter).
  CLI binary cora. BYOK AI code review + code intelligence platform.
version: 4.3.0
metadata:
  author: CodeCoraDev
  hermes:
    tags: [cora, code-review, code-intelligence, pre-commit, ci, rust, cli, brain-mode, embedding]
---

# Cora Code — Code Intelligence & Review

Rust CLI for AI-powered code review + code intelligence. Binary `cora` (crate: `cora-code`). BYOK — use any LLM. Regex-based symbol extraction for 18 languages. Tree-sitter AST for 12 languages (feature-gated: rs, go, py, ts/tsx, java, c, cpp, c#, rb, php, scala, js-via-ts). Svelte routes through TypeScript grammar.

**Repo:** https://github.com/codecoradev/cora-code · **Branch:** `develop` (PR-only) · **CI:** GitHub Actions

> **Positioning (v0.7+):** cora-code is NOT just a code review tool. It is a **CODE INTELLIGENCE PLATFORM**. It does NOT write code (not an AI coding agent). It does NOT provide IDE features (not a language server). Tagline: *"Understand your code, deeply."*


| Command | Purpose |
|---------|--------|
| `cora init` | Create `.cora.yaml` in repo root |
| `cora config set model/base_url/provider` | Set LLM config (NOT via YAML) |
| `cora hook install` | Install pre-commit hook |
| `cora auth status` | Verify API key configured |
| `cora review --staged` | Review staged files (pre-commit) |
| `cora review --base origin/develop` | Review against branch |
| `cora review --unstaged` | Review unstaged working tree changes |
| `cora review --diff-file patch.patch` | Review arbitrary diff file |
| `cora config validate` | Validate `.cora.yaml` schema |
| `cora scan` | Static security scan (12 built-in rules + 13 security + 15 secret patterns) |
| `cora debt` | Tech debt metrics with trend history |
| `cora commit` | Review + generate message + commit in one step |
| `cora mcp` | MCP server (15 tools for AI agents) |
| `cora index` | Parse project → knowledge graph |
| `cora brain <query>` | Hybrid search: FTS5 + vector + graph |
| `cora trace <symbol>` | BFS path tracing across edges |
| `cora arch` | Architecture overview: modules, edge stats |
| `cora callers <symbol>` | Who calls this symbol |
| `cora impact <symbol>` | Recursive reverse-traversal impact |
| `cora affected <files>` | Find tests affected by changed files |
| `cora explore <query>` | FTS5 keyword search with filters |

## MCP Server Mode

Cora includes a built-in MCP (Model Context Protocol) server (`cora mcp`) that exposes 15 tools for AI agents:

```yaml
# Example agent config
mcp_servers:
  cora:
    command: "cora"
    args: ["mcp"]
    timeout: 30
    connect_timeout: 10
```

After restart, tools become `mcp_cora_brain_search`, `mcp_cora_find_callers`, `mcp_cora_find_impact`, `mcp_cora_review_diff`, `mcp_cora_check_snippet`, `mcp_cora_search_symbols`, `mcp_cora_find_affected_tests`, `mcp_cora_index_status`, `mcp_cora_list_rules`, `mcp_cora_get_quality_gate`, `mcp_cora_get_config`, `mcp_cora_get_project_info`, `mcp_cora_get_debt`, `mcp_cora_list_profiles`, `mcp_cora_get_memory`.

## When to Use

- Setting up cora in a new repo (pre-commit hook + CI)
- Before writing code in an indexed repo → `cora brain` recall
- Before refactoring → `cora callers` + `cora impact`
- After editing → `cora review --staged` or `cora commit`
- Understanding a codebase → `cora arch`, `cora trace`
- Debugging cora issues (auth, config, CI failures)
- Adding CI review to a repo

## Data Directory

All data at `~/.codecora/cora-code/`:
- `graph.db` — SQLite (symbols, FTS5, call graph, reviews)
- `cora_index.usearch` — Vector index (256d, static tokens)
- Multi-project: all indexed repos share one database

## Workflow 1: Recall Before Edit

**ALWAYS do this before writing new code or modifying existing patterns.**

```bash
cora index --stats   # Check if indexed (0 symbols → run cora index)
cora brain "<topic>" --json --limit 5
```

Parse JSON. Each result: `name`, `kind`, `file`, `line`, `signature`, `score`, `signals`.
If similar code exists → follow existing patterns.

## Workflow 2: Impact Check Before Refactor

```bash
cora callers "<symbol>" --json
cora impact "<symbol>" --json
```

| Callers | Action |
|---------|--------|
| 0 | Safe to modify (check tests) |
| 1-3 | Modify, update all callers |
| 4+ | Consider batch update approach |

## Workflow 3: Review + Commit

```bash
cora review --staged       # Review staged diffs
cora commit                 # Review + interactive commit
cora commit --yolo          # Non-interactive (agent use)
```

## Workflow 4: Code Intelligence

```bash
cora arch --json                              # Module overview
cora trace "<symbol>" --json --depth 3         # Call chain
cora explore "<query>" --json                  # Keyword search
cora affected <files> --json                   # Test impact
```

## JSON Output Schemas

### `cora brain --json`
`[{symbol_id, name, kind, file, line, signature, score, signals}]`
Signals: `fts`, `vector`, `graph`, or combinations.

### `cora callers --json`
`[{caller, file, line}]`

### `cora impact --json`
`[{symbol, file, line, depth}]`

### `cora explore --json`
`[{name, kind, file, line, signature, score, language}]`

### `cora trace --json`
`[{symbol, file, line, kind: CALLS|CALLED_BY, depth}]`

### `cora arch --json`
`{modules: [{name, files, symbols}], edge_counts: [[type, count]]}`

### `cora affected --json`
`["path/to/test_file", ...]`

## CLI Flags

| Command | Key Flags |
|---------|----------|
| `cora brain` | `--limit N`, `--json` |
| `cora explore` | `--kind function|struct|...`, `--lang rust|...`, `--limit N`, `--json` |
| `cora callers` | `--json`, `--limit N` |
| `cora impact` | `--json`, `--depth N` |
| `cora trace` | `--json`, `--depth N`, `--incoming` |
| `cora arch` | `--json` |
| `cora affected` | `--json`, `--test-glob "*test*"` |
| `cora review` | `--staged`, `--branch <name>`, `--diff <file>`, `--severity major|minor|info` |
| `cora commit` | `--yolo` |
| `cora index` | `--rebuild`, `--stats`, `--watch`, `--prune` |
| `cora scan` | `--include "src/**/*.rs"`, `--batch-files N` |

## Agent Operating Rules

1. **Check index first.** `cora index --stats` — if 0 symbols, run `cora index`.
2. **Always `--json`.** Parse structured output, not pretty-print.
3. **Recall before edit.** Run `cora brain` before writing non-trivial code.
4. **Impact check before refactor.** Run `cora callers` + `cora impact` first.
5. **Cross-project.** Results may come from other repos. Check `file` path.
6. **Re-index after changes.** `cora index` (incremental, fast).
7. **Doc-only commits: `--no-verify`.** Pre-commit hook reviews code diffs — no value for markdown/shell changes. `CORA_SKIP=1` does NOT bypass the hook.
8. **MCP server fallback.** If `mcp_cora_cora_review_diff` returns `Connection closed`, fall back to CLI: `cora review --staged --format pretty`. The CLI binary is always available if `cora` is installed.
9. **`cora index` needs committed files.** New files that are staged but uncommitted won't appear in `cora search_symbols` or `cora brain`. Run `cora index` AFTER committing new modules.
10. **Review BEFORE commit.** Use `cora review --staged` (pre-commit) to catch issues early. Fix all MAJOR findings, re-run to verify, then commit with `--no-verify`.
11. **Pre-commit hook timeout in OTHER repos:** The cora hook runs `cora review --staged` which makes an LLM API call. On repos with large diffs, this exceeds 30s and gets killed (exit 130). Review manually with `cora review --staged` first, fix findings, then commit with `--no-verify`.
12. **`.unwrap()` in `#[cfg(test)]` is acceptable.** Cora flags these as minor `bug-unwrap` warnings. Rust test idiom uses `.unwrap()` freely. Don't waste cycles converting to `.expect()` — only fix `.unwrap()` in production code.

## Top Pitfalls

1. **Per-repo `.cora.yaml` overrides global config silently** — check `cat .cora.yaml` when auth issues arise
2. **`cora auth status` reports success with stale/revoked keys** — verify with real `cora review --base develop`
3. **API key source:** `~/.cora/auth.toml` (single key) or env vars: `CORA_PROVIDER`, `CORA_MODEL`, `CORA_BASE_URL`, `CORA_API_KEY`
4. **`--base branch` compares branches, not working tree** — use `--unstaged` for uncommitted changes
5. **`cora scan` sends full file content to LLM** — large files (>30KB) cause 502. Use `--batch-files 3` or prefer `cora review` (diff-based)
6. **GLM models may return invalid severity** — `"severity": "performance"` is not a valid variant. Batch skipped, non-blocking
7. **`.cora/` should be gitignored** — contains review history, not config
8. **Model quality varies** — test your model choice; some produce excessive false positives on the same code
9. **Installed binary may be stale** — after `cargo build`, check `cora --version`. If outdated, reinstall with `cargo install --path .`
10. **`.cora.yaml` v2 `ignore` requires struct** — `ignore: { files: [...], rules: [] }`. v1 list format causes silent parse error
11. **`gh pr checks --watch` timeout** — use `timeout=300` for Rust projects (CI takes 2-3 min)
12. **`gh pr checks` exit code 8** means checks still pending, NOT failure
13. **`cora trace` has no `--limit` flag** — use `--depth` only
14. **`cora brain` output paths are relative to repo root** — not absolute
15. **Static token 256d is NOT configurable** — changing dims means changing the hash algorithm
16. **`release.yml` `verify-main` guard blocks tags from develop** — tags MUST be on commits reachable from `main`. `develop → PR → main → tag`.

## `.cora.yaml` Config

See `references/cora-yaml-config.md` for full field reference and pitfalls.

## CI Setup

See `references/ci-setup.md` for workflow templates, org secrets, and CI pitfalls.

## Intelligence Loop — Integration Pattern

**Formula:** Index → Recall → Impact → Code → Verify

A 5-phase workflow for using Cora intelligence in every coding task.

### Integration Patterns

| Pattern | Flow | Use Case |
|---------|------|----------|
| A: New Feature | INDEX → RECALL(domain) → CODE → check_snippet → review → INDEX | Greenfield development |
| B: Bug Fix | INDEX → RECALL(symptom) → IMPACT(symbol) → CODE → affected_tests → VERIFY | Fix existing bugs |
| C: Refactoring | INDEX → IMPACT(target) → CALLERS → batch-update → CODE → VERIFY | Safe refactors |
| D: Code Review | REVIEW_DIFF → CHECK_SNIPPET(flagged) → DEBT(report) → approve | Agent-assisted review |
| E: Exploration | INDEX → ARCH → BRAIN(concept) → TRACE(symbol) | Onboarding, codebase understanding |

### Intelligence Loop Agent Rules

1. **Check index status first** — if symbols = 0, run `cora index`
2. **Recall before every edit** — `brain_search` catches duplicate patterns
3. **Impact-check before every modify** — `find_callers` + `find_impact` prevent cascading breakage
4. **Prefer MCP tools over terminal** — `mcp_cora_*` are native, no spawn overhead
5. **Use `check_snippet` for quick validation** — deterministic, no LLM cost
6. **Use `review_diff` for quality assurance** — full LLM pipeline, use after implementation
7. **Re-index after significant changes** — new symbols won't appear until indexed
8. **Respect quality gates** — if `get_quality_gate` shows failing thresholds, fix before proceeding

### Intelligence Loop Key Pitfalls

- **MCP tools not available** — agent must restart after adding MCP server config
- **`brain_search` requires index** — returns empty if `cora index` never run
- **`review_diff` has API cost** — use `check_snippet` for free deterministic checks
- **Regex-only languages** (Dart, PHP) — `find_callers` returns empty (no call edges)
- **Static token embedding** — 256d hash-based, good for exact patterns, less for conceptual queries

## Performance

| Metric | Value |
|--------|-------|
| Brain search (warm) | 37ms |
| Brain search (cold) | 52ms |
| Hash embed per vector | 0.7μs |
| Full rebuild (1.7K sym) | 5.3s |
| usearch KNN (bottleneck) | ~25ms (68% of search time) |

50 queries/session ≈ 1.8s total search overhead.

## Memory Integration (`--memory` / `--learn`) — HIDDEN

**Status: Hidden from user-facing docs.** Code still compiles and works, but undocumented. Do NOT mention to users.

| Flag | What it does | Code |
|------|-------------|------|
| `--memory` | Recall past patterns before review | `engine/memory.rs:recall_context()` |
| `--learn` | Save issue stats after review | `engine/memory.rs:save_findings()` |

**Why hidden:** `save_findings()` saves only stats/category names, NOT finding text. Un-hide only after `save_findings()` stores real finding content.

## Embedding Architecture

| Layer | Model | Dims | Status |
|-------|-------|------|--------|
| **Static tokens** | Hashing trick (`tokens.rs`) | 256d | Current (Phase 3) |
| **Voyage MRL** | Voyage-4-Nano ONNX | 256d | Planned (Phase 5) — same dims, swap embed fn |
| **Voyage MRL 512** | Voyage-4-Nano ONNX | 512d | Future opt — needs separate index file |

**Key:** Voyage Matryoshka 256d enables Phase 5 migration without changing usearch dims, schema, or index infra.

## Naming Convention

- Project: **cora-code** (crate/repo name)
- Binary: **cora** (user-facing)
- NEVER refer to it as `cora-cli` in new docs/code

## Versioning

- Stay in 0.x.x indefinitely (minor per feature batch, patch per fix)
- Bump version on every merge to develop


---

# Development Guide

> This section covers cora-code development internals — architecture, implementation phases, Brain Mode roadmap, embedding strategy, and CI pitfalls.

## Repository

- **Repo:** https://github.com/codecoradev/cora-code (renamed from `cora-cli`, Jul 2026)
- **Default branch:** `develop` (PR-only, no direct push)
- **Binary name:** `cora`
- **Crate name:** `cora-code`
- **CI:** GitHub Actions
- **Data directory:** `~/.codecora/cora-code/`

## CodeCora Data Directory Standard

All CodeCora Rust CLI products use `~/.codecora/{product}/` for local runtime data.

## Architecture Overview

```
cora-code (cora binary)
├── commands/       # CLI subcommands (review, scan, debt, commit, hook, etc.)
├── data_dir.rs    # Global data dir (~/.codecora/cora-code/)
├── engine/
│   ├── memory.rs   # Memory integration (hidden, --memory flag)
│   └── ...         # LLM engine, diff processing
├── index/           # Code intelligence (global DB with project_id FK)
│   ├── ast.rs      # Tree-sitter AST extraction (feature-gated, 12+ langs)
│   ├── brain.rs    # Brain Mode: hybrid search + index-time embedding (Phase 3)
│   ├── extract.rs  # Symbol extraction (tree-sitter primary, regex fallback)
│   ├── graph.rs    # Call graph + trace + arch (project-scoped queries)
│   ├── schema.rs   # SQLite schema v4: projects + edges table + embedding metadata
│   ├── symbols.rs  # Symbol types (project-scoped FTS5 search)
│   └── vector.rs   # CodeVectorIndex: usearch HNSW wrapper (Phase 3)
├── mcp/            # MCP server
├── git/            # Git operations
└── providers/      # LLM provider abstraction
```

## Dependencies (Cargo.toml)

Key deps: `clap`, `tokio`, `reqwest`, `git2` (vendored), `rusqlite` (bundled), `serde`, `anyhow`.
Binary target: `name = "cora"`, `path = "src/main.rs"`.

## Code Intelligence — Current State

- Symbol extraction via tree-sitter (primary, 12 langs + JS via TS) + regex fallback (18 langs total)
- Schema v4: `edges` table + embedding metadata on `projects` (tier, dims, model, last_embedded_at)
- Call graph via `graph.rs` (legacy `call_graph` table preserved, `edges` is superset)
- FTS5 search in SQLite
- Brain Mode: usearch HNSW vector index + RRF hybrid search (FTS5 + vector KNN + graph BFS)
- Memory integration via `engine/memory.rs` (hidden from docs, --memory flag)

## Brain Mode — Roadmap (v0.7+)

Project-scoped code context with embedding-powered semantic search.
See `references/brain-mode-architecture.md` for full design.

### Embedding Strategy (Tiered)

| Tier | Source | Size | Speed | Quality | Dependencies |
|------|--------|------|-------|---------|-------------|
| **0: Static** | nomic-embed-code token extraction (vendored) | ~30MB | ~0.1ms | Good (bag-of-tokens from 7B model) | None |
| **1: Local ONNX** | Voyage-4-Nano ONNX (opt-in, MRL 256d) | ~1.41GB | ~100-500ms | Best (full contextual, 32K ctx) | `ort` crate |
| **2: FastEmbed** | fastembed-rs (Jina Code, BGE, etc.) | Varies | Moderate | Good | `fastembed` crate |
| **3: API** | OpenAI, Voyage API (opt-in) | N/A | Network | Best | API key |

### Key Architecture Decisions

1. **Static token embeddings** (CBM approach): Vendored pre-built vectors from CBM repo (DeusData/codebase-memory-mcp, Apache-2.0). ~30MB int8 blob (40,856 tokens × 768 dims). Runtime = bag-of-tokens lookup (zero ONNX dep). See §Embedding Implementation for details.
2. **Voyage-4-Nano ONNX**: 340M params, Qwen3 architecture, 32K context, full 2048d (Matryoshka: 256/512/1024/2048). **Phase 5 target: MRL 256d truncate** — matches current static token dims, reuses 1 usearch index. See `references/embedding-dimension-strategy.md` D2.
3. **External memory stays generic** — cora-code bundles its own code embeddings; external memory keeps their own embeddings for general knowledge.
4. **Tree-sitter** needed for proper AST extraction (upgrade from regex-based `index/extract.rs`).

### Implementation Phases

See `references/brain-mode-architecture.md` §4 for details.

| Phase | Scope | Status |
|-------|-------|--------|
| **0** | Rename `cora-cli` → `cora-code` | ✅ Done |
| **1** | Static token embedding (30MB, zero deps, dual-backend) | ✅ Done |
| **2A** | Tree-sitter AST extraction (12 langs + JS grammar, feature-flagged) | ✅ Done |
| **2B** | Knowledge graph + schema v3 (edges table) | ✅ Done |
| **2C** | `cora trace` + `cora arch` subcommands | ✅ Done |
| **3** | Brain Mode hybrid search (usearch + RRF + static tokens) | ✅ Done |
| **4** | External memory cross-project integration (HTTP API only) | Planned — architecture decided |
| **5** | Voyage-4-Nano ONNX | Deferred — low ROI until user feedback |

### Phase 3: Brain Mode Hybrid Search

- **Vector storage: usearch** (HNSW, industry-standard). Separate `.usearch` + `.keys` files at `~/.codecora/cora-code/`.
- **`CodeVectorIndex`** in `src/index/vector.rs` — maps usearch u64 key↔symbol i64 ID. File locking via `fs2`. Auto-reserve capacity on insert.
- **Hybrid scoring: RRF** (Reciprocal Rank Fusion, k=60). Three signal sources: FTS5 keyword + usearch vector KNN (top 50) + graph BFS depth-2 from top-5 FTS hits.
- **Embedding timing: index-time**. `embed_project()` called after `index_project()`. Embeds symbol bodies via static tokens (256d), stores in usearch. Schema v4 tracks `last_embedded_at` on projects table.
- **Static token dimensions: 256** (NOT 768). The hashing trick in `tokens.rs` produces 256-dim vectors.
- **Dependencies added:** `usearch = "2"`, `fs2 = "0.4"`.
- **Schema v4:** `ALTER TABLE projects ADD (embedding_tier TEXT DEFAULT 'static', embedding_dims INTEGER DEFAULT 256, embedding_model TEXT DEFAULT 'static-tokens', last_embedded_at TEXT)`.
- **`cora brain <query>`** — CLI with `--json` and `--limit` flags. 3-signal RRF fusion, results show provenance (fts/vector/graph).
- **MCP tool `cora.brain_search`** — tool count now 15.

### Phase 4: External Memory Integration (architecture decided)

- **Integration method: HTTP API only** (external memory service endpoint). NOT SQLite ATTACH for vectors — ATTACH cannot access usearch index files (separate C library, not SQLite tables).
- **`cora brain --learn`** → push review findings/patterns to external memory, tagged `[cora-code, code-pattern, <category>]`.
- **Cross-project recall** — optional external memory enrichment in `cora brain`: local usearch results + HTTP `/search` results. Graceful degradation if service unavailable.
- **`.cora/graph.db.zst` export** — compress graph.db + cora_index.usearch for team sharing (inspired by CBM).
- **Estimated effort:** ~590 lines.

### Phase 5: Voyage-4-Nano ONNX (DEFERRED)

- **Status:** Deferred until user feedback indicates static tokens insufficient.
- **Reasoning:** Static tokens (Phase 3 default) cover ~80% of retrieval quality. +15-25% uplift from contextual embedding not worth 1.5-2GB RAM, ~6min index time (vs 0.2s), ONNX complexity.
- **If built:** `ort` crate + model download (fastembed pattern). **Voyage MRL 256d (Matryoshka truncate)** — same dims as current static tokens, so 1 usearch index file is reused. Swap `embed_code()` return value from hash to Voyage prefix. No schema/infra change needed. See `references/embedding-dimension-strategy.md` for locked decision D2.
- **Trigger conditions:** User explicit request, or `cora review --brain` needs very precise semantic matching.

### Implemented Subcommands (Code Intelligence)

- `cora index` — parse project → build knowledge graph in `~/.codecora/cora-code/graph.db`
- `cora explore <query>` — FTS5 symbol search with kind/file/language filters
- `cora callers <symbol>` — who calls this (call_graph + edges)
- `cora impact <symbol>` — recursive reverse-traversal impact analysis
- `cora affected` — find tests affected by changed files
- `cora trace <symbol>` — BFS path tracing across edges (outgoing/incoming, depth-limited)
- `cora arch` — architecture overview (module stats, edge distribution)
- `cora brain <query>` — hybrid search: FTS5 + usearch vectors + graph proximity, RRF fused (Phase 3)

### Planned Subcommands (Phase 4+)
- `cora review --learn` — push review findings to external memory (Phase 4)
- `cora export --zstd` — compress graph.db + usearch for team sharing (Phase 4)

## Embedding Implementation (Phase 1)

### Architecture

```
tokenize_code(code) → HashMap<String, u32>
  ├─→ embed() → TokenEmbedding (256-dim, hashing trick, fast)
  └─→ embed_pretrained() → PretrainedEmbedding (768-dim, real vectors)
```

Dual-backend in `src/embed/`:
- **`tokens.rs`** — Hashing trick: zero-dep, 256-dim, FNV-1a pseudo-random projections. Good for dedup.
- **`token_vocab.rs`** — Pre-trained nomic-embed-code: 768-dim real vectors vendored as 30MB int8 blob (`vendored/nomic/code_vectors.bin`).
- **`mod.rs`** — Module root. `#![allow(dead_code)]` until Phase 3 wires commands.

### Binary Format (code_vectors.bin)

```
[u32 LE: token_count=40856] [u32 LE: dim=768] + count×dim int8 values
```

Int8 values are unit-normalized floats × 127. Vocab in `code_tokens.txt` (one per line). Source: CBM repo (DeusData/codebase-memory-mcp), Apache-2.0.

### Tokenizer Features

Handles camelCase/snake_case/acronym splitting for vocab coverage:
- `calculateHash` → `[calculate, hash]`
- `hello_world` → `[hello, world]`
- `HTTPServer` → `[HTTP, Server]`
- Multi-char operators as single tokens (`->`, `::`, `+=`)
- Stop punctuation filtered, numbers normalized (`<FLOAT>`, `<NUM>`)

## CI / Development Pitfalls

- `#![allow(dead_code)]` inner attribute works in module files (must be before `pub mod` lines but can be after doc comments)
- Use `sort_by_key(|b| std::cmp::Reverse(b.1))` not `sort_by(|a, b| b.1.cmp(&a.1))`
- Use `(-1.0..=1.0).contains(&f)` not `f >= -1.0 && f <= 1.0`
- **Pre-commit hook timeout:** The global git hook runs `cora review --staged`. If the *installed* `cora` binary is outdated, the hook hangs/timeout. Use `git commit --no-verify` and rely on `cargo check + cargo test + cargo clippy` as validation. Rebuild+reinstall `cora` after merge to restore hook functionality.
- **Pre-commit hook for doc-only PRs:** `CORA_SKIP=1` env var does NOT bypass the cora pre-commit hook. For doc-only changes (README, docs/), always use `git commit --no-verify`.
- **Installed binary vs target/debug binary divergence:** After `cargo build`, the installed `cora` may be a different (older) version than `target/debug/cora`. Check both: `which cora && cora --version` vs `target/debug/cora --version`. After merge, always `cargo install --path .` to keep them in sync.
- **`cora index --stats` shows CURRENT PROJECT only:** The stats command displays symbol count for the project matching the current working directory. It does NOT show totals across all indexed projects.
- **Pre-commit hook + API key:** Hook also runs `cora scan` which needs an API key. Use `--no-verify` if not configured locally.
- **`gh pr checks --watch` timeout:** Defaults to 180s which is often insufficient — use `timeout=300` for Rust projects.
- **`std::env::set_var` is `unsafe` in Rust 2024 edition.** Wrap in `unsafe { }` in tests.
- **`schema` module visibility:** If `main.rs` needs to call `index::schema::*`, the `schema` module must be `pub mod schema`.
- **Tree-sitter 0.26 API changes:** `Node::descendants()` method does NOT exist. Use cursor-based DFS. Also, `row`/`column` fields are already `usize` — no `as usize` cast needed. See `references/tree-sitter-pitfalls.md`.
- **Tree-sitter grammar field names are unreliable:** Use the field-name-first + kind-fallback pattern.
- **TypeScript grammar wraps exports in `export_statement`:** Extractor must recursively unwrap to find real declarations.
- **Workspace + crate dependency synchronization:** Add deps in BOTH workspace root `[workspace.dependencies]` AND the specific crate's `Cargo.toml` as `dep = { workspace = true }`.
- **Clippy `-D warnings` + `cargo fmt`:** CI runs both. Always run both locally before pushing.
- **rusqlite `MappedRows` doesn't impl `Default`:** Use explicit `if let Ok(rows) = stmt.query_map(...) { ... }` pattern.
- **SQLite ATTACH cannot access usearch indices:** usearch stores vectors in a separate `.usearch` file managed by C++ HNSW library. For cross-product vector search, use external memory HTTP API.
- **Dual scanner false positive pattern (RESOLVED):** `security_scanner.rs` and `builtin.rs` now share the same `post_match_filter`. See `references/dual-scanner-false-positives.md`.
- **Static token embedding dimensions = 256, NOT 768:** Phase 3 uses ONLY `embed_code()` which calls `embed()` (256d).
- **Adding a new language to regex-based symbol extraction:** Touch ALL of these locations — missing any one causes partial breakage:
  1. Regex patterns — add `RE_<LANG>_*` statics
  2. `extract_symbols()` match arm — add `"<lang>" => extract_<lang>(...)`
  3. `extract_<lang>()` function — implement after last extractor
  4. Scope tracking — add to brace-counting block
  5. `detect_function_entry()` match arm
  6. `is_builtin()` filter — add language-specific keywords
  7. `src/engine/context/extraction.rs` — add to both context and definition extraction arms
  8. Tests — comprehensive + issue reproduction
  9. CHANGELOG.md

- **Adding a new language via "Strip & Delegate" pattern (Svelte-style, full-content):** For languages embedding another language:
  1. Regex patterns — content-level patterns
  2. `extract_symbols()` match arm — BEFORE `_ => {}`, signature differs (full content, not per-line)
  3. `extract_<lang>()` — strip inner language content, delegate to existing per-line extractor, dedup
  4. Scope tracking — do NOT add (runs before line loop)
  5. Tests + CHANGELOG

  **Critical pitfall:** If full-content extractor is called INSIDE the per-line loop, it processes full content on every line causing N× duplication. Move it BEFORE the loop or guard with a `once` flag.

- **Tree-sitter compatibility check before adding a language:** Verify grammar version compatibility, check alternative grammars (e.g., `tree-sitter-<lang>-ng`), verify grammar parses inner content.

### Post-Feature Documentation Workflow

After every feature batch merges to develop, update these docs in a single docs PR:
1. **CHANGELOG.md** — fill `[Unreleased]` section
2. **docs/cli-reference.md** — add new subcommands
3. **docs/roadmap.md** — update roadmap status
4. **AGENT.md** — update `src/` structure tree, test count, tool count
5. **README.md** — add top-level section for major capability areas
6. **New docs page** (if applicable) — create dedicated page for major features

### Release Workflow (Patch)

Standard pattern for patch releases:

1. **Bump version** — edit `Cargo.toml` `version` field
2. **Promote changelog** — rename `[Unreleased]` → `[X.Y.Z]` with date, add new `[Unreleased]`
3. **Commit, branch, push** — `chore/bump-v<N>` branch, create PR
4. **Wait for CI** — `gh pr checks <N> --watch` with `timeout=300`
5. **Merge** — `gh pr merge <N> --merge`
6. **Sync develop → main** — MUST be via PR to `main` (branch protection). Tag MUST be on a commit reachable from `main`.
7. **Tag** — `git tag -a v<N> -m "v<N> — summary"` then `git push origin v<N>`
8. **GitHub Release** — `gh release create v<N>` with comparison link

**CRITICAL: `release.yml` has a `verify-main` guard job** — it checks that the tag commit exists in `main` history.

### Tree-sitter Supported Languages

| Language | Grammar Crate | Key Nodes |
|----------|--------------|-----------|
| Rust | tree-sitter-rust 0.23 | fn, impl, trait, struct, enum, const, type alias |
| Go | tree-sitter-go 0.23 | func, method, type/interface, const, var, imports |
| Python | tree-sitter-python 0.23 | class, function, async def, import, nested classes |
| TypeScript/TSX | tree-sitter-typescript 0.23 | export wrapper, interface, class, function, const, type |
| JavaScript | tree-sitter-javascript 0.25 | (routes through JS grammar, subset of TS extraction) |
| Svelte | (delegates to TS) | Component name from filename + TS symbols |
| Dart | tree-sitter-dart 0.23 | class, mixin, extension, enum, function, constructor |
| Java | tree-sitter-java 0.23 | class, interface, method, enum, field, import |
| C | tree-sitter-c 0.24 | function, struct, enum, typedef, preproc include |
| C++ | tree-sitter-cpp 0.23 | extends C: class, namespace, template, inheritance |
| C# | tree-sitter-c-sharp 0.23 | class, struct, record, interface, namespace, using |
| Ruby | tree-sitter-ruby 0.23 | module, class, method, require |
| PHP | tree-sitter-php 0.24 | class, interface, trait, function, namespace, use |
| Scala | tree-sitter-scala 3 | class, object, trait, function, enum, import |

**JS note:** JavaScript files (`.js`, `.mjs`, `.cjs`) route through the TypeScript grammar extractor.

**Data storage:** Global index at `~/.codecora/cora-code/graph.db` (all projects keyed by `project_id` FK). NOT project-local `.cora/`. Single SQLite file, WAL mode.

**Cross-project search:** All indexed repos share one `graph.db` + one `cora_index.usearch`. Regex fallback languages (Dart, PHP, Svelte) index symbols but do NOT produce call edges — `cora callers`/`cora impact` return empty for regex-only languages.

**Tree-sitter implementation:** `src/index/ast.rs` provides AST-based symbol and edge extraction, gated behind `#[cfg(feature = "tree-sitter")]`. Feature flag in Cargo.toml. Default build has zero tree-sitter code. Grammar crates are statically linked. Edge types: Calls, Imports, Implements, Inherits, ChildOf. `extract_symbols()` and `extract_calls()` in `extract.rs` try tree-sitter first, fall back to regex. See `references/tree-sitter-pitfalls.md` for critical API gotchas.

**Adding a new tree-sitter language:** 1) Add grammar crate to Cargo.toml as optional dep + feature list. 2) Add `Language::*` variant in `get_language()`. 3) Add match arm in `extract()` dispatcher. 4) Add `extract_<lang>()` function. 5) Update tests. 6) Run `cargo fmt`.

**Schema v3:** `edges` table with `(source, kind, target, file, line, project_id)`. Edge kinds: CALLS, IMPORTS, IMPLEMENTS, INHERITS, CHILD_OF.

**`cora trace` and `cora arch`:** BFS path tracing with `--direction outgoing|incoming` and `--depth N`. Architecture overview: modules by symbol count, edge type distribution. Both support `--json`.

**Cross-product integration:** Separate DBs + external memory HTTP API for cross-query. ATTACH only works for SQLite tables — cannot access usearch index files. Phase 4 uses HTTP API exclusively. Each product owns its own DB; cora-code works independently (critical for CI).

## Related CodeCora Products

| Product | Repo | Crate | Binary | Notes |
|---------|------|-------|--------|-------|
| cora-code | `codecoradev/cora-code` | `cora-code` | `cora` | Code intelligence CLI |
| covecto | `codecoradev/covecto` | `covecto` | `covecto` | Image vectorizer CLI |

## References

| File | Content |
|------|--------|
| [ci-setup](references/ci-setup.md) | CI workflow template, org secrets, failure detection |
| [ci-setup-and-pitfalls](references/ci-setup-and-pitfalls.md) | CI patterns and pitfalls |
| [cora-ci-patterns](references/cora-ci-patterns.md) | CI workflow patterns |
| [cora-yaml-config](references/cora-yaml-config.md) | `.cora.yaml` field reference + pitfalls |
| [brain-mode-architecture](references/brain-mode-architecture.md) | Brain Mode design, embedding model comparison |
| [embedding-dimension-strategy](references/embedding-dimension-strategy.md) | 256d static + Voyage MRL + cross-system dim analysis |
| [brain-mode-phase3-4-decisions](references/brain-mode-phase3-4-decisions.md) | Phase 3/4 locked decisions |
| [phase1-implementation](references/phase1-implementation.md) | Phase 1 implementation notes |
| [cross-product-integration](references/cross-product-integration.md) | Separate DBs + cross-product integration pattern |
| [tree-sitter-pitfalls](references/tree-sitter-pitfalls.md) | tree-sitter 0.26 API gotchas |
| [dual-scanner-false-positives](references/dual-scanner-false-positives.md) | Dual scanner false positive analysis |
