# Uteke Pitfalls (Full List)

## Critical (check first)
1. **First run downloads 188MB model** — Lazy-loaded, ~20ms for non-embedding commands
2. **Namespace must be explicit** — Default "default". Always `--namespace <agent>`
3. **Always `--type` + `--detect-contradiction`** — Default fact loses richness
4. **After upgrade: `repair` then `doctor`** — Both DBs (HOME + DATA)
5. **Two binary paths shadow each other** — Clean stale `~/.local/bin/uteke`
6. **`forget` = POSITIONAL ID + `--confirm`** — Not `--id` flag
7. **Room `--room` is positional for subcommands** — Not a flag
8. **`doc create` SLUG is positional** — Not `--slug`
9. **`doc delete` by ID only** — Not slug
10. **recall() ≠ doc search** — Separate systems
11. **Content limit 10K chars** — #404 to remove
12. **CLI timeout when uteke-serve holds lock** — Use HTTP API at `localhost:8767` (Docker on Oracle via `/etc/hosts`). **NO local uteke-serve** — one server only. If HTTP API unavailable, use direct Python/SQLite: `sqlite3.connect('~/.uteke/uteke.db')`. See `references/cli-pitfalls.md` → "Bulk Noise Cleanup via Direct SQLite".
12a. **Multiple uteke processes cause SQLite lock contention** — Running local `uteke-serve` daemon + benchmark `uteke` CLI processes simultaneously locks `uteke.db`. The Docker container on Oracle hangs at `Opening store at: /data/uteke.db` with no further logs, domain unreachable. **Diagnosis:** `pgrep -fa uteke` — look for multiple PIDs (daemon, benchmark, child CLI). **Fix:** kill ALL local uteke processes (`pkill -9 -f uteke`), then `docker compose restart`. **Prevention:** NEVER start `uteke-serve` locally when Oracle Docker container is running.
12b. **Plugin `uteke-tool` env var mismatch + missing auth (fixed Jul 2026).** Plugin hard-coded `UTEKE_SERVER_URL` with default `127.0.0.1:8767`, but all agent `.env` files use `UTEKE_BASE_URL=http://localhost:8767`. Plugin also sent NO `Authorization` header → write ops returned 401/500. **Fixed:** `tool.py` now reads `UTEKE_SERVER_URL` → `UTEKE_BASE_URL` → fallback `http://localhost:8767`. Sends `Bearer $UTEKE_TOKEN` when set. **Standard config:** `UTEKE_BASE_URL=http://localhost:8767`, `UTEKE_TOKEN=<token>`, `UTEKE_NAMESPACE=<profile>`.

## Schema & Migration
13. **v7→v10 migration bug** — v0.3.2 fixes; existing v7 needs migration-v7-to-v11.py
14. **HOME DB may lag** — Manual migration if "no such column"
15. **Index mismatch after upgrade** — `uteke repair` both DBs
16. **schema_version format**: `(version INT, applied_at TEXT)` not `(key, value)`
17. **SCHEMA IF NOT EXISTS** — Doesn't modify existing tables. (Note: `POST /doc/create` was broken in v0.7 but fixed in v0.10.0 — now works via HTTP.)
18. **v11→v12 manual migration** — Add sort_order to documents

## Server & Performance
19. **uteke-serve deadlock (v0.3.2)** — Upgrade to v0.4.0+
20. **No rate limiting** — Not for public internet
21. **Auto-linking slow** — Cross-namespace cosine scan
22. **Zombie uteke-serve** — Stop daemon before replacing binary
23. **Mutex lock + blocking outbound HTTP = DoS** — uteke-serve uses `Mutex<Uteke>` (handlers.rs:79) to serialize ALL requests. If `/invoke` holds the lock while doing an outbound HTTP POST to a worker (30s timeout), every other endpoint (`/recall`, `/remember`, `/store`) blocks for the entire duration. Fix: release lock BEFORE outbound HTTP call, re-acquire only for writing the invocation log. This is a critical design constraint for RFC-001 tool-calling implementation.

## Config & Environment
23. **`--store` ≠ `UTEKE_HOME`** — Use `--store /path doctor`
24. **`uteke.json` no `${ENV_VAR}`** — Actual values only
25. **Don't set namespace in uteke.json** — Global override
26. **MemoryProvider in gateway process** — `UTEKE_NAMESPACE` in profile .env
27. **`uteke init` installs GLOBAL** — All agents share, overwrites
28. **MAX_SEQ_LEN was 256 → now 2048** — Repair after upgrade
29. **ONNX model nested `onnx/` subdir** — `models/embeddinggemma-q4/onnx/model_q4.onnx`
30. **Two graph systems** — Legacy metadata + auto-wired edges. Auto-wired primary since #346
31. **Plugin room actions not added** — #410 open
32. **"no command in config" MCP warning harmless** — uteke-tool is plugin, not MCP

