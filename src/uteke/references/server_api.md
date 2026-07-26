# Uteke HTTP Server API

> **Last verified:** v0.9.0 (2026-07-21). Source: `handlers.rs` (1832 lines).
> See SKILL.md "Breaking Changes" section for v0.7→v0.8 migration notes.
> **⚠️ API versioning (`/api/v1/`, `/api/v2/`) requires container restart after release.** Health reports correct version but versioned routes return 404 until container pulls new image. Validate with: `curl -sf -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"query":"test","limit":1}' http://localhost:8767/api/v2/recall`

## Daemon Setup
```bash
# Docker on Oracle (production) — one server only, NO local uteke-serve
# Access via /etc/hosts: uteke → 192.168.48.6
curl -s -H "Authorization: Bearer $UTEKE_TOKEN" http://localhost:8767/health

# All agents configured via .env:
#   UTEKE_BASE_URL=http://localhost:8767
#   UTEKE_TOKEN=<shared token>
#   UTEKE_NAMESPACE=<profile_name>
```

Server options: `--auth-token`, `--read-only-token`, `--cors-origin`

## Source of Truth: Domain vs Docker Internal (Jul 2026)

**Two valid access paths:**

| Path | URL | When to use |
|------|-----|-------------|
| **Domain (Traefik)** | `https://uteke.localhost/` | From any VM/client. Always requires `Authorization: Bearer $UTEKE_TOKEN`. |
| **Docker internal** | `http://localhost:8767` | From Docker network only (other containers, CI runners). May not be reachable from VM localhost. |

**⚠️ `http://localhost:8767` / `http://127.0.0.1:8767` — DO NOT USE.** Local uteke-serve binary must NEVER run on the VM (causes DB lock contention, zombie processes, dual-store problems). The Docker container on the host is the only valid uteke-serve instance.

**Env vars:**
```bash
UTEKE_BASE_URL=https://uteke.localhost  # or http://localhost:8767 for Docker-internal
UTEKE_TOKEN=<token>
UTEKE_NAMESPACE=<profile_name>  # optional, per-agent
```

**Hooks architecture (Jul 2026):** Both `uteke-extract` and `uteke-recall` hooks use `urllib.request` to `$UTEKE_BASE_URL` with Bearer auth. No local CLI dependency.

## Full Endpoint Map (v0.8.0, source-verified)

### Core Memory Operations
```
POST /remember              → { content, tags[], namespace?, type?, valid_from?, valid_until?, detect_contradiction? } → { id }
POST /recall                → { query, limit?, tags[], namespace?, entity?, category?, min_score?, strict?, at?, search_type?, enrich? }
                            → [{memory:{id,content,tags,metadata,...}, score:N}]  ⚠️ WRAPPED in v0.8.0 (was flat in v0.7.x)
GET  /memory?id=UUID        → { id, content, tags, metadata, namespace, memory_type, importance, pinned, ... }  (flat, unchanged)
PUT  /memory                → { id, content?, tags?, metadata?, importance?, pinned?, memory_type? } → { updated: id }  🆕 v0.8.0
DELETE /forget?id=UUID      → { forgotten }
DELETE /forget?tag=TAG&namespace=NS → { deleted }  (bulk delete by tag)
GET  /health                → { status, version, memories, namespaces }
```

### Feedback & Pinning (v0.8.0)
```
POST /memory/feedback       → { id, feedback: "helpful"|"unhelpful" } → { delta, importance, id }  🆕 v0.8.0
POST /memory/pin            → { id, pinned: bool } → { memory }  🆕 v0.8.0
```

### Stats & Namespaces
```
GET  /stats                 → { stats }  (?namespace= optional)
POST /stats                 → { namespace? } → { stats }
GET  /namespaces            → [namespaces]
GET  /recent                → [recent memories]  (?namespace=, ?limit=)
GET  /graph                 → { graph data }  (?namespace= optional)
POST /graph/edge            → { source_id, target_id, relation, metadata? } → { edge }
DELETE /graph/edge          → { source_id, target_id } → { deleted }
```

