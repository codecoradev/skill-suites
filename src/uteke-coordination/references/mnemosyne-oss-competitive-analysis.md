# Mnemosyne-OSS (BEAM) Competitive Analysis

**Date:** Jul 20, 2026  
**Repo:** https://github.com/mnemosyne-oss/mnemosyne  
**By:** AxDSan (Abdias J) — MIT License  
**Stack:** Python 99.3%, 1.6K stars, 147 forks, 874 commits, 43 releases

## BEAM Architecture (Bilevel Episodic-Associative Memory)

1. **Working Memory** — Hot context, auto-injected before LLM calls, TTL-based eviction, session-scoped
2. **Episodic Memory** — Long-term storage with sqlite-vec + FTS5 hybrid search
3. **Scratchpad** — Temporary agent reasoning workspace (cleared per session)
4. **TripleStore (KG)** — Temporal knowledge graph with version chains (SPO, valid_from, valid_until)
5. **MEMORIA (v3.0+)** — Structured extraction: facts, timelines, kg, instructions, preferences tables

### Scoring Formula
50% vector similarity + 30% FTS5 rank + 20% importance

### Binary Vectors: MIB (Information-theoretic binarization)
Compresses 384-dim float32 → 48 bytes (32x reduction). Hamming distance entirely within SQLite. No ANN indices needed.

## Published Benchmarks

| Benchmark | Score | Notes |
|-----------|-------|-------|
| LongMemEval (ICLR 2025) | **98.9% Recall@All@5** | bge-small-en-v1.5, 100 instances — top score |
| BEAM-100K end-to-end QA | **65.2%** | Top score, beats Honcho 63.0%, Hindsight 73.4% |
| BEAM retrieval @ 10M | 20% Recall@10 | 35ms latency, 7.2MB storage |

### Latency (CPU, sqlite-vec + FTS5, no GPU)
Write: 0.81ms | Read: 0.076ms | Search: 1.2ms | Cold Start: 0ms

## Integration Matrix (8+ platforms)

| Platform | Method | Setup |
|----------|--------|-------|
| Hermes Agent | Native plugin (23 tools!) | Ships enabled |
| Claude Code | MCP | `.claude/mcp.json` |
| Cursor | MCP | `.cursor/mcp.json` |
| OpenAI Codex CLI | MCP | `.codex/mcp.json` |
| OpenWebUI | Native @tool | Drop bridge file |
| Pi | Extension + skill | `pi install npm:@mnemosyne-oss/pi-mnemosyne` |
| Windsurf | MCP | `.windsurf/mcp_config.json` |
| OpenClaw | Native provider | `pip install mnemosyne-memory[openclaw]` |

## Mnemosyne Sync

Bidirectional delta sync between desktop and VPS. Optional client-side encryption (XChaCha20-Poly1305). Key never leaves machine. Append-only event log.

## Feature Comparison: Mnemosyne-OSS vs Uteke

| Feature | Mnemosyne-OSS | Uteke | Advantage |
|---------|:---:|:---:|---|
| **Stars** | 1.6K | ~117 | Mnemosyne |
| **Language** | Python | Rust | Uteke (perf) |
| **Dependencies** | Python stdlib + ONNX | Zero (single binary) | Uteke (simplicity) |
| **Memory tiers** | BEAM 3-tier (WM + EP + Scratchpad) | Flat + rooms + working_set | Mnemosyne (structure) |
| **Vector engine** | MIB binary (48 bytes, Hamming) | usearch HNSW (768d float) | Trade-off (speed vs recall) |
| **KG** | TripleStore with temporal validity | memory_edges (basic cosine) | Mnemosyne |
| **Structured extraction** | MEMORIA (5 tables) | --type taxonomy (basic) | Mnemosyne |
| **Consolidation** | Sleep cycles (auto WM→EP) | Dream pipeline (7-phase) | Uteke (comprehensive) |
| **Sync** | DeltaSync + encryption | None | Mnemosyne |
| **Document engine** | None | Wiki/docs engine | Uteke (unique) |
| **Benchmarks** | LongMemEval + BEAM published | None | Mnemosyne |
| **Hermes tools** | 23 plugin tools | Limited plugin tools | Mnemosyne |
| **Website** | mnemosyne.site (live demo) | docs.uteke.dev (VitePress) | Mnemosyne |
| **Launch** | Product Hunt featured | No launch | Mnemosyne |
| **Auto-aging** | Importance decay | aging (configurable) | Parity |
| **Working memory** | TTL-based, auto-injected | working_set/working_get/working_clear (TTL 24h) | Parity |
| **Offline** | Yes | Yes | Parity |
| **Cost** | Free forever | Free forever | Parity |

## Key Differences Summary

**Where Mnemosyne-OSS wins:**
1. Published benchmarks (academic credibility)
2. 23 Hermes plugin tools (deep integration)
3. MIB binary vectors (extreme compression, Hamming distance)
4. TripleStore with temporal validity (SPO + valid_from/until)
5. MEMORIA structured extraction (5 tables)
6. DeltaSync with client-side encryption
7. Website with live demo + comparison table
8. 1.6K stars + Product Hunt launch

**Where Uteke wins:**
1. Rust performance (vs Python)
2. Document engine / wiki (Mnemosyne has none)
3. Dream pipeline 7-phase (more comprehensive than sleep consolidation)
4. usearch HNSW 768d float (potentially better recall at scale)
5. Zero binary dependencies (single Rust binary vs Python + ONNX runtime)
6. Rooms + Namespaces (more flexible than memory banks)