## Multi-Repo & Publishing
33. **Multi-repo burden** — 6 repos = 6x CI
34. **`localhost/uteke` NOT a fork** — Independent repos, use `gh api` for PRs
35. **Inter-crate deps need manual bump** — `version.workspace` only covers crate itself
36. **Tag MUST be on main** — develop fails
37. **crates.io = API commitment** — Breaking changes need semver
38. **Shared SQLite concurrent risk** — WAL ok for reads, busy_timeout=5000ms for writes

## Rust Code Quality
39. **Materialized path LIKE needs full path** — Not UUID alone
40. **`has_children` stale on move/delete** — Explicit recompute
41. **`get_chunks_by_ids` unordered** — Use ordered variant
42. **`str::as_str()` unstable** — Use `as_ref()` or `&*s`
43. **CodeCora SARIF FPs on schema.rs** — Verify full call chain
48. **`println!` interprets `{}` as format placeholders** — JSON strings with curly braces in `println!()` must escape: `{` → `{{`, `}` → `}}`. E.g. `println!("{}",)` for raw JSON `{"key":"val"}` needs `println!("{{\"key\":\"val\"}}")`. CI error: `invalid format string: expected '}', found '"'` or `unmatched '}'`. Count braces carefully — 3 closing `}}}` in JSON needs 6 `}}}}}}` in Rust format string.

## Document Operations
49. **Root documents with NULL `path` column break `doc get` and `doc move --parent`.** The `documents` table has a `path TEXT` column for materialized paths (e.g., `/uuid/`). If root documents (depth=0, parent_id=NULL) were created before the `path` column was populated, they have `path=NULL`. Any command that calls `get_document_by_slug` (used internally by `doc get`, `doc move --parent`, `doc create --parent`) fails with: `Invalid column type Null at index: 12, name: path`. **Fix:** Direct SQLite: `UPDATE documents SET path = '/' || id || '/' WHERE path IS NULL AND depth = 0 AND parent_id IS NULL`. For child docs with NULL path, compute `parent_path + child_id + '/'`. After fixing, `doc move --parent` works. **Workaround:** `doc create` without `--parent` succeeds (upsert path differs from get), then move separately.
50. **CLI `doc list` is never global — `resolve_namespace()` always returns `Some("default")`.** `main.rs:165` resolves to `"default"` when no flag/env/config set, then `doc.rs:16` wraps in `Some(ns.as_str())`. Result: `uteke doc list` only shows docs in namespace `"default"`, even though server/Corin support `ns(None)` = global list. **Workaround:** `uteke doc list --namespace <ns>` per namespace, or use `uteke doc export --json` for all. **Fix:** Issue #614 — docs made global (no namespace isolation) starting from PR fix/614-doc-global-no-namespace.
51. **Docs ≠ Memories — namespace isolation is wrong for docs.** Documents are a shared wiki/knowledge base; namespace per-agent isolation was inherited from memories but causes UX problems: data appears "lost" when switching namespace view in Corin, slug duplication across namespaces wastes storage. Since #614: docs are global, slug uniqueness is global, `author` field added for attribution. Namespace column still exists in DB but is nullable/deprecated for docs.
52. **No batch/prune for documents.** Memories have `prune`, `forget --tag/--cold/--all`, `consolidate`, `dream`. Documents only have single-ID delete (`doc delete <id>`) with cascade. No batch delete, no TTL-based cleanup, no prune. Workaround: `uteke doc export --json > /tmp/docs.json`, filter IDs, loop `uteke doc delete "$id" --confirm`.

