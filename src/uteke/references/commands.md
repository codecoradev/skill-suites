# Uteke CLI Commands Reference

## Core Commands

```bash
# Store memory — ALWAYS use --type, --namespace, --tags
uteke remember "Deploy v2.1 to staging on Friday" --tags deploy,staging --namespace cto --type decision

# ⚠️ Positional args! NOT uteke remember --content "..."

# Store with metadata enrichment
uteke remember "RevenueCat Pro dipilih untuk Usago" \
  --tags revenuecat,decision --namespace cto --type decision \
  --entity usago --category billing --meta "sdk:purchases_flutter,cost:free-under-2500"

# Store with contradiction detection
uteke remember "Updated decision: use RevenueCat Pro" \
  --tags revenuecat,decision --namespace cto --type decision --detect-contradiction

# Semantic search — unified recall (memories + docs, v0.6.4+)
uteke recall "when do we deploy?" --namespace cto
uteke recall "modal fleet" --namespace cto                # Finds memories AND doc chunks (tagged [doc] vs [memory])
uteke recall "modal fleet" --type doc                     # Search docs only
uteke recall "modal fleet" --type memory                  # Search memories only (backward compat)
uteke recall "billing" --namespace cto --entity usago
uteke recall "query" --min 0.5                            # Min similarity threshold
uteke recall "query" --strict                             # Use strict threshold from config
uteke recall "query" --context                             # AI prompt injection format
uteke recall "query" --where role=CTO                     # JSON field filter
uteke recall "query" --content-format json               # Force JSON output for content

# Text/keyword search (FTS5)
uteke search "staging" --namespace cto
uteke list --tag deploy --namespace cto
uteke stats
uteke doctor
uteke export > backup.jsonl
uteke import < backup.jsonl
```

## Room Commands (v0.0.15+)

```bash
uteke remember "SurrealDB graph relevant" --room discord:1514528701109506199 --author cto
uteke room list [--namespace cto]
uteke room stats discord:1514528701109506199
uteke room recall discord:1514528701109506199 --limit 50
uteke room recall discord:1514528701109506199 --author coo
uteke room summary usago-logo-gtm
uteke room document usago-logo-gtm
uteke room delete discord:1514528701109506199 --confirm
```

**⚠️ Room CLI syntax:** `--room` is POSITIONAL for room subcommands. Correct: `uteke room recall <ID>`. Wrong: `uteke room recall --room <ID>`.

## Graph Commands (v0.0.15+)

```bash
uteke remember "Updated" --meta "rel:supersedes:<uuid>" --namespace cto
uteke recall "billing" --namespace cto --related --depth 2
uteke graph stats --namespace cto
uteke graph nodes --namespace cto
uteke graph edges --namespace cto
uteke graph neighbors --namespace cto <label>
uteke graph path --namespace cto <from> <to>
uteke graph query --namespace cto --relation SIMILAR_TO
```

## Document Engine (v0.3.0+, hierarchical docs v0.6.1+)

```bash
# Create doc (slug is positional)
uteke doc create my-slug --title "Title" --content "# Section\nBody" --tags infra
uteke doc create my-slug --title "Title" --file notes.md --tags arch

# Create with parent (hierarchical — doc #438+)
uteke doc create child-slug --title "Child" --parent parent-slug --content "..."
uteke doc create grandchild --parent child-slug --content "..."

# Read & navigate
uteke doc get my-slug                     # Read full content
uteke doc list                           # List all root docs
uteke doc children parent-slug            # List direct children
uteke doc descendants parent-slug          # List all descendants (recursive)
uteke doc breadcrumbs child-slug          # Show path from root to doc

# Move & restructure
uteke doc move child-slug --parent new-parent-slug
uteke doc move child-slug --parent root   # Move to root level

# Search (semantic + FTS5 hybrid)
uteke doc search "modal fleet api"        # Search across all docs

# Delete (cascades to children!)
uteke doc delete <doc-uuid> --confirm

# Export all docs
uteke doc export                          # Markdown
uteke doc export --json                   # JSON with full metadata
```

### Hierarchical Doc Pattern (proven Jul 2026)

When creating structured documentation (e.g., fleet reference with sub-sections):

```
1. Create parent doc: uteke doc create modal-fleet --title "Modal Fleet" --content "Overview..."
2. Create children:   uteke doc create fleet-naming --title "Naming" --parent modal-fleet --content "..."
3. Verify structure:  uteke doc children modal-fleet
4. Navigate path:     uteke doc breadcrumbs fleet-naming
```

