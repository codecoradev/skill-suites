# Uteke Bulk Cleanup / Prune / Delete Surface Map

Audited: 2026-07-08 (uteke v0.6.7, `~/repos/uteke/`)

## Core Library (`uteke-core`)

### `memory/bulk.rs` — Bulk Delete Operations

| Function | Scope | What It Does |
|----------|-------|-------------|
| `bulk_delete_by_tag(tag, ns)` | Tag + namespace | Hard DELETE all memories with given tag |
| `bulk_delete_cold(ns, warm_days)` | Namespace | Hard DELETE memories not accessed in N+ days or never accessed |
| `bulk_delete_all(ns)` | Namespace | Hard DELETE every memory in namespace |
| `deprecate(id)` | Single ID | Soft-delete: set `deprecated=1`, `valid_until=now` |
| `prune_ttl(ttl_days, ns)` | Deprecated + namespace | Hard DELETE deprecated memories older than TTL |
| `find_deprecated_for_prune(ttl_days, ns)` | Read-only | Dry-run: list what `prune_ttl` would delete |
| `delete_by_ids(ids)` | Explicit ID list | Hard DELETE by IDs (avoids TOCTOU races) |
| `find_similar(ns, limit)` | Namespace | Find non-deprecated memories (for contradiction detection) |

### `memory/aging.rs` — Age-Based Cleanup

| Function | Scope | What It Does |
|----------|-------|-------------|
| `find_aged(older_than_days, max_access_count, ns)` | Read-only | Find old, rarely-accessed memories |
| `cleanup_aged(older_than_days, max_access_count, ns)` | Namespace | Hard DELETE aged memories |
| `tier_counts(ns, hot_days, warm_days)` | Read-only | Hot/warm/cold memory counts |
| `count_never_accessed(ns)` | Read-only | Count memories never recalled |

### `operations.rs` — High-Level API (core + vector index cleanup)

| Function | Wraps | Also removes from usearch index? |
|----------|-------|----------------------------------|
| `bulk_forget_by_tag()` | `bulk_delete_by_tag` | ✅ Yes |
| `bulk_forget_cold()` | `bulk_delete_cold` | ✅ Yes |
| `bulk_forget_all()` | `bulk_delete_all` | ✅ Yes |

### `dream.rs` — Dream Cycle (coordinated 6-phase pipeline)

Phases: `lint → backlinks → dedup → orphans → compact → verify`

**Compact phase** calls `prune(TTL_DAYS=30, namespace, dry_run)` which:
1. `find_deprecated_for_prune()` to count candidates
2. If dry_run=false: `prune_ttl()` to hard-delete deprecated memories

## CLI Exposure

| Command | Modes | Safety |
|---------|-------|--------|
| `uteke forget <id> --confirm` | Single memory delete | `--confirm` or interactive prompt |
| `uteke forget --tag <tag> [--namespace] --confirm` | Bulk by tag | `--confirm` or shows count first |
| `uteke forget --cold [--namespace] --confirm` | Bulk cold memories | `--confirm` or warns |
| `uteke forget --all [--namespace] --confirm` | Bulk all in namespace | `--confirm` required |
| `uteke prune --ttl <days> [--dry-run]` | Prune deprecated by TTL | `--dry-run` preview |
| `uteke aging status` | Show tier counts | Read-only |
| `uteke aging preview --older-than-days N --max-access-count N` | List candidates | Read-only |
| `uteke aging cleanup --older-than-days N --max-access-count N --yes` | Hard delete aged | `--yes` confirmation |
| `uteke dream [--phases ...] [--skip ...] [--dry-run]` | Full pipeline | `--dry-run`, errors exit non-zero |
| `uteke consolidate [--threshold] [--dry-run]` | Dedup/merge | `--dry-run` preview |

## Server API Exposure (uteke-serve)

| Endpoint | Method | Bulk Modes Available |
|----------|--------|---------------------|
| `DELETE /forget?id=` | DELETE | Single only |
| `DELETE /forget?tag=&namespace=` | DELETE | Bulk by tag ✅ |
| `POST /prune` | POST | Prune deprecated by TTL ✅ |
| `POST /aging` | POST | `{action: "status\|preview\|cleanup"}` ✅ |
| `POST /dream` | POST | Full dream cycle ✅ |
| `POST /consolidate` | POST | Dedup merge ✅ |

## Gaps — What Doesn't Exist

### No HTTP exposure for these core operations:

| Core Function | CLI Available | Server HTTP | MCP |
|---------------|-------------|-------------|-----|
| `bulk_forget_cold()` | ✅ `uteke forget --cold` | ❌ Missing | ❌ Missing |
| `bulk_forget_all()` | ✅ `uteke forget --all` | ❌ Missing | ❌ Missing |

### No document-level bulk cleanup:
- `/doc/delete` only deletes single documents (with cascade to children)
- No batch doc delete by prefix, tag, namespace, or age
- No `bulk_delete_documents()` in `memory/documents.rs`
- **Workaround:** `uteke doc export --json > /tmp/docs.json` → `jq` to filter IDs → loop `uteke doc delete <id> --confirm`

### CLI doc list never global (design bug):
- `resolve_namespace()` in `cli/main.rs:165` always returns a string (defaults `"default"`)
- `doc.rs:16` wraps as `Some(ns.as_str())` — never `None`
- Server's `ns(None)` returns global results correctly, but CLI never passes `None`
- Corin desktop handles this correctly (passes `null` when no namespace selected)
- **Root cause** of most "docs disappeared" reports — docs exist in another namespace

### Design debt: docs shouldn't use namespace isolation:
- Docs = shared wiki/knowledge base, not agent-isolated data like memories
- Namespace on docs causes UX confusion (switch namespace → docs "disappear")
- Slug uniqueness per namespace creates duplicates across namespaces
- **Future direction:** `namespace` nullable, slug unique globally, `author` field for attribution

### Desktop app doc cleanup (Corin, Hub):

| App | Doc Engine | Batch Delete UI | Notes |
|-----|-----------|-----------------|-------|
| Corin (`~/corin`) | ✅ wraps uteke-serve | ❌ single-delete only | `DocumentsView.svelte` — one 🗑 button per doc, no multi-select |
| Hub (`~/hub`) | ❌ no doc engine | N/A | Only memories, no document operations at all |

### No SQLite-level optimization:
- No `PRAGMA optimize` or `VACUUM` exposed (compact handles data rows, not file-level bloat)

### No scheduled automation:
- No built-in cron/timer; relies on external scheduling (`uteke dream` via cron)

## Safety Patterns

1. **All bulk CLI deletes require `--confirm`** — without it, they show what would be affected and exit
2. **Server has no confirmation** — HTTP endpoints execute immediately (auth-gated)
3. **Vector index synced** — `operations.rs` wrappers acquire write lock on usearch before SQLite delete
4. **Dream compact is safe** — only deletes `deprecated=1 AND updated_at < TTL` (soft-deprecated first)
5. **Aging cleanup preserves** — skips pinned (`pinned=0`) and high-access memories