## Hermes Integration (Jul 2026)
53. **Hermes `uteke` tool broken — `PluginContext.agent_name` AttributeError (Jul 2026, FIXED root cause identified).** The `uteke` tool throws `AttributeError: 'PluginContext' object has no attribute 'agent_name'`. This is NOT a Hermes upstream bug — it's a **user-deployed plugin bug**. The gateway loads plugins from `HERMES_HOME/plugins/` = `~/plugins/uteke-tool/__init__.py` (old buggy copy, 377 lines). A fixed copy exists at `~/.hermes/plugins/uteke-tool/__init__.py` (107 lines) but is NOT loaded because that path is never scanned when `HERMES_HOME=~`. The old plugin's `uteke_handler()` closure captures `ctx` from `register(ctx)` and accesses `ctx.agent_name` (line 66 & 244) — but `PluginContext` only has `profile_name`. **Fix:** patch `~/plugins/uteke-tool/__init__.py`: `ctx.agent_name` → `ctx.profile_name`, or replace with the fixed version. See `uteke-plugin-fix` skill → "Dual Plugin Path Bug" section. **Three distinct uteke code paths exist in Hermes:**
    - **`uteke-tool` plugin** (`~/plugins/uteke-tool/`) — Old CLI-based plugin. **BROKEN** with `ctx.agent_name` error. This is the one loaded by the gateway.
    - **`uteke-tool` plugin** (`~/.hermes/plugins/uteke-tool/`) — Fixed HTTP-based plugin. NOT loaded (wrong path). Uses `uteke-serve` HTTP API.
    - **`uteke` memory provider** (`~/.hermes/plugins/uteke/`) — MemoryProvider bridge. Registers via `ctx.register_memory_provider()`. NOT loaded from this path either.
    - **`knowledge` tool** — Hermes's built-in hybrid memory tool (Qdrant→Uteke HTTP→SQLite cascade). The Uteke tier uses HTTP API directly. **This one works** — prefer it when the `uteke` tool fails.
54. **uteke CLI binary hangs on ALL commands (Jul 2026).** `uteke recall`, `uteke doctor`, `uteke stats` all timeout (180s+). Not connection refused — silent hang with no output. **Root causes:** (1) Embedding server unreachable → embedding generation blocks. (2) Stale usearch `fs2` advisory lock from killed uteke-serve. (3) Large store (18K+ memories) → slow vector ops. **Fix:** `pkill -f uteke; rm -f ~/.uteke/uteke_index.usearch.lock` then restart uteke-serve. If corrupt: `uteke repair --namespace <ns>` then `uteke doctor`. **Workaround:** Use uteke-serve HTTP API directly or the `knowledge` tool.
55. **`uteke verify` and `uteke doctor` specifically timeout when uteke-serve holds the usearch lock (Jul 2026).** Distinct from #54 — this is NOT a stale lock from a killed process, but a **live lock contention** between a running uteke-serve and CLI commands. Both need exclusive access to `uteke_index.usearch`. Log shows repeated: `usearch file lock busy on ...uteke_index.usearch, waiting...` (16+ occurrences in a single day). **Diagnosis:** `ps aux | grep uteke-serve` confirms serve running. **Preferred fix — use HTTP API:** `curl -sf -H "Authorization: Bearer $UTEKE_TOKEN" http://localhost:8767/health` returns `{"status":"ok","version":"0.7.2","memories":N,"namespaces":N}`. For actual verify/repair, stop uteke-serve first, then run CLI. **Also see:** SKILL.md pitfall #0f.
56. **`POST /remember` with `room_id` SILENTLY FAILS to create room_memories junction (v0.7.2, Jul 2026).** The HTTP API endpoint accepts `room_id` in the JSON body and returns `{"id": "<uuid>"}` (success response), but the `room_memories` junction row is **never created**. The memory exists in SQLite but is invisible when doing room-scoped recall. **Diagnosis:** `SELECT * FROM room_memories WHERE memory_id = '<uuid>'` returns empty. **Fix — direct SQLite insert after POST /remember:** `INSERT OR IGNORE INTO room_memories (room_id, memory_id, author, role, joined_at) VALUES ('<room>', '<id>', '<author>', 'author', '<iso-timestamp>')`. **Schema:** 5 columns — `room_id TEXT`, `memory_id TEXT`, `author TEXT NOT NULL`, `role TEXT NOT NULL DEFAULT 'participant'`, `joined_at TEXT NOT NULL`. **Also see:** SKILL.md pitfall #18a. **Note (Jul 2026):** The **CLI path** (`uteke remember "content" --room <id>`) appears to handle the junction correctly — it returned `✓ Memory stored` with a valid ID and the room_memories entry was created. This bug may be HTTP-API-specific. When using CLI, pass content as a positional arg (NOT stdin, see pitfall #0). Always verify with a SQLite query after storing if room visibility matters.
57. **Skill sync namespace isolation — synced skills invisible to agents (Jul 2026).** `sync_skills_to_uteke.py` stores 509 skills to `default` namespace (no `--namespace` flag). But `uteke-recall` hook queries per-agent namespaces (`--namespace cto`, `--namespace coo`, etc.). Result: `uteke recall "docker" --namespace cto` returns nothing even though skills exist in `default`. **Fix: use Uteke rooms** (cross-namespace) for skill storage instead of flat memories. See `skill-audit` → `references/skill-routing-architecture.md` for migration plan. **Context:** Qdrant (hermes-skills collection, 465 points) being deprecated — all skill routing migrating to Uteke.

