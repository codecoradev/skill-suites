# Uteke CLI Pitfalls — Production-Tested

Patterns discovered from active use. Updated July 2026.

## `uteke remember` — Stdin Pipe Does NOT Work

`cat file | uteke remember -` stores literal `"-"` instead of reading stdin. `<CONTENT>` is positional.

```bash
# Wrong
echo "test" | uteke remember --namespace test -
# Right
uteke remember --namespace test "test content"

# For long content, use Python:
import subprocess
subprocess.run(["uteke", "remember", "--namespace", "ns", "content"], timeout=30)
```

## `uteke recall --json` — Line Numbers in Content

Normal recall prepends line numbers: `"content": "1|[text]\n2|[more]"`. Room recall does NOT. Strip `"N|"` prefixes when parsing recall JSON.

## Vector Index Desync — Memories Invisible to Search

Memories can exist in SQLite but have NO embedding, invisible to `uteke recall`.

Symptoms:
- Room has N memories but recall finds fewer
- Recently remembered items don't appear in search

Diagnosis:
```bash
uteke stats --namespace myns   # shows correct count
uteke recall --namespace myns "query" --limit 50  # returns fewer
```

Fix: `uteke repair --namespace myns` to regenerate missing embeddings.

## Bulk Noise Cleanup via Direct SQLite

When room accumulates noise (test memories, duplicates), bulk-delete via SQLite:

```python
import sqlite3
conn = sqlite3.connect("~/.uteke/uteke.db")
# Delete by tag pattern
conn.execute("DELETE FROM memories WHERE namespace=? AND tags LIKE ?", ("room", "%test%"))
conn.commit()
# Then repair
subprocess.run(["uteke", "repair", "--namespace", "room"])
```

## `uteke forget` — Positional ID + Confirm Flag

```bash
# Wrong
uteke forget --id abc-123
# Right
uteke forget abc-123 --confirm
```

## Room Commands — `--room` is Positional

```bash
# Wrong
uteke room remember --room myroom "content"
# Right
uteke room remember myroom "content"
uteke room recall myroom "query" --limit 5
```

## `doc create` — Slug is Positional

```bash
# Wrong
uteke doc create --slug my-doc --title "Title" --content "..."
# Right
uteke doc create my-doc --title "Title" --content "..."
```

## `doc delete` by ID Only

```bash
uteke doc delete --id <uuid>   # Works
uteke doc delete --slug my-doc  # Does NOT work
```

## CLI Timeout When Server Holds Lock

If uteke-serve is running, CLI commands can timeout waiting for DB lock. Use HTTP API instead: `curl -X POST http://localhost:8767/recall ...`

## Multiple uteke Processes Cause SQLite Lock Contention

Running local `uteke-serve` + CLI processes simultaneously locks the DB. Only one uteke process should access the DB at a time.

Diagnosis: `pgrep -fa uteke` — look for multiple PIDs.
Fix: `pkill -f uteke` then restart server.

## `uteke recall` vs `uteke doc search` — Separate Systems

Recall searches memories (flat namespace). Doc search searches document tree. A memory referencing a doc via `[[wikilink]]` does NOT make the doc content searchable via recall.

## Content Limit 10K Characters

`uteke remember` truncates content beyond ~10K chars. For longer content, split into multiple memories or use the HTTP API with direct SQLite as fallback.

## First Run Downloads 188MB Embedding Model

Lazy-loaded on first embedding operation. ~20ms for non-embedding commands (remember without search, stats, list).
