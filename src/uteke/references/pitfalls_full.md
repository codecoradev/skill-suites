# Uteke Pitfalls (Full List)

## Critical (check first)
1. First run downloads 188MB model — Lazy-loaded, ~20ms for non-embedding commands
2. Namespace must be explicit — Default "default". Always `--namespace <agent>`
3. Always `--type` + `--detect-contradiction` — Default fact loses richness
4. After upgrade: `repair` then `doctor` — Both DBs (HOME + DATA)
5. Two binary paths shadow each other — Clean stale `~/.local/bin/uteke`
6. `forget` = POSITIONAL ID + `--confirm` — Not `--id` flag
7. Room `--room` is positional for subcommands — Not a flag
8. `doc create` SLUG is positional — Not `--slug`
9. `doc delete` by ID only — Not slug
10. `recall()` ≠ `doc search` — Separate systems
11. Content limit 10K chars — Split long content into multiple memories
12. CLI timeout when uteke-serve holds lock — Use HTTP API at `localhost:8767`
12a. Multiple uteke processes cause SQLite lock contention — Only one process at a time. `pkill -9 -f uteke` then restart.
12b. Plugin env var mismatch — Use `UTEKE_BASE_URL` (not `UTEKE_SERVER_URL`). Send `Bearer $UTEKE_TOKEN` header for auth.

## Schema & Migration
13. v7→v10 migration bug — v0.3.2 fixes; existing v7 needs migration script
14. HOME DB may lag — Manual migration if "no such column"
15. Index mismatch after upgrade — `uteke repair` both DBs
16. schema_version format: `(version INT, applied_at TEXT)` not `(key, value)`
17. `POST /doc/create` was broken in v0.7, fixed in v0.10.0
18. v11→v12 manual migration — Add sort_order to documents

## Server & Performance
19. uteke-serve deadlock (v0.3.2) — Upgrade to v0.4.0+
20. No rate limiting — Not for public internet without reverse proxy
21. Auto-linking slow — Cross-namespace cosine scan, disable for large datasets
22. Dream phase can OOM — Use `--dry-run` first on large namespaces
23. Container mutex serializes ALL requests — Add `--max-time 10` to curl

## HTTP API Specifics
24. `/remember` drops custom `metadata` field (Bug #56) — Direct SQLite for structured metadata
25. `recall` response wrapped in v0.8.0 — `[{memory: {...}, score: N}]` not flat array
26. `/forget` by tag requires `namespace` param — Otherwise deletes across all namespaces
27. `tags` parameter must be JSON array — Not comma-separated string
28. `/room/recall` requires `query` field — No "list all" endpoint (use `GET /room/memories`)

## Plugin (uteke-tool)
29. Plugin sends NO auth header pre-v0.5.0 — Upgrade required
30. Plugin reads `UTEKE_BASE_URL` → fallback `http://localhost:8767`
31. Plugin `room_remember` requires `author` field — Optional in CLI, required in plugin
32. Plugin timeout 30s default — Increase for large `room_recall` queries

## Data Integrity
33. Vector index desync — `uteke repair` to regenerate missing embeddings
34. Orphaned tags after forget — `uteke tags cleanup` (v0.9.0+)
35. Room memories not in namespace stats — Rooms are separate scope
36. `importance` defaults to 0.5 — Use feedback API to adjust
37. Pinned memories always returned first in recall — Use for critical context

## CLI vs HTTP API
38. CLI `recall --json` prepends line numbers — Room recall does not
39. CLI `--meta` works (direct DB) — HTTP `/remember` drops metadata (Bug #56)
40. CLI `--type` sets metadata only — `memory_type` column stays "fact" via HTTP
41. CLI timeout 180s default — HTTP API has no timeout (use `--max-time`)