## HTTP API Quirks (via Traefik domain, Jul 2026)
71. **`POST /remember` with tags returns "Internal server error" but data IS saved.** When storing via `https://uteke.localhost/remember` with a `tags` array, the HTTP response body is `{"error":"Internal server error"}` but the memory is actually persisted. Confirmed by searching and finding the memory. **Without tags:** returns clean `{"id":"<uuid>"}`. **With tags:** error body but data saved. **Impact:** Error-handling code that checks response body will incorrectly assume failure. **Fix:** Always check via search after remember, or ignore the error body and assume success when no exception was raised. **Do NOT retry** — retrying creates duplicate memories (each attempt saves despite the error response).
72. **~~`POST /forget` returns "Not found" and does NOT delete.~~ FIXED: `/forget` uses DELETE method, not POST.** Correct usage: `curl -X DELETE "http://localhost:8767/forget?id=<uuid>" -H "Authorization: Bearer $UTEKE_TOKEN"`. Returns `{"forgotten":"<uuid>"}`. Also supports bulk delete by tag: `DELETE /forget?tag=<TAG>&namespace=<NS>`. **Never use POST for /forget.** SQLite is last resort only.
73. **Domain (`uteke.localhost`) requires auth; NEVER use `localhost:8767` or `127.0.0.1:8767` from VM.** `https://uteke.localhost/` always needs `Authorization: Bearer $UTEKE_TOKEN`. Local `http://localhost:8767` / `http://127.0.0.1:8767` may point to a DIFFERENT uteke instance (local uteke-serve) with a different database, causing dual-store problems. **Standard pattern:** Use `$UTEKE_BASE_URL` env var (defaults to `https://uteke.localhost`) + `$UTEKE_TOKEN` for all operations. Docker internal: `http://localhost:8767` (reachable only from within Docker network).
74. **No `POST /remember_in_room` HTTP endpoint.** The uteke-server HTTP API has NO endpoint to simultaneously create a memory AND link it to a room. `POST /remember` with `room_id` field creates the memory but does NOT create the `room_memories` junction row (see pitfall #56). **Workaround:** POST /remember first, then INSERT into `room_memories` via direct SQLite.

## Infrastructure: Hooks HTTP API Rewrite (Jul 2026)
74. **uteke-extract and uteke-recall hooks rewritten from CLI to HTTP API.** Both hooks at `~/hooks/uteke-{extract,recall}/handler.py` were changed from `subprocess.run([UTEKE_BIN, ...])` to `urllib.request` calls. Source of truth: `$UTEKE_BASE_URL` (default `https://uteke.localhost`). Auth: `$UTEKE_TOKEN`. If `UTEKE_TOKEN` is empty, hooks silently return empty results (no crash). **No more local `uteke` CLI dependency in hooks.**
75. **~~uteke-tool plugin still has `http://127.0.0.1:8767` default (Jul 2026).~~ FIXED.** Plugin at `~/plugins/uteke-tool/tool.py` now reads `UTEKE_SERVER_URL` → `UTEKE_BASE_URL` → fallback `https://uteke.localhost`. Also sends `Authorization: Bearer $UTEKE_TOKEN` header when set. **Full domain migration completed (Jul 2026):** ALL hooks, plugins, scripts, and 15+ skills updated from `localhost:8767`/`127.0.0.1:8767` to `https://uteke.localhost` (domain) or `http://localhost:8767` (Docker internal). Standard env: `UTEKE_BASE_URL=http://localhost:8767`, `UTEKE_TOKEN=<token>`. **Never use `127.0.0.1:8767` or `localhost:8767` from the VM** — these point to a local uteke-serve instance with a DIFFERENT database, causing dual-store problems.

## General
44. **Uteke ≠ task orchestrator** — Tasks in Hermes Kanban
45. **Docker volume needed** — Mount ~/.uteke/
46. **Use pre-built binary** — Not `cargo install`
47. **`hermes` CLI: `/opt/hermes/.venv/bin/hermes`**