### Room Operations
```
POST /room/create           → { room_id, title?, namespace? } → { created, namespace }
POST /room/remember         → { room_id, content, tags[], namespace?, type?, metadata?, author } → { id, room_id }  🆕 v0.10.0
GET  /room/list             → [rooms]
POST /room/recall           → { room_id, query, limit?, author?, min_score? } → [results]
POST /room/summary          → { room_id } → { summary }
POST /room/document         → { room_id } → { room summary document }  (NOT a junction endpoint!)
POST /room/stats            → { room_id } → { room stats }
DELETE /room/delete         → { room_id } → { deleted }
```

### Room ↔ Document Junction (v0.8.0, #689)
```
PUT    /room/document/add    → { room_id, doc_slug } → { status: "linked", ... }  🆕
POST   /room/document/list   → { room_id } → { room_id, doc_slugs: [] }  🆕
DELETE /room/document/remove → { room_id, doc_slug } → { status: "unlinked" }  🆕
POST   /doc/room/list       → { doc_slug } → { doc_slug, room_ids: [] }  🆕
POST   /doc/mem-refs        → { doc_slug } → memories referencing this doc via [[wikilinks]]  🆕
POST   /memory/:id/doc-refs → documents referenced by this memory's [[wikilinks]]  🆕
```

### Context & Dream
```
POST /context               → { namespace? } → { context }
POST /dream                 → { namespace?, dry_run?, phases? } → { dream report }
POST /mcp                   → JSON-RPC 2.0 (1 MiB limit)
```

### Document Operations
```
POST /doc/create            → { slug, title?, content, tags[], namespace?, parent? } → { id, slug }
POST /doc/get               → { id | slug, namespace? } → { document }
POST /doc/list              → { namespace?, limit?, roots_only?, parent? } → [docs]
POST /doc/search            → { query, limit?, namespace?, mode? } → [results]
POST /doc/move              → { id | slug, new_parent?, namespace? } → { moved }
POST /doc/update            → { id | slug, title?, content?, tags?, metadata? } (partial update)
DELETE /doc/delete?id=UUID
DELETE /doc/delete?slug=SLUG
```

### ⚠️ Known API Issues

| # | Issue | Severity | Workaround |
|---|-------|----------|-----------|
| **56** | `/remember` drops custom `meta`/`metadata`/`entity` field | Medium | Direct SQLite insert for structured metadata |
| **56a** | `/remember` doesn't set `memory_type` column from `type` param | Low | Direct SQLite or `PUT /memory` after creation |
| **57** | Container Mutex serializes ALL requests | Medium | Add `--max-time 10` to all curl calls |
| **#733** | `PUT /room/document/add` returns empty body on validation error | Medium | Verify with `POST /room/document/list` |
| **#734** | `trust_score` not exposed in GET /memory response | Low | Track via importance delta from feedback |
| **#735** | `POST /room/document` confused with junction routes | Low | Use `PUT /room/document/add` for linking |

### ⚠️ `meta` Field Bug — API Drops Custom Metadata (source-verified Jul 14 2026)

**Root cause (exact):** `RememberRequest` struct in `main.rs:98-113` does NOT have `meta`, `metadata`, `entity`, `category`, `importance`, or `slug` fields. Metadata auto-built only from `type` + `valid_from` + `valid_until` (line 606-620). The `uteke.remember()` core function DOES accept `metadata: Option<Value>` — but the HTTP handler never passes custom metadata to it.

| What you send | What gets stored in `memories.metadata` |
|---|---|
| `meta: "platform:threads,likes:45"` | `null` (field not in struct) |
| `type: "event"` (no meta) | `{"type": "event"}` (auto-generated from `r#type`) |
| `type: "insight"` (no meta) | `{"type": "insight"}` (auto-generated) |

**Bug 56a:** `memory_type` column always `fact`. `r#type` param only affects auto-metadata `{"type":"event"}`, not the `memory_type` SQL column. `uteke.remember()` core function sets `memory_type` separately, but the HTTP handler calls `uteke.remember(content, tags, metadata, namespace)` which doesn't set memory_type from `r#type`.

**Evidence:** Direct SQLite query confirms. CLI memories with `--meta` or `--entity` DO have custom metadata → DB schema supports it, HTTP handler doesn't pass it.

