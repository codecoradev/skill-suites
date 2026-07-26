# Uteke CLI Pitfalls — Production-Tested

Patterns discovered from active use on Hermes server. Updated July 9, 2026.

## `uteke remember` — Stdin Pipe Does NOT Work (GitHub #620)

`cat file | uteke remember -` silently stores literal `"-"` instead of reading stdin. `<CONTENT>` is a positional argument — no stdin support exists.

**Reproduction:**
```bash
echo "test content" | uteke remember --namespace test --tags "test-pipe" - 2>&1
# → ✓ Memory stored (ID: ...)
uteke recall --namespace test "test-pipe" --json --limit 1
# → {"content": "-"}  ← WRONG — should be "test content"
```

**Fix:** Always pass content as positional argument. For long content (>4K chars) or content with shell metacharacters, use Python subprocess:
```python
import subprocess
subprocess.run(["uteke", "remember", "--namespace", "ns", "content"], timeout=30)
```

## `uteke recall --json` — Line Numbers in Content (GitHub #622)

Normal recall prepends line numbers: `"content": "1|[text]\n2|[more]"`. Room recall does NOT (clean content). Strip `"N|"` prefixes when parsing recall JSON, or prefer room recall.

## Vector Index Desync — Memories Invisible to Semantic Search (GitHub #621)

Memories can exist in SQLite but have NO vector embedding → invisible to `uteke recall`. Symptoms:
- Room has 43 memories but `uteke recall` only finds 12
- `uteke forget` warns: "Vector index entry not found during forget for id=..."

**Diagnosis & Fix:**
```bash
uteke verify --namespace <ns>
# → ✗ MISMATCH — SQLite: 17755, Index: 17055

uteke repair --namespace <ns>
# → ✓ Index rebuilt successfully (17055 → 17755)

uteke doctor  # Verify consistent
```

**Real case (Jul 2026):** 700/17,755 memories (4%) missing from vector index on Hermes server. Likely caused by concurrent writes or silent embedding generation failure.

**Prevention:** Run `uteke repair` after any bulk remember/forget operation. Run `uteke verify` periodically.

## `uteke room recall` — Default Limit 20 Silently Truncates (GitHub #623)

`room stats` reports correct count but `room recall` returns only 20 without `--limit`:
```bash
uteke room stats --namespace coo --json "disc:topic"  # → memory_count: 43
uteke room recall --namespace coo --json "disc:topic"    # → 20 results (no warning!)
uteke room recall --namespace coo --json --limit 100 "disc:topic"  # → 43 results
```

**Rule:** Always pass `--limit 100` (or higher) for rooms exceeding 20 memories.

## Building from Source — OpenSSL / ort-sys

`ort-sys` (ONNX Runtime bindings) requires OpenSSL headers. On Hermes server they're at a non-standard path:

```bash
export PKG_CONFIG_PATH="~/.openssl-dev/lib/pkgconfig"
export OPENSSL_DIR="~/.openssl-dev"
cargo check -p uteke-cli  # or cargo test, cargo build
```

