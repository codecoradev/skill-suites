# Uteke HTTP Server API

> Last verified: v0.10.1. Source-verified from `handlers.rs`.

## Setup

```bash
uteke serve --port 8767 --auth-token <token>
export UTEKE_BASE_URL=http://localhost:8767
export UTEKE_TOKEN=<token>
export UTEKE_NAMESPACE=default  # per-agent namespace
```

Server options: `--auth-token`, `--read-only-token`, `--cors-origin`

## Full Endpoint Map

### Core Memory
```
POST /remember              → { content, tags[], namespace?, type?, detect_contradiction? } → { id }
POST /recall                → { query, limit?, tags[], namespace?, min_score?, strict?, search_type?, enrich? }
                            → [{memory:{id,content,tags,metadata,...}, score:N}]
GET  /memory?id=UUID        → { id, content, tags, metadata, namespace, memory_type, importance, pinned }
PUT  /memory                → { id, content?, tags?, metadata?, importance?, pinned?, memory_type? } → { updated: id }
DELETE /forget?id=UUID      → { forgotten }
DELETE /forget?tag=TAG&namespace=NS → { deleted }
GET  /health                → { status, version, memories, namespaces }
```

### Feedback & Pinning
```
POST /memory/feedback       → { id, feedback: "helpful"|"unhelpful" } → { delta, importance, id }
POST /memory/pin            → { id, pinned: bool } → { memory }
```

### Stats & Namespaces
```
GET  /stats                 → { stats }  (?namespace=)
GET  /namespaces            → [namespaces]
GET  /recent                → [recent memories]  (?namespace=, ?limit=)
GET  /graph                 → { graph data }  (?namespace=)
POST /graph/edge            → { source_id, target_id, relation, metadata? } → { edge }
DELETE /graph/edge          → { source_id, target_id } → { deleted }
```

### Room Operations
```
POST /room/create           → { room_id, title?, namespace? } → { created, namespace }
POST /room/remember         → { room_id, content, tags[], namespace?, type?, author } → { id, room_id }
GET  /room/list             → [rooms]
POST /room/recall           → { room_id, query, limit?, author?, min_score? } → [results]
POST /room/summary          → { room_id } → { summary }
POST /room/stats            → { room_id } → { room stats }
DELETE /room/delete         → { room_id } → { deleted }
```

### Room ↔ Document Junction
```
PUT    /room/document/add    → { room_id, doc_slug } → { status: "linked" }
POST   /room/document/list   → { room_id } → { room_id, doc_slugs: [] }
DELETE /room/document/remove → { room_id, doc_slug } → { status: "unlinked" }
POST   /doc/room/list       → { doc_slug } → { doc_slug, room_ids: [] }
POST   /doc/mem-refs        → { doc_slug } → memories referencing this doc via [[wikilinks]]
POST   /memory/:id/doc-refs → documents referenced by this memory's [[wikilinks]]
```

### Context & Dream
```
POST /context               → { namespace? } → { context }
POST /dream                 → { namespace?, dry_run?, phases? } → { dream report }
POST /mcp                   → JSON-RPC 2.0 (1 MiB limit)
```

### Documents
```
POST /doc/create            → { slug, title?, content, tags[], namespace?, parent? } → { id, slug }
POST /doc/get               → { id | slug, namespace? } → { document }
POST /doc/list              → { namespace?, limit?, roots_only?, parent? } → [docs]
POST /doc/search            → { query, limit?, namespace?, mode? } → [results]
POST /doc/move              → { id | slug, new_parent?, namespace? } → { moved }
POST /doc/update            → { id | slug, title?, content?, tags?, metadata? }
DELETE /doc/delete?id=UUID
DELETE /doc/delete?slug=SLUG
```

### Tags & Namespaces
```
GET    /tags/list           → [tags]
GET    /namespace/list      → [namespaces]
GET    /namespace/stats     → { stats }
```

## Known API Issues

| # | Issue | Workaround |
|---|-------|-----------|
| 56 | `/remember` drops custom `metadata`/`entity` field | Direct SQLite insert for structured metadata |
| 56a | `/remember` doesn't set `memory_type` column from `type` param | Use `PUT /memory` after creation |
| 57 | Container mutex serializes ALL requests | Add `--max-time 10` to curl calls |
| 733 | `PUT /room/document/add` empty body on validation error | Verify with `POST /room/document/list` |
| 734 | `trust_score` not exposed in GET /memory response | Track via importance delta from feedback |

### meta Field Bug

`RememberRequest` struct lacks `meta`/`metadata`/`entity`/`category` fields. Metadata is auto-built only from `type` + `valid_from` + `valid_until`. CLI `--meta` works (writes to DB directly), HTTP handler does not pass custom metadata.

| What you send | What gets stored |
|---|---|
| `meta: "platform:threads"` | `null` (field not in struct) |
| `type: "event"` | `{"type": "event"}` (auto-generated) |

### recall Response Format Change (v0.7→v0.8)

v0.7.x returned flat `[{id, content, tags, score}]`. v0.8.0 wraps: `[{memory: {id, content, ...}, score: N}]`. Update parsers accordingly.

## curl Examples

```bash
# Remember
curl -sf -X POST http://localhost:8767/remember \
  -H "Authorization: Bearer $UTEKE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Deploy v2.1","tags":["deploy"],"namespace":"ops"}'

# Recall
curl -sf -X POST http://localhost:8767/recall \
  -H "Authorization: Bearer $UTEKE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"deploy timeline","limit":3,"namespace":"ops"}'

# Room recall
curl -sf -X POST http://localhost:8767/room/recall \
  -H "Authorization: Bearer $UTEKE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"room_id":"project-hub","query":"deadline"}'
```
