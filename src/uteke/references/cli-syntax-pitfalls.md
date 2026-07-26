# Uteke CLI Syntax Pitfalls

## Positional Args, NOT Flags (CRITICAL)

The #1 mistake: treating content/query as named flags. They are **positional**.

```bash
# ✅ CORRECT — content/query is positional
uteke remember "content to remember" --tags "tag1,tag2" --namespace cto
uteke recall "query text" --namespace cto --limit 3
uteke search "keyword" --namespace cto

# ❌ WRONG — these will error with "unexpected argument"
uteke remember --content "content to remember"
uteke recall --query "query text"
uteke search --keyword "keyword"
```

Error message when wrong: `error: unexpected argument '--content' found`

## Quick Command Reference

| Command | Syntax | Output |
|---------|--------|--------|
| Remember | `uteke remember "content" --tags "t1,t2" --namespace ns --type fact` | Memory ID |
| Recall | `uteke recall "query" --namespace ns --limit 5` | Ranked results |
| Search | `uteke search "keyword" --namespace ns` | Text matches |
| Get | `uteke get <UUID>` | Single memory |
| Forget | `uteke forget <UUID>` | Delete |
| Stats | `uteke stats` | Store statistics |
| List | `uteke list --namespace ns --tags tag1` | Filtered list |
| Doctor | `uteke doctor` | Health check |
| Import | `uteke import <file> --extract --namespace ns` | Batch import |

## Optional Flags (shared across commands)

- `--namespace <name>` — agent isolation (default: "default")
- `--tags "tag1,tag2"` — comma-separated tags
- `--type <type>` — fact, procedure, preference, decision, context, note, insight, reference, event (default: fact with auto-inference)
- `--source <src>` — provenance URL/path
- `--source-type <type>` — user, url, file, import, derived, system, unknown
- `--json` — JSON output instead of formatted text
- `--store <path>` — override store path
- `--entity <name>` — entity identifier
- `--category <name>` — category classification
- `--meta "key:value,key2:value2"` — arbitrary metadata
- `--room <id>` — room for collaborative context
- `--author <name>` — author attribution in room
- `--detect-contradiction` — auto-deprecate conflicting memories
- `--verbose` — verbose logging

## Embedding & Extraction Config

All config in `~/.uteke/uteke.toml`:
- `[extraction]` — model, base_url, api_key, endpoint_path
- `[embedding]` — backend (onnx/modal), api_key

**Do NOT rely on env vars** for API keys. Set in toml. Resolution: CLI flag → toml → OPENAI_API_KEY → ZAI_API_KEY.