**Tips:**
- `--parent` accepts slug (NOT UUID). Use the slug you created.
- `doc delete` cascades — deletes all children too. Be careful with parent deletes.
- `doc search` is hybrid (FTS5 + vector RRF) — finds content across all docs.
- Maximum 1 `doc create` per terminal call (heredoc with `&` is blocked by Hermes). Batch via separate sequential calls.

⚠️ SLUG is positional. ⚠️ delete by ID only. ⚠️ recall() now searches BOTH memories AND docs (unified recall since v0.6.4+). Results are tagged `[doc]` for doc chunks and `[memory]` for memories.

**`uteke recall` unified recall (v0.6.4+):**
- `uteke recall <query>` — searches **memories + docs** (unified, RRF merged). Default `--type all`
- `uteke recall <query> --type memory` — memories only (backward compatible)
- `uteke recall <query> --type doc` — documents only
- `uteke search <query>` — FTS5 keyword text search (memories only)
- `uteke doc search <query>` — hybrid search (docs only, separate index)

## Timeline, Edges, Dream (v0.3.0)

```bash
uteke timeline <uuid> --namespace cto
uteke edges <uuid> --namespace cto
uteke edges <uuid> --deep 2 --namespace cto
uteke edges <uuid> --direction incoming --namespace cto
uteke orphans --namespace cto
uteke dream --namespace cto
```

## Recall Enhancements (v0.3.0+)

```bash
uteke recall "query" --strategy graph --namespace cto     # Graph-signal reranking
uteke recall "query" --strategy hybrid --namespace cto    # FTS5 + vector RRF
uteke recall "query" --strategy fts5 --namespace cto      # Keyword only
uteke recall "query" --salience --namespace cto           # Salience boost (importance weighting)
uteke recall "query" --recency --namespace cto            # Recency boost (freshness weighting)
uteke recall "query" --at 2026-06-01T00:00:00Z --namespace cto  # Point-in-time recall
uteke recall "query" --min 0.5 --namespace cto             # Min similarity filter
uteke recall "query" --strict --namespace cto             # Use config's min_score_strict
uteke recall "query" --context --namespace cto           # AI prompt injection format
uteke recall "query" --where role=CTO --namespace cto     # JSON field filter
uteke recall "query" --type doc --namespace cto           # Search docs only
uteke recall "query" --type memory --namespace cto        # Search memories only
uteke recall "query" --content-format json --namespace cto # Force JSON content output
```

## MCP Server (v0.0.15+)

Tools: `uteke_remember`, `uteke_recall`, `uteke_list`, `uteke_forget`, `uteke_stats`, `uteke_context`, `uteke_dream`, `uteke_room_memories` (27 tools total, v0.6.7+)
Config: `{"mcpServers":{"uteke":{"command":"uteke-mcp","args":[]}}}` (stdio) or `POST /mcp` on uteke-serve (HTTP JSON-RPC 2.0, protocol 2025-06-18)

## Memory Types

| Type | Use | Example |
|------|-----|---------|
| `fact` | Objective info (default) | "Binary at ~/.cargo/bin/uteke" |
| `decision` | Product/arch choices | "RevenueCat Pro for Usago billing" |
| `procedure` | Step-by-step workflows | "Deploy: tag→push→CI→sync" |
| `preference` | User/agent style | "user prefers minimal tool calls" |
| `context` | Temporal state | "Usago paused until device" |

## Maintenance

```bash
uteke aging status/cleanup
uteke consolidate/prune
uteke verify/repair
uteke tags list/rename/delete
uteke dream
uteke orphans
uteke pin/unpin/importance
uteke rebuild-backlinks
```

## Lifecycle

```
remember → SQLite + embed + usearch + auto-link
recall → embed query → ANN search (memories + docs) → RRF merge → ranked results
  --type all (default): unified memories + docs
  --type memory: memories only
  --type doc: documents only
  --strategy: vector | fts5 | hybrid | graph
  --salience / --recency / --related: boost signals
aging → hot(7d) → warm(30d) → cold(>30d)
dream → lint→backlinks→dedup→orphans→compact→verify
```

## Python Wrapper

```python
import subprocess, json
def uteke_remember(content, tags=None, namespace=None):
    cmd = ["uteke", "remember", content, "--json"]
    if tags: cmd += ["--tags", ",".join(tags)]
    if namespace: cmd += ["--namespace", namespace]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)
```

## TODO Tracking

```bash
uteke remember "TODO: Task desc" --tags task,pending,product,high-priority --namespace todo --type task
uteke list --namespace todo --tag pending
uteke remember "DONE: Task" --tags task,done,product --namespace todo --type task
uteke forget <old-id> --confirm
```