### ⚠️ HTTP-First Priority (Jul 2026)

**Always try HTTP API before SQLite.** Container API and host SQLite share the same DB file. HTTP is preferred because:
1. Embeddings generated server-side (semantic search works immediately)
2. No lock contention with running uteke-serve
3. Auth/token handled uniformly

**Fallback to direct SQLite only when:**
- HTTP endpoint has documented bug (e.g., `DELETE /doc/delete` query param bug — #776)
- Custom metadata needed (pitfall #56 — `/remember` drops `meta`)
- Room junction row needed (pitfall #56 — `/remember` with `room_id` silently fails)
- Bulk operations faster via SQL batch

### ⚠️ Data Limitations
- **`/remember` can't set entity/category/importance at creation time** — use `PUT /memory` after creation (v0.8.0) or CLI `--entity`/`--importance`.
- **entity/category filter**: Fixed in v0.8.0 (#667) — pushed into core recall candidate loop, no more 10x fetch overhead.
- **`/room/remember` (v0.10.0+)**: Use this to store AND link to room in one call. `{room_id, content, tags[], namespace?, type?, metadata?, author}`. Plugin (tool.py) still broken — sends to `/remember` instead (GitHub #783). Use direct curl or `execute_code`.
- **`/forget` uses DELETE method**: May timeout under Mutex contention — use direct SQLite DELETE as fallback.

### Dual-Write Pattern: SQLite Structured + API Semantic (verified Jul 14 2026)

Since the container API drops custom metadata but correctly **reads and exposes** metadata stored via direct SQLite, use dual-write for structured data use cases (social media tracking, CRM, analytics):

**Write:** Direct SQLite insert with full metadata JSON + memory_tags rows.
**Read/Search:** Container API `/recall` (semantic) or `/list` (tag filter) — both expose metadata correctly.

```python
import sqlite3, json, uuid, datetime

DB_PATH = "~/.uteke/uteke.db"
now = datetime.datetime.now(datetime.timezone.utc).isoformat()

def uteke_store(content, tags, metadata, namespace="cmo", memory_id=None):
    """Store memory with custom metadata via direct SQLite — bypasses API meta bug."""
    mem_id = memory_id or str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    # Insert memory with structured metadata
    conn.execute("""
        INSERT INTO memories (id, content, tags, metadata, namespace, memory_type, 
                               importance, created_at, updated_at, source_type)
        VALUES (?,?,?,?,?,?,?,datetime('now'),datetime('now'),'user')
    """, (mem_id, content, json.dumps(tags), json.dumps(metadata), namespace, "fact", 0.5))
    # Insert individual tags for FTS5 + tag-based filtering
    for tag in tags:
        conn.execute("INSERT OR IGNORE INTO memory_tags (memory_id, tag) VALUES (?,?)", (mem_id, tag))
    conn.commit()
    conn.close()
    return mem_id

# Example: social media post with structured metadata
post_id = uteke_store(
    content="@codecoradev — DrawOver v1.0 launch — 45 likes, 12 replies",
    tags=["social-post", "threads", "codecoradev"],
    metadata={
        "platform": "threads",
        "account": "codecoradev", 
        "post_id": "THR-001",
        "status": "published",
        "likes": 45,
        "replies": 12,
        "date": "2026-07-14"
    }
)
```

Then read via API — metadata IS exposed:
```python
# /list returns full metadata from SQLite
POST /list {"tag":"social-post","namespace":"cmo"}
# → [{"id":"...","content":"...","metadata":{"platform":"threads","account":"codecoradev",...}}]
```

**Key insight:** Container API and local SQLite share the SAME database (volume `uteke-data` at `/data/uteke.db` inside container, mounted at `~/.uteke/uteke.db` on host). Changes via either path are immediately visible to both.

### SQLite Schema Reference (for direct access)

```sql
-- memories table (17K+ rows)
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding BLOB,           -- vector (768d)
    tags TEXT,                -- JSON array: '["tag1","tag2"]'
    metadata TEXT,            -- JSON object: '{"key":"value"}' — ARBITRARY!
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    namespace TEXT NOT NULL DEFAULT 'default',
    access_count INTEGER NOT NULL DEFAULT 0,
    last_accessed TEXT,
    deprecated INTEGER NOT NULL DEFAULT 0,
    valid_from TEXT,
    valid_until TEXT,
    memory_type TEXT NOT NULL DEFAULT 'fact',
    importance REAL NOT NULL DEFAULT 0.5,
    pinned INTEGER NOT NULL DEFAULT 0,
    content_type TEXT NOT NULL DEFAULT 'text',
    slug TEXT,
    source TEXT,
    source_type TEXT NOT NULL DEFAULT 'user'
);

-- FTS5 index for keyword search
CREATE VIRTUAL TABLE memories_fts USING fts5(content, tags, namespace, content='memories');

-- Separate tag index (faster than JSON parsing)
CREATE TABLE memory_tags (memory_id TEXT NOT NULL, tag TEXT NOT NULL, PRIMARY KEY (memory_id, tag));

-- Rooms
CREATE TABLE rooms (id TEXT PRIMARY KEY, title TEXT, namespace TEXT NOT NULL DEFAULT 'default', 
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE room_memories (room_id TEXT NOT NULL, memory_id TEXT NOT NULL, 
                            author TEXT NOT NULL DEFAULT 'unknown', role TEXT NOT NULL DEFAULT 'participant',
                            joined_at TEXT NOT NULL, PRIMARY KEY (room_id, memory_id));
```

### Alternative: Direct SQLite Access
When API routes are broken or insufficient, query SQLite directly:
```python
import sqlite3
conn = sqlite3.connect("~/.uteke/uteke.db")
# Get memory by ID
mem = conn.execute("SELECT * FROM memories WHERE id = ?", (mem_id,)).fetchone()
# Get room memories
rows = conn.execute("SELECT m.* FROM memories m JOIN room_memories rm ON m.id = rm.memory_id WHERE rm.room_id = ?", (room_id,)).fetchall()
# Query by metadata JSON (SQLite json functions)
rows = conn.execute("SELECT id, content, metadata FROM memories WHERE json_extract(metadata, '$.platform') = 'threads' AND namespace = 'cmo'",).fetchall()
conn.close()
```

### Container API Quick Reference
```bash
# Health check
curl -sf http://localhost:8767/health

# Remember with tags (meta is ignored — use SQLite for structured data)
curl -s -H "Authorization: Bearer $UTEKE_TOKEN" -H "Content-Type: application/json" \
  $UTEKE_BASE_URL/remember -d '{"content":"...","tags":["tag1"],"namespace":"cmo"}'

# Semantic recall (v0.8.0: wrapped response [{memory:{...}, score}])
curl -s -H "Authorization: Bearer $UTEKE_TOKEN" -H "Content-Type: application/json" \
  $UTEKE_BASE_URL/recall -d '{"query":"...","namespace":"cmo","limit":5}'

# Partial update (v0.8.0)
curl -s -X PUT -H "Authorization: Bearer $UTEKE_TOKEN" -H "Content-Type: application/json" \
  $UTEKE_BASE_URL/memory -d '{"id":"<uuid>","tags":["new-tag"],"importance":0.8}'

# Trust feedback (v0.8.0)
curl -s -H "Authorization: Bearer $UTEKE_TOKEN" -H "Content-Type: application/json" \
  $UTEKE_BASE_URL/memory/feedback -d '{"id":"<uuid>","feedback":"helpful"}'

# List by tag
curl -s -H "Authorization: Bearer $UTEKE_TOKEN" -H "Content-Type: application/json" \
  $UTEKE_BASE_URL/list -d '{"tag":"social-post","namespace":"cmo"}'

# Room document (most reliable room read method)
curl -s -H "Authorization: Bearer $UTEKE_TOKEN" -H "Content-Type: application/json" \
  $UTEKE_BASE_URL/room/document -d '{"room_id":"my-room"}'

# Link doc to room (v0.8.0)
curl -s -X PUT -H "Authorization: Bearer $UTEKE_TOKEN" -H "Content-Type: application/json" \
  $UTEKE_BASE_URL/room/document/add -d '{"room_id":"my-room","doc_slug":"my-doc"}'
```

**Tags format**: JSON array `["tag1", "tag2"]` (NOT comma-separated string).

## Tag Management API (v0.6.6, #566)
```
GET  /tags                  → [tags with counts]
POST /tags/rename            → { old_name, new_name }
POST /tags/delete            → { name }
```

## Pin API
```
POST /memory/pin            → { id, pinned: bool }  (v0.8.0, #660)
GET  /memory?id=UUID        → check pinned field in response
```

## Timeline & Edges API (v0.6.6, #566)
```
GET  /timeline?id=UUID       → [timeline events]
GET  /edges?id=UUID          → [edges] (?direction=both|incoming|outgoing)
POST /graph/edge             → { source_id, target_id, relation, metadata? }
DELETE /graph/edge           → { source_id, target_id }
```

## Room Memories API (v0.6.7, #569)
```
GET  /room/memories?room_id= → [memories in room]
```

## Document API (v0.4.0)
```
POST /doc/create          → { slug, content, title?, tags?, parent?, namespace? }
POST /doc/get              → { id | slug, namespace? }
POST /doc/list             → { namespace?, limit?, roots_only?, parent? }
POST /doc/search            → { query, mode? (hybrid|semantic|fts), namespace?, limit? }
POST /doc/move              → { id | slug, new_parent?, namespace? }
POST /doc/update            → { id | slug, title?, content?, file?, tags?, metadata? } (partial update, #589)
DELETE /doc/delete?id=UUID
```

### ⚠️ Auth Required for Write Endpoints
ALL write endpoints (`/remember`, `/doc/create`, `/doc/update`, `/doc/delete`, `/room/create`, etc.) require `Authorization: *** from `UTEKE_TOKEN` in `.env`). Without it: `500 Internal Server Error` or silent failure. GET endpoints (`/health`, `/room/list`, `/doc/search`) work without auth.

### Doc Create vs Doc Update — Different Workarounds Needed
- **`POST /doc/create`** — WORKS in v0.10.0+ with auth token. (Was broken in v0.7 — pitfall #17.)
- **`POST /doc/update`** — WORKS with auth token. Pass `{"slug": "...", "content": "...", "tags": [...]}` with `Authorization: *** the preferred way to update existing docs when uteke-serve is running (no lock contention, no SQLite direct access needed).

### ⚠️ Room Remember via REST API — Plugin Still Broken (v0.10.0, GitHub #783)
`POST /room/remember` (v0.10.0+) works correctly: `{room_id, content, tags[], namespace?, type?, metadata?, author}` → `{id, room_id}`. Creates both the memory AND the `room_memories` junction row.

**However**, the Hermes uteke-tool plugin (tool.py) still sends `room_remember` and `room_document` actions to `POST /remember` (wrong endpoint) with `room` field (wrong field name — should be `room_id`). Serde silently ignores the `room` field → no junction row created. 903/1,939 memories (46.6%) orphaned.

**Correct workaround — direct curl:**
```bash
curl -X POST https://uteke.localhost/room/remember \
  -H "Authorization: Bearer $UTEKE_TOKEN" -H "Content-Type: application/json" \
  -d '{"room_id":"my-room","content":"...","author":"COO","namespace":"coo","tags":["tag1"]}'
```

**Or via execute_code (Python urllib):**
```python
import json, urllib.request
req = urllib.request.Request(
    "https://uteke.localhost/room/remember",
    data=json.dumps({"room_id":"my-room","content":"...","author":"COO","namespace":"coo"}).encode(),
    headers={"Authorization":"Bearer TOKEN","Content-Type":"application/json"},
    method="POST"
)
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())  # {"id":"...","room_id":"my-room"}
```

**8 plugin endpoint mismatches documented in GitHub #783** (Jul 26, 2026):
| Plugin Action | Plugin Sends | Correct | Bug |
|---|---|---|---|
| `room_remember` | `POST /remember` with `room` | `POST /room/remember` with `room_id` | Room link silently dropped |
| `room_document` | `POST /remember` with `room` | `POST /room/remember` with `room_id` | Same as above |
| `namespace_list` | `GET /namespace/list` | `GET /namespaces` | 404 |
| `namespace_stats` | `GET /namespace/stats?ns=` | `GET /stats?namespace=` | 404 |
| `tags_list` | `GET /tags/list` | `GET /tags` | 404 |
| `tags_delete` | `DELETE /tags/delete?tag=` | `POST /tags/delete` with body `{tag}` | Wrong method + 404 |
| `import` | `POST /import` with `{"data":...}` | `POST /import` with `{"content":...}` | Wrong field name |
| `consolidate` | `POST /consolidate?threshold=X` | `POST /consolidate` JSON body | Query params instead of body |

## Performance (v0.4.2, Oracle ARM, 274 memories)
| Operation | Latency |
|-----------|---------|
| POST /remember (cold) | ~2.1s |
| POST /remember (warm) | ~60ms |
| POST /recall | ~37ms |
| POST /stats, GET /health | ~7ms |
| Memory (VmRSS) | 418 MB |

## Remote Embedding Backend
```toml
[embedding]
backend = "openai"
model = "gemma-768"
base_url = "https://<url>.modal.run"
api_key = "<key>"
dims = 768
max_seq_length = 2048
endpoint_path = "/embeddings"
```

Config resolution: CLI args > project toml > global toml > ENV > defaults

## Full ENV Vars
| ENV Var | Config Path |
|---------|-------------|
| `UTEKE_EMBEDDING_BACKEND` | embedding.backend |
| `UTEKE_EMBEDDING_MODEL` | embedding.model |
| `UTEKE_EMBEDDING_API_KEY` | embedding.api_key (falls back to OPENAI_API_KEY) |
| `UTEKE_EMBEDDING_BASE_URL` | embedding.base_url |
| `UTEKE_EMBEDDING_ENDPOINT_PATH` | embedding.endpoint_path |
| `UTEKE_EMBEDDING_DIMS` | embedding.dims |
| `UTEKE_MAX_SEQ_LENGTH` | embedding.max_seq_length |
| `UTEKE_SERVER_HOST/PORT` | server.host/port |
| `UTEKE_RECALL_MIN_SCORE` | recall.min_score |
| `UTEKE_RECALL_STRATEGY` | recall.default_strategy |

## Cross-Embedding Compatibility
| Condition | Cosine | Verdict |
|-----------|--------|---------|
| Same model, same pooling, same max_seq | 0.9996 | ✅ Identical |
| Same model, diff max_seq (256 vs 2048) | 0.42 | ❌ |
| Naive mean pool | 0.42 | ❌ |

Free-switch: set max_seq=2048 → repair → doctor → switch backend.

## Dual-DB Architecture
| DB Path | Role |
|---------|------|
| `~/home/.uteke/uteke.db` | CLI default ($HOME/.uteke) |
| `~/.uteke/uteke.db` | Hermes MemoryProvider (uteke.json uteke_home) |

⚠️ Container and host share the SAME database: Docker volume `uteke-data` maps to `/data/uteke.db` inside container = `~/.uteke/uteke.db` on host. Direct SQLite writes from host are immediately visible via container API.

Audit: `uteke verify` + `uteke repair` for BOTH DBs.

## Upgrade Procedure
```bash
VERSION=v0.5.0 && cd /tmp && gh release download $VERSION --repo codecoradev/uteke \
  -p "uteke-aarch64-unknown-linux-gnu-${VERSION}.tar.gz" \
  -p "checksums-sha256.txt" --clobber && \
  sha256sum -c < <(grep aarch64 checksums-sha256.txt) && \
  tar xzf uteke-aarch64-unknown-linux-gnu-${VERSION}.tar.gz && \
  pgrep -f uteke-serve | xargs kill 2>/dev/null; sleep 1 && \
  cp uteke ~/.cargo/bin/ && cp uteke-serve ~/.cargo/bin/ && \
  chmod +x ~/.cargo/bin/uteke ~/.cargo/bin/uteke-serve
```
After: `uteke repair` && `uteke doctor` for both DBs.
