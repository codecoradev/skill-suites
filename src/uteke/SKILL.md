---
name: uteke
description: "Uteke offline semantic memory engine — open source product."
version: 0.10.0
metadata:
  hermes:
    tags: [uteke, memory, semantic-search, offline, rust, local-first]
    related_skills: [hybrid-memory, graphify]
---

# Uteke — Offline-First Semantic Memory Engine

**Open source product.** Repo: [codecoradev/uteke](https://github.com/codecoradev/uteke).

Persistent, searchable AI memory — offline, single Rust binary, ~30ms recall. No API keys, no Python. Runs natively or via Docker.

## Quick Reference

| Topic | Details |
|-------|---------|
| **Binary** | `uteke` (v0.10.0, installed from GitHub release). Set env: `UTEKE_BASE_URL` (default `http://localhost:8767`), `UTEKE_TOKEN`, `UTEKE_NAMESPACE`. Use `curl` to the server API when running uteke-serve in Docker. |
| **License** | Apache 2.0 |
| **Install** | `curl -sSL codecora.dev/install | sh` (one-liner, all platforms) |
| **Source** | [codecoradev/uteke](https://github.com/codecoradev/uteke) (Rust, develop=mainline, main=release mirror) |
| **Hermes** | Mode A (uteke-tool plugin, manual HTTP to uteke-serve) + Mode C (uteke-memory plugin: `pre_llm_call` hook auto-recall). Mode C plugin registers `ctx.register_hook("pre_llm_call", callback)` — in-process, no subprocess spawn, full contextvar access. See `extensions/hermes-memory-provider/` in uteke repo. |
| **Embedding** | EmbeddingGemma Q4 ONNX 768d, lazy-loaded, uses output[1] (sentence_embedding, mean-pooled), L2 normalized. HF: `onnx-community/embeddinggemma-300m-ONNX`. SHA256-verified download. Remote via OpenAI/Ollama (opt-in). See [`references/source-verified-internals.md`](references/source-verified-internals.md) |
| **Storage** | SQLite + usearch vector index at `~/.uteke/` |
| **Server** | Docker container `uteke-serve`. Auth: `Authorization: Bearer $UTEKE_TOKEN`. Env: `UTEKE_BASE_URL` (default `http://localhost:8767`), `UTEKE_TOKEN`, `UTEKE_NAMESPACE`. Schema v15. All operations via `curl` to your uteke-serve instance. Source-verified endpoint map in [`references/server_api.md`](references/server_api.md). DB schema audit with indexes, FTS5, and query patterns in [`references/db-schema-audit.md`](references/db-schema-audit.md). ⚠️ **Auto-aging and auto-dream DISABLED in production** — see config section below. |
| **Docker** | `ghcr.io/codecoradev/uteke:latest` |
| **Init** | `uteke init --agent <pi|claude|cursor|hermes> [--memory-provider]` — sets up agent integration (manual or auto recall). Pi: TS extension with `before_agent_start` hook. Claude/Cursor: enhanced rules + MCP config snippet. |
| **Upgrade** | `uteke upgrade` (v0.7.0+) — self-update to latest release with checksum verification. Pre-v0.7.0: manual download from GitHub Releases, extract 3 binaries (`uteke`, `uteke-serve`, `uteke-mcp`), replace in PATH. **Pitfall:** `curl -fsSL -L` for GitHub release assets (follow redirects). Extract to temp dir to avoid `tar: Cannot open: File exists`. |
| **Docs** | `uteke doc` — wiki/knowledge base layer (global, no namespace). `create`, `get`, `list`, `search`, `delete`, `export`. Slug-based (globally unique), hierarchical (parent/children, depth 10), `author` field for attribution. ⚠️ `doc create` buggy (v0.7.0) — broken in CLI AND HTTP API (`/doc/create` 500). Use direct SQLite insert. See pitfall #17. |
| **Unified Recall** | `uteke recall` searches both memories AND docs since v0.6.4. Results tagged `[doc]` or `[memory]`. Use `--type doc|memory|all` to filter. |

## Core Commands (quick)

```bash
uteke remember "Deploy v2.1 to staging" --tags deploy,staging --namespace myagent --type decision
uteke recall "when deploy?" --namespace myagent           # Unified: searches memories AND docs (v0.6.4+)
uteke recall "modal fleet" --type doc                 # Docs only
uteke recall "modal fleet" --type memory              # Memories only
uteke recall "query" --context --namespace myagent       # AI prompt injection format
uteke search "staging" --namespace myagent                 # FTS5 text search
uteke list --tag deploy --namespace myagent
uteke doc create my-slug --title "My Doc" --content "$(cat file.md)" --tags infra
uteke doc get my-slug                           # Read doc content
uteke doc list                                 # List all docs
uteke doc children parent-slug                  # List child docs
uteke doc search "modal fleet"                  # Search across all docs
uteke stats / uteke doctor / uteke verify / uteke repair
uteke feedback helpful <id>              # Boost trust score +0.05
uteke feedback unhelpful <id>            # Lower trust score -0.10
uteke dream --phases contradict          # Auto-contradiction scan (Dream Phase 4)
uteke dream --phases lint,backlinks,dedup,contradict,orphans,compact,verify  # Full 7-phase pipeline

# Partial memory update via PUT (v0.8.0) — no more forget+remember
curl -X PUT ${UTEKE_BASE_URL}/memory \
  -H "Authorization: Bearer $UTEKE_TOKEN" -H "Content-Type: application/json" \
  -d '{"id":"<uuid>","content":"updated text","tags":["new-tag"],"importance":0.8}'

# Trust scoring / feedback via HTTP
curl -X POST ${UTEKE_BASE_URL}/memory/feedback \
  -H "Authorization: Bearer $UTEKE_TOKEN" -H "Content-Type: application/json" \
  -d '{"id":"<uuid>","feedback":"helpful"}'

# Room↔Document linking (v0.8.0)
curl -X PUT ${UTEKE_BASE_URL}/room/document/add \
  -H "Authorization: Bearer $UTEKE_TOKEN" -H "Content-Type: application/json" \
  -d '{"room_id":"<room-id>","doc_slug":"<existing-doc-slug>"}'
curl -X POST ${UTEKE_BASE_URL}/room/document/list \
  -H "Authorization: Bearer $UTEKE_TOKEN" -H "Content-Type: application/json" \
  -d '{"room_id":"<room-id>"}'
curl -X DELETE ${UTEKE_BASE_URL}/room/document/remove \
  -H "Authorization: Bearer $UTEKE_TOKEN" -H "Content-Type: application/json" \
  -d '{"room_id":"<room-id>","doc_slug":"<doc-slug>"}'
```

⚠️ Always use `--namespace <agent>`, `--type <fact|decision|procedure|preference|context>`, `--detect-contradiction` when re-storing.

## ⚠️ Breaking Changes (v0.8.0)

### Recall Response Format Changed
`POST /recall` now returns `[{memory: {...}, score: N}]` (wrapped) instead of flat `[{id, content, score, ...}]`.

**Old (v0.7.x):**
```json
[{"id":"abc","content":"...","score":0.8,"namespace":"myagent"}]
```

**New (v0.8.0):**
```json
[{"memory":{"id":"abc","content":"...","namespace":"myagent"},"score":0.8}]
```

**`UnifiedSearchResult`** (when `search_type` is set) includes full memory detail fields (no secondary lookups needed): `result_type`, `content`, `memory_id`, `doc_slug`, `tags`, `metadata`, `memory_type`, `namespace`, `importance`, `pinned`, `access_count`, `created_at`, `updated_at`, `linked_doc_slugs`, `linked_memory_ids`.

**Impact:** Any code/hooks parsing recall responses MUST update to unwrap `item['memory']` instead of reading flat `item['content']`. This includes Hermes `uteke` plugin and shell hooks.

**`GET /memory?id=`** returns flat format (unchanged).

### Room Document Routes
Room↔document junction uses **separate routes** (not `POST /room/document` with action param):
- `PUT /room/document/add` → link doc to room (`{room_id, doc_slug}`)
- `POST /room/document/list` → list linked docs (`{room_id}`)
- `DELETE /room/document/remove` → unlink doc (`{room_id, doc_slug}`)
- `POST /room/summary-document` → generates room summary document (NOT a link/unlink endpoint)

**⚠️ `PUT /room/document/add` returns 400 with validation message** on error (room/doc not found). Handler catches `uteke_core::Error::Validation(_)` at `handlers.rs:1087`. Verified: invalid room_id → `{"error":"Validation error: Unknown room: ..."}`.

## Roadmap

**Theme:** Quality + remaining fixes.

See the [CHANGELOG](https://github.com/codecoradev/uteke/blob/main/CHANGELOG.md) for version details (onboard wizard, API versioning, configurable dream thresholds, community templates, deprecated filter fix, Windows OS error 33 fix, embedding download robustness).

**Open issues tracked in the [GitHub Issues](https://github.com/codecoradev/uteke/issues) page.**

## Linked Files

| File | Description |
|------|-------------|
| [`references/commands.md`](references/commands.md) | All CLI commands: core, rooms, graph, documents, timeline, MCP, maintenance, TODO tracking |
| [`references/server_api.md`](references/server_api.md) | HTTP API endpoints, performance benchmarks, remote embedding config, ENV vars, dual-DB architecture, upgrade procedure |
| [`references/pitfalls_full.md`](references/pitfalls_full.md) | Full pitfalls list: critical, schema, server, config, multi-repo, Rust, docs, general |
| [`references/cli-pitfalls.md`](references/cli-pitfalls.md) | Production-tested CLI patterns |
| [`references/cli-syntax-pitfalls.md`](references/cli-syntax-pitfalls.md) | CLI syntax gotchas (positional args, etc.) |
| [`references/architecture.md`](references/architecture.md) | Crate/module map, key file locations |
| [`references/fts5-hybrid-search.md`](references/fts5-hybrid-search.md) | FTS5 hybrid search design (RRF merge) |
| [`references/document-layer-architecture.md`](references/document-layer-architecture.md) | Document engine schema, CLI, API, roadmap |
| [`references/mcp-docker-deployment.md`](references/mcp-docker-deployment.md) | Docker deployment, UID mismatch fix |
| [`references/python-sync-patterns.md`](references/python-sync-patterns.md) | Python REST API patterns: batch sync, deduplication, frontmatter parser, truncation |

## Project-Scoped Memory (Tag-Based Isolation)

**Problem:** Agents use a static namespace but work across multiple projects. Memories from different projects mix — causing noise and irrelevant recall.

**Solution: Auto-tag every remember/recall with `project:<folder_name>` derived from cwd.**

No Uteke binary changes needed — `--tags` already supported in both `recall` and `remember`. Applies to ALL agents.

### Tag Architecture

```
Layer 1: AUTO-TAG from cwd
  Agent session starts in ~/projects/my-app/
  → tag: project:my-app

Layer 2: AGENT NAMESPACE (unchanged)
  namespace = myagent (agent identity — stays per-agent)

Layer 3: COMPOSITE SCOPE
  remember: uteke remember "..." --namespace myagent --tags project:my-app
  recall:   uteke recall "..." --namespace myagent --tags project:my-app
```

### Scope Rules

| cwd Pattern | Tag Behavior |
|-------------|-------------|
| `/projects/{project}/` or `/projects/{project}/sub/deep/path/` | `project:{project}` — walk up to git root or extract direct parent folder name |
| No cwd info available | Fallback to namespace only (backward compatible) |

## Key Pitfalls

0. ⚠️ **`uteke remember` stdin pipe does NOT read content — stores literal `-`.** `cat file | uteke remember -` silently stores `"-"` instead of reading stdin. **Root cause:** `content: String` is a bare positional arg in `cli.rs:49-51` — clap parses `-` literally. No stdin-reading logic exists in `commands/remember.rs`. Contrast with `doc create --file -` which has explicit stdin check (`doc.rs:28-35`). **Fix — Python subprocess (recommended for all content > 1 line):**
    ```python
    import subprocess
    with open("content.md") as f:
        content = f.read()
    subprocess.run([
        "uteke", "remember", "--namespace", "myagent",
        "--room", "disc:topic", "--author", "agent",
        "--type", "decision", "--tags", "round-1,agent",
        content  # positional arg, NOT stdin
    ], timeout=30)
    ```
    **Shell fallback for short content:** `uteke remember "$(cat /tmp/file.txt)" --tags x --room r --namespace myagent`. **No `uteke save` command exists** — it's always `uteke remember`.

0a. ⚠️ **`uteke recall --json` line numbers in content.** Reported: `"content": "1|[text]\n2|[more]"`. `uteke room recall --json` does NOT have this. **Code audit:** Neither `output.rs:print_json()` nor `Memory` serialization adds line numbers. The JSON path in `recall.rs:292-307` uses clean `serde_json::to_string`. The "N|" format likely originates from the **calling tool/consumer** (e.g., a file reader tool) rather than uteke itself. Verify by testing `uteke recall --json` directly in a terminal.

0b. ⚠️ **Vector index silently desyncs from SQLite.** Memories can exist in SQLite but have NO vector embedding — invisible to `uteke recall`. **Root cause (audited, exact locations):**
    - **Remember** (`operations.rs:223 remember_precomputed`): SQLite insert at line 267, vector insert at line 288, `index.save()` at line 289. If `save()` fails → warning logged, `Ok(())` returned → caller reports success but vector NOT on disk.
    - **Forget** (`operations.rs:790 forget`): SQLite delete at line 806, `index.remove()` at line 808 (warning-only on failure), `index.save()` at line 811 (warning-only → `Ok(())`). Vector orphan persists.
    - **No atomic transaction** wraps SQLite + vector index. No retry around embedding generation (`operations.rs:133-139`).
    **Diagnosis:** `uteke verify --namespace <ns>` → MISMATCH. **Fix:** `uteke repair --namespace <ns>` then `uteke doctor`.

0c. ⚠️ **`uteke room recall` default limit is 20 — silently truncates.** **Location:** `cli.rs:649` — `#[arg(long, default_value = "20")]` in `RoomCommands::Recall`. **Always pass `--limit 100`** for rooms exceeding 20 memories.

0d. ⚠️ **`author` field not exposed in `uteke room recall --json` output.** **Root cause:** `Memory` struct (`types.rs:10-69`) has **no `author` field**. Author lives in `room_memories` junction table (schema `store.rs:144-151`). The `recall_room` SQL (`memory/rooms.rs:277-327`) joins `room_memories` but only SELECTs from `memories` — `rm.author` not selected.

0e. ⚠️ **`uteke room create` hangs when uteke-serve holds the usearch file lock.** Room commands (`room create`, `room list`, `room recall`) need long-held access to `uteke_index.usearch`. When `uteke-serve` is running, it holds the lock via `fs2` advisory file locking → CLI blocks indefinitely (log: `usearch file lock busy, waiting...`). **This is lock contention, NOT a uteke bug.** `uteke remember` (without `--room`) works because it has a shorter lock hold pattern. **Workaround — direct SQLite insert for rooms:**
    ```python
    import sqlite3, datetime
    conn = sqlite3.connect("~/.uteke/uteke.db")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn.execute(
        "INSERT OR IGNORE INTO rooms (id, title, namespace, created_at, updated_at) VALUES (?,?,?,?,?)",
        ("my-room-id", "Room Title", "myagent", now, now))
    conn.commit(); conn.close()
    ```
    **For recall, use namespace+tag filter workaround:** `uteke recall "query" --namespace default --tags "my-tags" --limit 5` (different code path, less lock contention). **`rooms` schema:** `id TEXT PK`, `title TEXT` (NOT `name`), `namespace TEXT NOT NULL`, `created_at TEXT NOT NULL`, `updated_at TEXT NOT NULL`. **`room_memories` schema (5 columns):** `room_id TEXT`, `memory_id TEXT`, `author TEXT NOT NULL`, `role TEXT NOT NULL DEFAULT 'participant'`, `joined_at TEXT NOT NULL`. After creating the room via SQLite, link memories via `room_memories` junction table (the `--room` flag on `uteke remember` also silently fails — see pitfall #18a).

0f. ⚠️ **`uteke verify` and `uteke doctor` timeout (180s+) when uteke-serve holds the usearch file lock.** These commands need exclusive access to `uteke_index.usearch`. When uteke-serve is running, it holds the lock → CLI blocks indefinitely with log message `usearch file lock busy on ...uteke_index.usearch, waiting...`. **This also happens with LOCAL uteke processes (daemon, benchmarks) conflicting with the container uteke-serve.** Multiple uteke instances on different machines sharing the same DB volume → lock contention. **This affects ALL CLI commands** that open the store, not just verify/doctor. **Diagnosis:** Check logs at `~/.uteke/uteke.log.$(date +%Y-%m-%d)` for repeated "file lock busy" messages. Also check: `pgrep -fa uteke` — any local uteke-serve or benchmark process must be killed. **Fix — use HTTP API instead:** `curl -sf ${UTEKE_BASE_URL}/health` for status check (returns version, memory count, namespace count). For verify/repair, stop uteke-serve first, then run CLI commands.

1. ⚠️ First run downloads 188MB model (lazy-loaded). ⚠️ Always `--namespace`. ⚠️ Always `--type` + `--detect-contradiction`. After upgrade: `repair` → `doctor`. **Preferred diagnostic path when uteke-serve is running:** `curl -sf ${UTEKE_BASE_URL}/health` → returns `{"status":"ok","version":"...","memories":N,"namespaces":N}`. Use HTTP API instead of CLI when lock contention occurs (see pitfall #0f).
2. ⚠️ Two DBs may exist: HOME (`$HOME/.uteke`) for CLI, DATA (configured path) for MemoryProvider. Audit BOTH after changes.
3. ⚠️ `forget` = positional ID + `--confirm`. Room `--room` = positional for subcommands. `doc create` slug = positional. `doc delete` by ID only.
4. ⚠️ Uteke ≠ task orchestrator. Use a dedicated task manager for that.
5. ⚠️ `uteke.json` no `${ENV_VAR}` expansion. Don't set `namespace` there (global override).
6. ⚠️ REST API `POST /remember` does **not** accept `namespace` in the JSON body. Namespace is server-config-only. Use tags for filtering/isolation. See [`references/python-sync-patterns.md`](references/python-sync-patterns.md).
7. ⚠️ **`uteke import --extract` hangs when uteke-serve holds the usearch file lock.** uteke-serve uses `fs2` advisory file locking on `uteke_index.usearch`. CLI `uteke import` also needs exclusive lock → dead wait. **Fix:** stop uteke-serve first, run extraction, then restart. Or use `--store /tmp/path` for a temporary separate store. If uteke-serve was SIGKILL'd, the lock may go stale — no process holds the fd but the kernel-level flock persists. Only fix: delete the index file and let it rebuild.
8. ⚠️ **API gateway virtual key headers incompatible with uteke extraction.** uteke only sends `Authorization: Bearer $UTEKE_TOKEN` — cannot add custom headers. If your LLM gateway requires custom headers for remote embedding, configure a provider without that requirement or use a local proxy wrapper.
9. ⚠️ **Mutex lock + blocking outbound HTTP = DoS.** uteke-serve serializes ALL requests via `Mutex<Uteke>`. Any endpoint that makes outbound HTTP calls MUST release the lock before the HTTP call and re-acquire only for writes. Holding lock during a 30s worker timeout blocks every other endpoint. See pitfall #23 in [`references/pitfalls_full.md`](references/pitfalls_full.md).
11. ⚠️ **"Uteke dokumen" = `uteke doc`, NOT external wiki tools.** `uteke doc` CLI is a local-first document store at `~/.uteke/`. Use `uteke doc create <slug> --content "..."`.
12. ⚠️ **`uteke recall` is unified since v0.6.4 — searches memories AND docs.** Do NOT assume `uteke recall` only searches memories. Default `--type all` merges both stores via RRF. Results are tagged `[doc]` or `[memory]`. Use `--type doc` for docs-only, `--type memory` for memories-only. `uteke doc search` is separate (docs-only, hybrid FTS5+vector).
10. ⚠️ **Root documents with NULL `path` break `doc get` and `doc move --parent`.** `documents.path` column stores materialized paths. Root docs created before path population have `path=NULL` → `get_document_by_slug` fails with `Invalid column type Null at index: 12, name: path`. Fix: `UPDATE documents SET path = '/' || id || '/' WHERE path IS NULL AND depth = 0 AND parent_id IS NULL`. See pitfall #49 in [`references/pitfalls_full.md`](references/pitfalls_full.md).
13. ⚠️ **No doc-level prune/batch cleanup exists.** `uteke prune` only works on memories. Documents can only be deleted one-by-one (`uteke doc delete <id> --confirm`, cascades to children). There is no `doc prune`, `doc delete --tag`, `doc delete --all`, or batch endpoint. **Workaround:** `uteke doc export --json → filter IDs → loop delete`. See [`references/bulk-cleanup-surface.md`](references/bulk-cleanup-surface.md) for full gap map.
15. ⚠️ **CLI `doc list` is NEVER global — always scoped to namespace.** `resolve_namespace()` in `cli/main.rs:165` always returns a string (defaults to `"default"`), then `doc.rs:16` wraps it as `Some(ns.as_str())`. Server handles `ns(None)` correctly (returns all docs), but CLI never passes `None`. Result: `uteke doc list` without `--namespace` only shows docs in namespace `default`. To see all docs: `uteke doc list --namespace <ns>` for each. This is the **#1 cause of "docs disappeared"** reports.
16. ⚠️ **Documents are GLOBAL — namespace isolation removed (v0.6.7+).** Docs = shared wiki/knowledge base, not agent-isolated data. `namespace` column nullable on docs (deprecated), slug uniqueness is **global** (not per-namespace), `author` column added for attribution. All doc CLI/API/MCP operations ignore namespace. **Migration** handles existing duplicate slugs by renaming (e.g., `slug` → `slug-ns2`).
17. ⚠️ **`uteke doc create` bug (v0.7.0) — broken in BOTH CLI and HTTP API.** CLI: `--namespace` flag parsed by clap but NOT passed to INSERT → `NOT NULL constraint failed: documents.namespace`. HTTP API: `POST /doc/create` returns `500 Internal Server Error` (same root cause, even WITH auth token). Even `--namespace default` fails on CLI. **Workaround — direct SQLite insert via Python (use for BOTH CLI and API failures):**
    ```python
    import sqlite3, uuid, json, datetime
    conn = sqlite3.connect("~/.uteke/uteke.db")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    doc_id = str(uuid.uuid4())
    conn.execute("""INSERT OR REPLACE INTO documents 
        (id, slug, title, content, namespace, tags, metadata, version, content_type, created_at, updated_at, parent_id, depth, has_children, path)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        doc_id, "my-slug", "My Title", "content...", "myagent",
        json.dumps(["tag1", "tag2"]), json.dumps({"source": "agent"}), 1, "markdown",
        now, now, None, 0, 0, "/my-slug"))
    conn.commit(); conn.close()
    ```
    **Critical:** `path` column MUST NOT be NULL — `doc get` crashes with `Invalid column type Null`. Set `path` to `"/slug"` for root docs, `"/parent-slug/child-slug"` for children. `INSERT OR REPLACE` makes this pattern idempotent — safe to re-run. There are 15 columns and 15 `?` placeholders (the older version of this pitfall had only 14 — missing `content_type`).
    
    **For UPDATING existing docs** (partial find-and-replace within content, link fixes, tag updates): `POST /doc/update` with auth header works for simple full-content replacement, but for **in-place edits** direct SQLite UPDATE is most reliable:
    ```python
    conn = sqlite3.connect("~/.uteke/uteke.db")
    result = conn.execute("SELECT content FROM documents WHERE slug = 'target-slug'").fetchone()
    content = result[0]
    content = content.replace("old-link", "new-link")
    conn.execute("UPDATE documents SET content = ?, updated_at = ?, version = version + 1 WHERE slug = 'target-slug'",
                 (content, now))
    conn.commit()
    ```
    This bypasses both the broken CLI and HTTP API auth complexity. Always bump `version` on UPDATE.
18. ⚠️ **REST API auth tokens required for all write operations.** `UTEKE_TOKEN` env var must be passed as `Authorization: Bearer $UTEKE_TOKEN`. Without it: `500 Internal Server Error` on write endpoints. GET endpoints (`/health`, `/room/list`, `/doc/search`) work without auth. **When uteke-serve is running (port 8767), prefer REST API over CLI** — CLI hangs on usearch file lock (see pitfall #0f). For doc updates: `POST /doc/update` with `{"slug":"...", "content":"...", "tags":[...]}` + auth header works perfectly (unlike `/doc/create` which is still broken, see pitfall #17). Tags must be JSON array, not comma-separated string. See [`references/server_api.md`](references/server_api.md) for full API patterns.

18a. ⚠️ **`POST /remember` has NO `room` field — room linking SILENTLY FAILS (v0.7.3→v0.9.1).** FIXED in v0.10.0: `POST /room/remember` endpoint now exists. Use it directly. **Legacy (pre-v0.10.0):** `RememberRequest` struct (`types.rs:101-128`) had NO room/author fields. The `link_memory_to_room()` core function existed (`rooms.rs:277`) but had NO HTTP endpoint. Setting `metadata: {"room": "my-room"}` stored the string in metadata column but did NOT create a `room_memories` junction row. **Fix was:** (1) store memory via `/remember` API, (2) link via **direct SQLite INSERT** into `room_memories` junction table.

18b. ⚠️ **Hermes uteke-tool plugin endpoint mismatches (FIXED).** Plugin `tool.py` was sending to wrong endpoints across multiple actions. All fixed in recent versions. Key fixes included: `room_remember` & `room_document` routing to `/room/remember`, namespace list/stats routing, tags list/delete routing, consolidate/aging parameter formats, and `_request()` helper fixing `if data` → `if data is not None` (empty `{}` body was silently dropped because `{}` is falsy in Python). Plugin needs gateway reload to take effect.
    ```python
    import sqlite3, datetime
    conn = sqlite3.connect("~/.uteke/uteke.db")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn.execute(
        "INSERT OR IGNORE INTO room_memories (room_id, memory_id, author, role, joined_at) VALUES (?,?,?,?,?)",
        ("my-room", "<memory-id-from-post>", "agent", "author", now))
    conn.commit(); conn.close()
    ```
    **`room_memories` schema (5 columns, all NOT NULL except role):** `room_id TEXT, memory_id TEXT, author TEXT, role TEXT DEFAULT 'participant', joined_at TEXT`. `INSERT OR IGNORE` silently drops if any NOT NULL column is missing — always include `joined_at`.

### Batch Room Backfill Pattern

When backfilling historical data into Uteke rooms:
1. Query source DB (SQLite, etc.) for messages by date range
2. Group messages by topic (NOT per-message — that creates noise)
3. Classify each topic: `lead`, `support`, `discussion`, `feedback`, `partnership`, `daily-stats`
4. For each insight: `POST /remember` → get ID → `INSERT INTO room_memories` (two-step, pitfall #18a)
5. Tags: `daily-extract`, `{YYYY-MM-DD}`, `{category}`
6. After batch: run tag cleanup (normalize prefixes, case, aliases — subagents produce inconsistent formats)
7. Delete noise: content < 50 chars, bare URLs < 120 chars, ≤ 4 words for discussion

**Subagent delegation:** Split date ranges for parallel processing. Always include explicit instruction: "group related messages into one insight per topic, NOT one memory per message." Explicitly specify tag format: lowercase only, no prefixes, no colons after date.

**Room memory coverage audit:** When a room appears to have only 1 memory but should have many, the root cause is almost always agents using `uteke remember` (stores to namespace only) instead of `uteke room_remember` or `POST /room/remember` (stores AND links to room). The memory exists in the DB but has no `room_memories` junction row.

**For room memory migration (move memory between rooms):** See [`references/room-memory-migration.md`](references/room-memory-migration.md) for the complete clone → verify → delete old junction recipe.

14. ⚠️ **"Data hilang" troubleshooting checklist — run these before assuming data loss:**
    1. `uteke doctor` — check index consistency. Mismatch (DB≠Index) means `uteke repair` needed. Also catches DB corruption.
    2. `uteke doc list` — should show ALL docs globally (post-namespace-removal). If only shows 1 doc, may be on older binary: check per namespace with `--namespace <ns>`.
    3. `ps aux | grep uteke-serve` — zombie/defunct uteke-serve means clients can't connect to API at all → docs appear empty. Restart or kill orphan process.
    4. Direct DB check: `python3 -c "import sqlite3; c=sqlite3.connect('~/.uteke/uteke.db'); print(c.execute('SELECT namespace, count(*) FROM documents GROUP BY namespace').fetchall())"` — ground truth.
    5. **Check logs for delete:** `grep -i "doc.*delete" ~/.uteke/uteke.log.*` — zero matches = data was never deleted. It's a view/connection issue, not cleanup.

55a. ⚠️ **Hermes `uteke` tool plugin `room` parameter mismatch — room actions return empty/wrong results.** Plugin's room action handlers read `kwargs.get("room_id")` but the Hermes tool API passes the parameter as `room` (not `room_id`). Result: `room_id` is always empty string → API gets empty room_id → `room_recall` returns `"No memories found in room"`, `room_stats`/`room_summary` hit API errors. **Memory remember/recall works fine** (no room_id needed). **Root cause:** Parameter name mismatch between Hermes tool API naming (`room`) and plugin code expectation (`room_id`). **Fix:** Add `_get_room_id(kwargs)` helper that resolves both `room` and `room_id` keys. **Note:** Plugin needs gateway reload to take effect. For room writes, still use direct SQLite `room_memories` INSERT (pitfall #18a — `/remember` API has no room linking).

55b. ⚠️ **`POST /room/recall` API requires BOTH `room_id` AND `query` fields — `query` is mandatory.** Missing `room_id` → 400 "missing field `room_id`". Missing `query` → 400 "missing field `query`". The field name is `room_id` (not `room`). **Note:** `room_stats` works with just `room_id` (no `query` needed). For semantic room recall, always include a query term. Direct API: `curl -d '{"room_id":"my-room","query":"daily extract","limit":5}' ${UTEKE_BASE_URL}/room/recall`.

71. ⚠️ **Room HTTP routes have NO version prefix — do NOT guess, check `main.rs` route listing.** `/v1/rooms`, `/v2/rooms`, `/v1/room/create`, `/v2/room/create` all return 404. The actual room routes are unversioned: `POST /room/create`, `GET /room/list`, `POST /room/recall`, `POST /room/remember`, `POST /room/summary`, `POST /room/document`, `POST /room/stats`, `DELETE /room/delete`. **The JSON field for room ID is `room_id` (NOT `room`)** — `POST /room/create` requires `{"room_id": "..."}`, sending `{"room": "..."}` returns 400 "missing field `room_id`". Similarly, `POST /room/remember` requires `room_id` (not `room`). **Diagnosis:** grep routes from source: `grep -n '/room\|\.route' crates/uteke-server/src/main.rs` (or check the startup banner which lists all routes). **Only `/health` and `/recall` (with version prefix `/api/vN/recall`) are commonly used — all other routes may have unexpected shapes. Always verify with source before blind API calls.**

56. ⚠️ **Server API `/remember` metadata handling improved (v0.9.1).** `RememberRequest` now accepts `metadata`, `entity`, `category` fields (added v0.8.0). However, metadata with `{"room": "..."}` does NOT create room_memories junction — it's just a string in the metadata column. Room linking requires direct SQLite INSERT (pitfall #18a). **Fixed in v0.10.0** — `POST /room/remember` endpoint exists. Omit `tags` from `/remember` payload; use `/room/remember` for room-scoped memories.

57. ⚠️ **Server API Mutex serializes ALL requests (v0.7.3).** `uteke.lock()` at `main.rs:571-578` — single-threaded. Heavy operations (semantic search, room document) block ALL other endpoints including `/health`. Can cause cascading timeouts when multiple agents query simultaneously. Not fixable without code change (rwlock upgrade). **Workaround:** serialize requests from agents, add `--max-time 10` to all curl calls.

58. ⚠️ **`graph.rs::get_related()` has O(n) full table scan (v0.7.3).** Lines 153-165 call `self.store.load_all(None)?` to scan ALL memories for reverse metadata edges — degrades linearly with memory count. The indexed `memory_edges` table already handles forward edges efficiently. Fix: remove the legacy reverse metadata scan and rely solely on `memory_edges` (which has backlinks). See [`references/data-architecture-audit.md`](references/data-architecture-audit.md).

## Server API Verified Routes (v0.8.0, source-verified)

⚠️ Full endpoint map verified from `handlers.rs` source. See [`references/server_api.md`](references/server_api.md). Key additions in v0.8.0:

**New Endpoints:**
- **`PUT /memory`** — Partial update: content, tags, metadata, importance, pinned, memory_type. Returns `{updated: id}`.
- **`POST /memory/feedback`** — Trust scoring: `{id, feedback: "helpful"|"unhelpful"}`. Returns `{delta, importance}`. `helpful` = +0.05, `unhelpful` = -0.10.
- **`POST /memory/pin`** — Pin/unpin: `{id, pinned: bool}`.
- **`PUT /room/document/add`** — Link doc to room: `{room_id, doc_slug}`. Returns `{status, room_id, doc_slug}`.
- **`POST /room/document/list`** — List linked docs: `{room_id}`. Returns `{room_id, doc_slugs: []}`.
- **`DELETE /room/document/remove`** — Unlink doc: `{room_id, doc_slug}`. Returns `{status: "unlinked"}`.
- **`POST /doc/room/list`** — List rooms linked to doc: `{doc_slug}`. Returns `{doc_slug, room_ids: []}`.
- **`POST /doc/mem-refs`** — Memories referencing a doc via wikilinks: `{doc_slug}`.
- **`POST /memory/:id/doc-refs`** — Documents referenced by a memory's wikilinks.

**Breaking Changes:**
- `POST /recall` returns `[{memory: {...}, score: N}]` — NOT flat `[{id, content, score}]`.
- `UnifiedSearchResult` (when `search_type` set) includes full detail: `result_type`, `memory_id`, `doc_slug`, `tags`, `metadata`, `memory_type`, `namespace`, `importance`, `pinned`, `access_count`, `created_at`, `updated_at`, `linked_doc_slugs`, `linked_memory_ids`.
- `GET /memory?id=` returns flat (unchanged).

### API Versioning

All routes support URL prefix versioning. Unversioned routes alias to latest (v2).

| Path Pattern | Version | Recall Format |
|-------------|---------|---------------|
| `/recall` | latest (v2) | Wrapped: `[{memory: {...}, score}]` |
| `/api/v1/recall` | v1 | Flat: `[{id, content, score, ...}]` |
| `/api/v2/recall` | v2 | Wrapped: `[{memory: {...}, score}]` |
| `/health` | unversioned | Includes `api_versions`, `api_latest` |

All sub-routes (`/remember`, `/memory`, `/forget`, `/list`, `/search`, `/stats`, `/room/*`, `/doc/*`) follow the same pattern. **Health is always unversioned.**

### Tested Endpoints (v0.8.0)

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/memory` | `PUT` | ✅ | Partial update: content, tags, metadata, importance, pinned, memory_type. `{"updated":"<id>"}` |
| `/memory/feedback` | `POST` | ✅ | `{id, feedback: "helpful"|"unhelpful"}` → `{delta, importance}` |
| `/room/summary-document` | `POST` | ✅ | Generates room summary document (NOT link/unlink — use PUT/POST/DELETE routes below). |
| `/room/summary-document` (deprecated) | `POST` | ✅ | `POST /room/document` still works as deprecated alias with warn log |
| `/room/document/add` | `PUT` | ✅ | Link doc to room. Returns 400 on validation error (room/doc not found). |
| `/room/document/list` | `POST` | ✅ | `{room_id, doc_slugs: []}` |
| `/room/document/remove` | `DELETE` | ✅ | `{status: "unlinked"}` |
| `/doc/room/list` | `POST` | ✅ | List rooms linked to doc |
| `/doc/mem-refs` | `POST` | ✅ | Memories referencing doc via wikilinks |
| `/memory/:id/doc-refs` | `POST` | ✅ | Docs referenced by memory's wikilinks |

## Disk Cleanup

`~/.uteke/` accumulates stale files. Typical cleanup saves ~500-770 MB.

| File Pattern | Size (typical) | Safe to Delete? |
|---|---|---|
| `uteke.log.2026-MM-DD` (>3 days old) | ~50-130 MB each | ✅ Yes — rotated logs |
| `uteke_index.usearch.stale.*` | ~55 MB each | ✅ Yes — stale index snapshots |
| `uteke_index.usearch.bak*` | ~52-55 MB each | ✅ Yes — old index backups |
| `uteke.db.bak.*` | ~2-3 MB each | ⚡ Keep latest only |
| `memories.db` (0 bytes) | 0 | ✅ Artifact, delete |
| `uteke.toml.bak*` | 4 KB | ⚡ Low priority |

**Cleanup commands:**
```bash
# Delete old logs (>3 days)
find ~/.uteke/ -name "uteke.log.*" -mtime +3 -delete
# Delete stale index files
rm -f ~/.uteke/uteke_index.usearch.stale.* ~/.uteke/uteke_index.usearch.bak*
# Delete empty artifact
rm -f ~/.uteke/memories.db
```

**⚠️ NEVER delete while uteke-serve is running** — stop serve first to avoid lock issues.

## Production Config (Safe Defaults)

⚠️ **Auto-aging and auto-dream MUST be DISABLED in production.** The dedup/dream pipeline can be aggressive — it may delete or merge memories unexpectedly. Only run `uteke dream` manually when needed.

```toml
# ~/.uteke/uteke.toml — safe production defaults
[aging]
enabled = false

[maintenance]
auto_aging_enabled = false          # Opt-in
auto_aging_interval_hours = 24      # Daily
auto_dream_enabled = true
auto_dream_interval_days = 7        # Weekly

# Dream pipeline thresholds
[dream]
contradict_similarity_threshold = 0.6   # Cosine > this → NOT contradiction
contradict_tag_jaccard_min = 0.4       # Tag overlap ≥ this
contradict_max_memories = 200          # O(n²) scan limit
dedup_threshold = 0.92                # Cosine > this → merge candidate
orphan_importance_threshold = 0.15    # Below this → orphan

# Optional: Jaccard token reranking (v0.8.0)
[recall]
jaccard_weight = 0.0  # default; increase (0.0-1.0) for keyword-heavy queries
```

**Salience/recency boosts** default to 0.1 in v0.8.0 — no configuration needed, always active.

## Docs Maintenance

VitePress docs live in the `docs/` directory of the uteke repo. Key files:

| File | Content |
|------|---------|
| `docs/cli-reference.md` | All CLI commands, HTTP endpoints table, config limits |
| `docs/install.md` | Installation methods (curl, cargo, binary, Docker) |
| `docs/comparison.md` | uteke vs Mem0/Letta/Cognee feature comparison table |
| `docs/shell-hooks.md` | cd-based project memory auto-activation (bash/zsh/fish) |
| `docs/rooms.md`, `docs/smart-decay.md`, `docs/time-travel.md`, `docs/relationship-graph.md` | Feature docs |
| `docs/mcp.md` | MCP server setup, tool table (27 tools), JSON-RPC compliance |
| `docs/docker.md` | Docker setup, image tags, MCP tools in Docker |
| `docs/architecture.md` | System design, schema versioning (currently v15), data flow |
| `docs/integrations/hermes.md` | Hermes Mode A/B/C integration, memory-provider for pi/claude/cursor. |

⚠️ **hermes.md location:** The file is at `docs/integrations/hermes.md`, NOT `docs/hermes.md`. The integrations subdirectory is not obvious from issue specs that reference "docs/hermes.md".

When fixing documentation gaps from a GitHub issue spec:
1. **Read all target files first** before editing — files referenced in issues may have moved or been renamed
2. **Verify actual file paths** with `search_files` before patching — issue specs sometimes use shorthand paths
3. **Count actual tools/endpoints** when the issue says "update to N" — count from the source of truth (the code or the current table), not from the issue's claim
4. **Update both VitePress docs AND skill references** — when docs change, check if `references/server_api.md` in this skill also needs the same updates to stay in sync

60. ⚠️ **`uteke init --agent hermes --memory-provider` still active in Rust code.** `init_hermes_memory_provider()` in `crates/uteke-cli/src/init.rs:631` still installs the deprecated Mode B plugin and prints `memory.provider: uteke` config advice — even though the template was rewritten as a `pre_llm_call` Python plugin. **Impact:** Users who run this command get a broken setup. **Workaround:** Only run `uteke init --agent hermes` (without `--memory-provider`). The `__init__.py.tmpl` is now a pure `register(ctx)` plugin (v2.0.0) that registers `ctx.register_hook("pre_llm_call", _pre_llm_call)`. **Fix needed:** Either add deprecation warning in the Rust code output, or remove the Hermes path from `--memory-provider` entirely. This is a Rust codebase change, not a config fix. See `references/hermes-integration.md`.

62. ⚠️ **`POST /memory/feedback` updates `importance` — `importance` IS the trust score.** `importance` is a composite 0.0-1.0 score (+0.05 helpful, -0.10 unhelpful). Already exposed in recall, GET /memory, and feedback responses. No separate `trust_score` field needed.

63. ⚠️ **Route naming collision — `/room/summary` already existed for clustering.** When renaming an endpoint, ALWAYS grep the full route list in `handlers.rs` before committing. The existing `POST /room/summary` (room_summary: tag clustering) was invisible during code review because only the junction routes were checked. Clippy caught the duplicate `match` arm as `unreachable pattern`. **Rule:** Before any route rename, run `grep -n '"/room/' crates/uteke-server/src/handlers.rs` and verify no collision. **`replace_all` on Rust source is dangerous** — it also renamed SQL table names unintentionally. Always use targeted `replace` (not `replace_all`) when renaming identifiers in Rust source that contains both function names and SQL strings.

64. ⚠️ **`unwrap_or_default()` on `Option<usize>` returns 0 — logic bug.** When wiring optional config fields, `Option<usize>::unwrap_or_default()` returns 0 (not the intended default). For numeric config fields, always use `unwrap_or(ConfigStruct::default().field)` or pre-compute a defaults struct. Same pitfall applies to `Option<f32>`, `Option<f64>` — `unwrap_or_default()` returns 0.0 which may not be the intended fallback. **Pattern:** `let defaults = DreamConfig::default(); dc.field.unwrap_or(defaults.field)`.

65. ⚠️ **Generated files leak into `git commit --amend`.** A file generated during development keeps reappearing in amended commits even after `git rm --cached`. **Root cause:** The file exists in the working directory (untracked) and gets re-staged by pre-commit hooks or `git add -A`. **Fix:** Add to `.gitignore` and verify with `git status` before any `--amend` push.

68. ⚠️ **Orphaned FK references accumulate after bulk delete/aging.** `memory_edges`, `memory_tags`, `timeline_events`, `room_memories` reference deleted memories. Root cause: `PRAGMA foreign_keys` defaults OFF in SQLite. Uteke does not enforce FK on every connection. Aging/consolidation bulk deletes bypass CASCADE. **Workaround:** Periodic cleanup via direct SQLite — `DELETE FROM memory_edges WHERE source_id NOT IN (SELECT id FROM memories)`. **Fix:** Ensure `PRAGMA foreign_keys = ON` on every connection in Rust source (`store.rs` connection open).

69. ⚠️ **Zombie uteke-serve + stale WAL/SHM files block server startup.** If `uteke-serve` becomes a zombie (PID exists, status=Z) or is SIGKILL'd without clean shutdown, it leaves behind `uteke.db-wal` and `uteke.db-shm` lock files. The next `uteke-serve` startup stalls at "Opening store" indefinitely — health check fails. **Fix:** `kill -9 <zombie_pid>` then `rm -f ~/.uteke/uteke.db-shm ~/.uteke/uteke.db-wal` then restart. **Prevention:** Always use `kill <pid>` (SIGTERM) not `kill -9` (SIGKILL) when stopping uteke-serve. If SIGTERM hangs, kill + cleanup WAL/SHM.

70. ⚠️ **Multi-file patch tools can corrupt Cargo.toml — swaps adjacent lines, drops fields.** When using fuzzy multi-file patches to bump intra-workspace deps, the fuzzy matcher can swap adjacent lines with same structure (`path = "src/main.rs"` ↔ `readme = "README.md"`) and drop fields (`edition = "2021"`, `serde`, `tiny_http`). **Impact:** CI Build/Clippy fail or silently change binary behavior. **Prevention:** After any multi-file patch on Cargo.toml, ALWAYS verify with `diff`. **Better:** Use exact string matching replace for each file individually — it's safer for Cargo.toml.

72. ⚠️ **Hermes uteke-tool plugin namespace and room parameter bugs (FIXED).** Three bugs were fixed in the plugin's `tool.py`:
    - **Bug A (FIXED): `new_` parameter silently dropped.** `_get_room_id()` now checks `kwargs.get("new_", "")` as fallback after `room_id` and `room`.
    - **Bug B (FIXED): Namespace default hardcoded to `"hermes"`.** Now uses `os.environ.get("HERMES_PROFILE", "hermes")` as default — automatically matches the agent's profile namespace.
    - **Bug C (FIXED): `room_recall` doesn't send namespace.** `room_recall`, `room_summary`, `room_stats`, and `room_delete` now all include `namespace` in their API calls.
    **Note:** Plugin needs gateway reload to take effect. For room writes, `POST /room/remember` (v0.10.0+) is preferred over the plugin (see pitfall #18a).

75. ⚠️ **`uteke room recall` JSON format is INCONSISTENT between semantic and chronological modes.** With `--query`, returns `[{"memory": {...}, "score": 0.98}]` (wrapped, like `/recall` API). WITHOUT `--query`, returns flat `[{"id": "...", "content": "..."}]` (no wrapper, no score). **Any code parsing `room recall --json` MUST handle both formats.** Fix: unwrap function that checks for `"memory"` key:
    ```python
    def unwrap_room_recall(raw):
        out = []
        for item in raw:
            if "memory" in item and isinstance(item["memory"], dict):
                mem = item["memory"]
                mem["score"] = item.get("score", 0)
                out.append(mem)
            else:
                out.append(item)
        return out
    ```

76. ⚠️ **Editing embedded Python in Rust `init.rs` — escaping trap.** The `tool_py` string in `crates/uteke-cli/src/init.rs` is a single very long Rust string literal containing an entire Python file. Direct `patch`/`sed`/`replace` approaches fail because:
    - The entire Python file is **one line** in the .rs file — git diff shows 1 line changed.
    - In the **file on disk**, Rust escape `\"` = 2 chars (`\` + `"`), but Python `repr()` shows it as 3 chars (`\\"`). Pattern matching must use file-byte representation, not Python repr.
    - In the **file on disk**, Rust `\n` = 2 chars (`\` + `n`) = newline in the Rust string. Python docstrings inside the template must use `"""` (which in the file is `\"\"\"` = 6 chars). Using `\\\"` (3 backslashes) causes Rust error `unknown character escape: 'R'`.
    - Building search patterns with Python f-strings or raw strings is error-prone because you need triple-escaping for `\"` and `\n`.
    **Proven approach — Python script with `chr()` helpers:**
    ```python
    BS = chr(92)   # backslash
    QQ = chr(34)   # double quote
    NL = BS + 'n'  # Rust newline escape
    def q(s): return BS + QQ + s + BS + QQ  # Rust quoted string "..."
    ```
    Build patterns using these helpers, NOT raw strings or f-strings. Apply `content.replace(old, new)` then write.

### Room Appears Empty / Underpopulated

**Symptom:** `uteke room stats` shows 1-2 memories, or `room recall` returns empty, but the agent clearly stored more content related to that topic.

**Root cause:** Agent used `uteke remember` (or plugin's `remember` action) which stores to the namespace but does NOT create a `room_memories` junction row. The memory exists in SQLite and is searchable via `uteke recall`, but is invisible to `uteke room recall`.

**Diagnostic:**
1. Check memories IN room vs orphan candidates matching room keywords.
2. Or full audit: per-namespace coverage table. Namespaces with <10% coverage and >5 memories are almost certainly missing `room_remember` calls.
3. Verify directly: `SELECT COUNT(*) FROM memories WHERE namespace='myagent' AND deprecated=0` vs `SELECT COUNT(DISTINCT memory_id) FROM room_memories rm JOIN memories m ON rm.memory_id=m.id WHERE m.namespace='myagent' AND m.deprecated=0`.

**Fix:** Use `POST /room/remember` (v0.10.0+) or direct SQLite INSERT into `room_memories` (pitfall #18a) to backfill the junction rows.

**Prevention:** When an agent intends to store to a room, it must use `uteke room_remember` or the plugin's `room_remember` action — NOT the plain `remember` action.

### Database Health Check Pattern

| File | Description |
|------|-------------|
| [`references/db-health-check.md`](references/db-health-check.md) | Reusable audit for Uteke DB integrity. Run via Python+sqlite3 (works while uteke-serve runs). |

Full pitfalls → [`references/pitfalls_full.md`](references/pitfalls_full.md)