**Without these env vars:** Build fails with `openssl-sys` configure errors (can't find SSL headers).

**Pitfall:** The `.pc` files in `~/.openssl-dev/lib/pkgconfig/` may have wrong prefix (says `/usr` but actual is `~/.openssl-dev`). Patch `Cflags` and `Libs` if `pkg-config --cflags openssl` returns wrong paths.

**Pitfall:** ARM-specific include dir — `configuration.h` may be at `include/aarch64-linux-gnu/openssl/configuration.h`. If `ort-sys` can't find it, symlink it to `include/openssl/configuration.h`.

**Pitfall:** `std::fs::metadata()` does NOT return a type that impls `Default`. Cannot use `.unwrap_or_default()`. Use `match` instead:

```rust
// WRONG: let meta = std::fs::metadata(&path).unwrap_or_default();
// RIGHT:
match std::fs::metadata(&path) {
    Ok(metadata) if metadata.len() as usize > max_size => { /* skip */ }
    _ => { /* proceed */ }
}
```

## Patch Tool + Rustfmt Pitfall

When patching Rust files, the `patch` tool auto-runs rustfmt which can reformat surrounding code in unexpected ways. This is especially problematic when:

- The `old_string` has inconsistent indentation (mix of 2/4 space indents)
- The patch inserts code into a block that rustfmt reformats entirely

**Mitigation:** Always use `read_file` to verify exact whitespace before patching. If a patch mangles formatting, use subsequent patches to fix rather than rewriting the whole file. The rustfmt diff output (shown in lint errors) is actually helpful — it shows exactly what changed.

## `uteke forget` — Non-Interactive Deletion

```bash
# ID is POSITIONAL (not --id flag). Requires --confirm to skip y/N prompt.
uteke forget --namespace cto 367171cc-ab68-433c-b7c5-7266eb2ff836 --confirm
# Output: {"forgotten":"367171cc-..."}

# Delete all memories with a tag:
uteke forget --namespace cto --tag bench --confirm

# Delete ALL cold memories:
uteke forget --namespace cto --cold --confirm
```

**Pitfall:** Without `--confirm`, uteke prompts interactively. In Hermes terminal (non-PTY), the prompt defaults to "N" (cancelled). Always use `--confirm` in scripts/terminal.

**Pitfall:** Flag is `--id` but it's actually a positional arg. `uteke forget --id UUID` → `error: unexpected argument '--id' found`. Correct: `uteke forget UUID --confirm`.

## Index Corruption After Gateway Restart

**Happened June 28, 2026.** When all Hermes gateways are restarted via `s6-svc -r /run/service/gateway-*/`, uteke-serve gets killed mid-write and the shared usearch index corrupts. Symptoms:

```
uteke recall --namespace cto "test" 2>&1
# → WARN uteke_core::error: "Not a dense USearch index!"
# → or "End of file reached!"
uteke doctor
# → ✗ Index consistency: MISMATCH
uteke repair --namespace cto
# → Error: Failed to open memory store: load vector index: embedding operation failed
```

**Root cause:** Gateway restart kills uteke-serve (child process) while it holds the index file lock. The `.usearch` file gets partially written.

**Safe gateway restart pattern:** Before restarting gateways, stop uteke-serve first:

```bash
# 1. Stop uteke-serve gracefully
kill $(pgrep -f "uteke-serve") 2>/dev/null
sleep 2

# 2. Restart all gateways
for svc in /run/service/gateway-*/; do
  /command/s6-svc -r "$svc"
done

# 3. Restart uteke-serve AFTER gateways are up
uteke-serve --host 127.0.0.1 --port 8767

# 4. Verify
uteke doctor  # Should pass
```

**Note:** `s6-svc` is NOT in `$PATH`. Full path: `/command/s6-svc` (symlink to `/package/admin/s6-2.15.0.0/command/s6-svc`).

**Fix — full index rebuild** (if already corrupted):

```bash
# 1. Kill uteke-serve (may already be dead)
kill $(pgrep -f "uteke-serve") 2>/dev/null

# 2. Delete ALL index files (keys + usearch + backups)
rm -f ~/.uteke/uteke_index.usearch ~/.uteke/uteke_index.usearch.bak
rm -f ~/.uteke/uteke_index.keys ~/.uteke/uteke_index.keys.bak

# 3. Repair (rebuilds from SQLite — no data loss)
uteke repair --namespace default 2>&1
# → Index rebuilt successfully

# 4. Verify
uteke doctor
# → All checks passed.

# 5. Restart uteke-serve
uteke-serve --host 127.0.0.1 --port 8767
```

**Pitfall:** Per-namespace `uteke repair --namespace cto` only works if uteke-serve is NOT running. If uteke-serve is up, it locks the shared index and repair fails. Kill uteke-serve first.

**Pitfall:** If you repair ONE namespace (e.g. cto) while others are still corrupted, subsequent namespace repairs fail with "Not a dense USearch index" because the shared index file was rebuilt by the first repair. Delete index files first, then repair `default` namespace (which rebuilds the global index).

**Pitfall:** `uteke doctor` shows global stats but `uteke repair` works per-namespace. Always use `--namespace default` after deleting index files to rebuild the global index.

## Index Mismatch After Bulk Deletes

After deleting multiple memories, the vector index can desync from SQLite:

```
✗ Index consistency: MISMATCH: DB=770 Index=771 — run `uteke repair`
```

**Fix:** Run `uteke repair` after any bulk `forget` operation. This rebuilds the usearch index from SQLite.

```bash
uteke forget --namespace cto <UUID> --confirm
uteke repair --namespace default
uteke doctor  # Verify: should show DB count == Index count
```

## Test Data Cleanup Procedure

When validating recall quality, test/benchmark data pollutes results. Use this procedure:

```bash
# 1. List all namespaces to find where test data lives
uteke namespace list

# 2. List memories in namespace to identify test entries
uteke list --namespace cto

# 3. Delete individual test entries (use --confirm for non-interactive)
uteke forget --namespace cto <UUID> --confirm

# 4. Repair index after bulk deletes
uteke repair

# 5. Verify health
uteke doctor  # Should show DB count == Index count
```

**Common test data patterns to clean:** entries tagged `[t]`, `[debug]`, `[bench]`, or content like `"Uteke is great"`, `"warm benchmark message"`, `"test embed"`, `"fresh start benchmark test"`.

### Bulk Noise Cleanup via Direct SQLite (when CLI times out)

When uteke CLI commands (`stats`, `list`, `recall`, `search`, `namespace list`) all **timeout** (usually because a gateway process holds the DB lock), use direct Python/SQLite access instead:

```python
import sqlite3

DB = '~/.uteke/uteke.db'
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Build temp table of IDs to delete
cur.execute("CREATE TEMP TABLE to_delete (id TEXT PRIMARY KEY)")

# Pattern 1: "The user wants/is/asked..." extraction noise (most common)
cur.execute("""
    INSERT OR IGNORE INTO to_delete (id)
    SELECT id FROM memories 
    WHERE content GLOB 'The user *'
       OR content GLOB "User's handle*"
       OR content LIKE '%unknown - untitled%'
""")

# Pattern 2: Test/experiment tags
cur.execute("""
    INSERT OR IGNORE INTO to_delete (id)
    SELECT id FROM memories 
    WHERE tags LIKE '%"test"%' 
       OR tags LIKE '%"experiment"%'
       OR tags LIKE '%"test-debug"%'
       OR tags LIKE '%"handler-debug"%'
       OR tags LIKE '%"uteke-recall-auto-test"%'
""")

# Pattern 3: Explicit test/dummy content
cur.execute("""
    INSERT OR IGNORE INTO to_delete (id)
    SELECT id FROM memories 
    WHERE content LIKE 'test in %' 
       OR content LIKE 'Direct test:%' 
       OR content LIKE '[AUTO-TEST]%' 
       OR content LIKE 'benchmark message%' 
       OR content LIKE 'Test alert%'
""")

# Pattern 4: auto-extract session dumps (truncated session summaries)
cur.execute("""
    INSERT OR IGNORE INTO to_delete (id)
    SELECT id FROM memories 
    WHERE tags LIKE '%"reason:session_expired"%' 
       OR tags LIKE '%"reason:shutdown"%'
""")

# Preview before deleting
total = cur.execute("SELECT count(*) FROM to_delete").fetchone()[0]
print(f"IDs to delete: {total}")

# Delete from related tables first (FK integrity)
cur.execute("DELETE FROM memory_tags WHERE memory_id IN (SELECT id FROM to_delete)")
cur.execute("DELETE FROM memory_edges WHERE source_id IN (SELECT id FROM to_delete) OR target_id IN (SELECT id FROM to_delete)")
cur.execute("DELETE FROM room_memories WHERE memory_id IN (SELECT id FROM to_delete)")

# Delete from main memories table
cur.execute("DELETE FROM memories WHERE id IN (SELECT id FROM to_delete)")

# ⚠️ CRITICAL: Do NOT "DELETE FROM memories_fts" — this causes
# "database disk image is malformed" error on FTS5 virtual tables.
# Instead, DROP + RECREATE the FTS index:
cur.execute("DROP TABLE IF EXISTS memories_fts")
cur.execute("DROP TABLE IF EXISTS memories_fts_data")
cur.execute("DROP TABLE IF EXISTS memories_fts_idx")
cur.execute("DROP TABLE IF EXISTS memories_fts_docsize")
cur.execute("DROP TABLE IF EXISTS memories_fts_config")
cur.execute("""
    CREATE VIRTUAL TABLE memories_fts USING fts5(
        content, tags, namespace,
        content='memories', content_rowid='rowid'
    )
""")
cur.execute("INSERT INTO memories_fts(rowid, content, tags, namespace) SELECT rowid, content, tags, namespace FROM memories")

conn.commit()

# Verify
remaining = cur.execute("SELECT count(*) FROM memories").fetchone()[0]
print(f"Remaining: {remaining}")
conn.close()
```

**⚠️ FTS5 DELETE pitfall:** `DELETE FROM memories_fts WHERE rowid IN (...)` raises `database disk image is malformed` on Uteke's FTS5 virtual tables. Always **drop + recreate** instead.

**⚠️ After this cleanup, `uteke repair` is still needed** to rebuild the usearch embedding index (the SQLite delete only cleans the DB, not the vector index). Run repair when no gateway holds the lock.

## `uteke remember --type` — Valid Types Only

`--type` only accepts: `fact`, `procedure`, `preference`, `decision`, `context`, `note`, `insight`, `reference`, `event`. Common mistake: using `--type analysis` (not valid — use `insight` for analytical findings).

```bash
# ❌ WRONG — "analysis" is not a valid type
uteke remember --namespace cmo --room my-room --type analysis "..."
# → Validation error: Unknown memory type 'analysis'

# ✅ CORRECT — use "insight" for analytical findings
uteke remember --namespace cmo --room my-room --type insight "..."
```

## `uteke recall` — Positional Query

```bash
# Query is POSITIONAL (not --query flag)
uteke recall --namespace cto "my search query" --limit 5
# NOT: uteke recall --query "my search query"  ← ERROR
```

## `uteke namespace` — List & Stats

```bash
uteke namespace list    # All namespaces with memory counts
uteke namespace stats   # Current namespace stats
uteke namespace list --json  # Machine-readable
```

Useful for auditing agent memory usage across fleet.

## `uteke recall --json` Output Format

v0.0.7+ nests results under `memory` key:

```json
[{"memory": {"id": "uuid", "content": "...", "tags": [...], "namespace": "..."}, "score": 0.72}]
```

NOT flat `{content, score}`. Parse `item["memory"]["content"]` and `item["score"]`.

## CLI vs Serve Embedding Inconsistency (CRITICAL)

**Same query, different results** between `uteke recall` (CLI) and `uteke-serve` (HTTP):

| Query | CLI Result | Serve HTTP Result |
|-------|-----------|-------------------|
| "Bagaimana kondisi terakhir?" | `[]` ❌ | 2 results (0.41, 0.37) ✅ |
| "kondisi terakhir proyek" | 1 result (0.36) ✅ | 2 results ✅ |

**Root cause:** CLI does cold ONNX inference each call (graph optimization state varies). Serve keeps model warm in RAM with consistent graph state. The score difference means CLI can return `[]` when serve finds matches above threshold.

**Fix:** Use uteke-serve HTTP instead of CLI subprocess when available:
```python
# In hooks/scripts — prefer HTTP over CLI
import urllib.request, json
req = urllib.request.Request(
    "http://127.0.0.1:8767/recall",
    data=json.dumps({"query": text, "namespace": ns, "limit": 5}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=5).read())
```

This is 50x faster (59ms vs 3s) and produces consistent scores.

## Hook Auto-Recall Behavior — DEPRECATED

> ⚠️ **Mode A (hooks) is superseded by Mode B (memory-provider) since v0.5.0.**
> All 6 agents migrated to Mode B on June 28, 2026. See `references/hermes-mode-b-setup.md`.
> The hooks below (`uteke-recall`, `working-memory`) have been REMOVED from all agents.

The `uteke-recall` gateway hook fired on `agent:start` and used the user's message as recall query. Historical behaviors (for reference when auditing older sessions):

1. **Too-short messages (<10 chars) were skipped** — the hook returned early without searching
2. **Generic queries returned empty** — "kondisi terakhir" or "bersihkan test data" won't match semantic memories
3. **Hook searched TWO namespaces**: `hermes-knowledge` (limit 3) then `{agent_name}` (limit 2)
4. **Output was passive** — written to `/tmp/hermes/uteke-context/{agent}.md`, NOT injected into prompt
5. **⚠️ Hook used CLI subprocess** (not HTTP) — subject to CLI vs serve inconsistency above

**Why Mode B is better**: Direct string injection (no file I/O), circuit breaker (won't block agent on failure), auto extraction on session end, no CLI vs serve inconsistency.

## `uteke import --extract` — Batch Mode (v0.6.0+)

```bash
# Batch: all .md/.txt/.jsonl in directory (v0.6.0+)
uteke import --extract --batch-dir ./skills/ --namespace cto

# Batch with recursive scan:
uteke import --extract --batch-dir ./obsidian-vault/ --recursive

# Force all files as documents (no LLM):
uteke import --batch-dir ./docs/ --as-doc

# Force all files as memories (with LLM extract):
uteke import --batch-dir ./notes/ --as-memory --extract

# Preview without storing:
uteke import --batch-dir ./knowledge/ --dry-run

# Single file (unchanged):
uteke import --extract --namespace cto file.md

# Stdin (concatenates all input as one blob — still same caveat):
cat *.md | uteke import --extract --namespace cto
```

**Auto-detection:** `.md` → Document (no LLM), `.txt`/`.jsonl` → MemoryExtract (LLM). Use `--as-doc`/`--as-memory` to override.

**Stdin caveat:** Pipe concatenates ALL files into ONE blob before extracting. For per-document extraction, use `--batch-dir` instead.

**Parallel extraction** (`--extract-parallel N`, max 10): Available in CLI but sequential implementation deferred to v0.6.1. Currently all files processed sequentially regardless of this flag.

**BatchResult tracks `skipped_files` and `skipped_facts` separately** — `skipped_files` = files that couldn't be processed (e.g., no `--extract` for `.txt` files), `skipped_facts` = individual facts skipped during LLM extraction within a successfully processed file. Do NOT conflate with `ImportResult.skipped` which is fact-level only.

**`--extract-model` defaults:** config's `[extraction] model` → `UTEKE_EXTRACTION_MODEL` env → `OPENAI_API_KEY`. For FreeModel, explicitly set `--extract-model gpt-5.4-mini --extract-base-url https://api.freemodel.dev/v1 --extract-api-key <CORA_API_KEY>`.

## Patch Tool + Struct Field Renaming Pitfall

When renaming a struct field with Hermes `patch` tool using `replace_all`, it catches ALL matching strings — even across different structs with the same field name. This caused a cascade bug in this session:

**Scenario:** `BatchResult.skipped` renamed to `skipped_files` + `skipped_facts`. Used `replace_all` on `result.skipped` → also caught `ImportResult.skipped` (which should stay unchanged).

**Fix pattern:** When two structs share a field name and only one is being renamed:
1. First use targeted `replace_all` on the DISAMBIGUATED form (`result.skipped_files`, `result.skipped_facts`)
2. Then fix remaining references individually with context-aware patches
3. Verify with `grep -n "field_name"` before building

**Better approach:** Instead of `replace_all`, rename the struct's init block (which is unique due to struct name + field list) first, then update usages one at a time. Counter-intuitively, MORE patch calls with MORE context is safer than fewer `replace_all` calls.