## Uteke Feature Mapping vs BEAM

| BEAM Component | Mnemosyne-OSS | Uteke Equivalent | Status |
|---|---|---|---|
| Working Memory | TTL, auto-injected, session | working_set/working_get/working_clear (TTL 24h) | ✅ EXISTS |
| Episodic Memory | sqlite-vec + FTS5 | remember/recall (usearch + FTS5) | ✅ EXISTS |
| Scratchpad | Temp reasoning workspace | Namespace isolation | ⚠️ PARTIAL |
| TripleStore | Temporal KG (SPO, validity) | memory_edges (basic cosine) | ⚠️ WEAKER |
| MEMORIA | 5 structured tables | --type taxonomy | ⚠️ WEAKER |
| Sleep Consolidation | Auto WM→EP summarization | Dream pipeline (7-phase) | ✅ EXISTS+ |
| Memory Banks | Per-domain isolation | Rooms + Namespaces | ✅ EXISTS |
| Aging/Decay | TTL + importance decay | uteke aging | ✅ EXISTS |
| Importance | importance scoring | importance scoring | ✅ EXISTS |
| Tags/Type | tags + type + namespace | tags + type + namespace | ✅ EXISTS |

## Marketing Positioning Notes

**Do NOT use "5-layer cognitive architecture" or "like a human brain" for marketing.**
- That claim belongs to 28naem-del/mnemosy.ai (91 stars, TS + Qdrant + Redis + FalkorDB) — a DIFFERENT product
- Mnemosyne-OSS does NOT use that term — they use "BEAM" (honest engineering naming)
- The neuroscience analogy is marketing language, not neuroscientific accuracy

**Valid differentiators for Uteke marketing:**
1. "Single binary, zero runtime deps" — Mnemosyne-OSS needs Python + ONNX
2. "Built-in document/wiki engine" — Mnemosyne-OSS has none
3. "7-phase dream pipeline" — more comprehensive consolidation
4. "Rust performance" — measurable, benchmarkable
5. "Room-based coordination" — multi-agent shared context

**Invalid differentiators (Mnemosyne-OSS has same):**
- ~~Zero external services~~ — both zero deps
- ~~Local-first~~ — both local-first
- ~~Free forever~~ — both free

## BEAM Feature Adoption Analysis for Uteke (Jul 2026)

### Priority 1 — Scratchpad
**Rekomendasi: JANGAN bikin table baru.** Uteke `working_set`/`working_get`/`working_clear` sudah setara BEAM Scratchpad (ephemeral, TTL 24h). Cukup add `scratchpad` sebagai semantic alias di API — agent tulis reasoning ke `working_set(key="scratchpad", value="...")`. Zero schema change.

### Priority 2 — Temporal TripleStore
**Rekomendasi: Upgrade `memory_edges`, bukan bikin baru.**
- `memory_edges` sudah punya `edge_type` (sebagai predicate) dan 481 edges aktif
- Tambah: `weight REAL` (confidence), `valid_from TEXT`, `valid_until TEXT`
- `memories` table sudah punya `valid_from` (5970 records) — temporal pattern sudah established
- Deprecate `graph_nodes` + `graph_edges` — kedua tabel KOSONG, redundant dengan `memories` + `memory_edges`
- Tambah query API: `query_edges(subject, predicate, object)` — alias untuk filter `memory_edges`

### Priority 2 — MEMORIA Structured Extraction
**Rekomendasi: JANGAN normalize ke 5 tables.** Uteke sudah punya MEMORIA setara via `memory_type` taxonomy.

| MEMORIA Table | Uteke `memory_type` | Status |
|---|---|---|
| `memoria_facts` | `fact` (5610 records) | ✅ Parity |
| `memoria_timelines` | `event` (127) + `timeline_events` (8759) | ✅ Parity+ |
| `memoria_kg` | `memory_edges` (SPO via source→edge_type→target) | ⚠️ Needs SPO query layer |
| `memoria_instructions` | `procedure` (58) | ✅ Parity |
| `memoria_preferences` | `preference` (70) | ✅ Parity |

**Trade-off: normalized 5 tables vs single `memories` table with `memory_type`:**
- Uteke: simpler schema, flexible types, single WHERE for cross-type queries
- BEAM: faster type-specific queries (smaller index), but rigid schema, cross-type needs JOIN

**Yang perlu:** Auto-extraction pipeline (extract structured data from content → appropriate `memory_type` + `metadata` JSON for structured fields). BEAM uses `extract=True` + regex + LLM fallback. Uteke needs similar pipeline but stores result in existing `memories` table.

### Priority 3 — Temporal Recall
**Rekomendasi:** `valid_from`/`valid_until` query support di `recall()` — point-in-time queries. `memories` table already has the columns.

### Priority 3 — Configurable Scoring
**Rekomendasi:** Make `vec_weight`, `fts_weight`, `importance_weight` configurable per-query. BEAM defaults: 50/30/20.

### Key Data Points (Uteke production, Jul 2026)
- Total memories: 5,977
- `memory_edges`: 481 (437 `similar_to`, 15 `referenced_by`, 15 `tagged_as`, 14 `possible_duplicate`)
- `graph_nodes`: 0 (EMPTY — candidate for deprecation)
- `graph_edges`: 0 (EMPTY — candidate for deprecation)
- `timeline_events`: 8,759 (all `created` type)
- Rooms: 52, Documents: 82
- `memory_type` distribution: fact(5610), event(127), preference(70), procedure(58), decision(54), insight(33), context(17), note(8)
