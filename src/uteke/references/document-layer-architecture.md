# Document Layer + Web UI Architecture

**Last updated:** 2026-06-12 (deep analysis session)

## Overview

Uteke Document layer replaces Outline as the AI-first knowledge base. Documents are structured content (title, slug, sections with headings) written by AI agents via CLI/MCP, read by humans via shareable web links. Single data source, two interfaces.

**Core principle:** "AI writes, humans read." No rich editor, no WYSIWYG, no realtime collaboration.

## Schema v4 (Additive, Non-Destructive)

Adds two new tables to existing schema — no migration of existing data:

### `documents` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PRIMARY KEY | UUID v4 |
| `title` | TEXT NOT NULL | |
| `slug` | TEXT UNIQUE NOT NULL | URL-safe identifier |
| `namespace` | TEXT NOT NULL | Author isolation |
| `tags` | TEXT | JSON array |
| `metadata` | TEXT | JSON object |
| `status` | TEXT | draft / published |
| `version` | INTEGER | Auto-increment on update |
| `created_at` | TEXT | ISO 8601 |
| `updated_at` | TEXT | ISO 8601 |

### `document_sections` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PRIMARY KEY | UUID v4 |
| `document_id` | TEXT FK→documents | |
| `heading` | TEXT | H2/H3 section title |
| `content` | TEXT NOT NULL | Markdown body |
| `order` | INTEGER | Section sequence |
| `memory_ids` | TEXT | JSON array — links to source memory UUIDs |
| `embedding` | BLOB | 768d vector of section content |
| `created_at` | TEXT | ISO 8601 |

### Document ↔ Memory Bridge

`document_sections.memory_ids` links sections to source memories. This enables:
- Traceability: which memories contributed to which document sections
- Re-synthesis: re-embed documents from updated memories
- Semantic search: document sections auto-embedded alongside memories

## CLI Commands

```bash
uteke doc create --title "Project Brief" --slug "project-brief" [--tags "planning,startup"]
uteke doc edit --slug "project-brief" --section "Architecture" --content "..."
uteke doc list [--namespace cto] [--status draft|published]
uteke doc export --slug "project-brief" --format markdown|json
uteke doc delete --slug "project-brief" --confirm
uteke doc from-room --room discord:123 --slug "meeting-notes-jun12" --title "Meeting Notes Jun 12"
```

`from-room` is key: it synthesizes room memories into a structured document.

## API Routes (uteke-serve)

| Method | Route | Description |
|--------|-------|-------------|
| POST | /documents | Create document |
| GET | /documents | List documents |
| GET | /documents/:slug | Get document by slug |
| PUT | /documents/:slug | Update document |
| DELETE | /documents/:slug | Delete document |
| GET | /d/:slug | Public share link (HTML rendered) |
| POST | /documents/from-room | Synthesize room → document |

## MCP Tools (uteke-mcp)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `uteke_document_create` | title, slug, sections, tags | Create structured document |
| `uteke_document_export` | slug, format | Export as markdown/JSON |
| `uteke_document_list` | namespace, status | List/filter documents |
| `uteke_document_from_room` | room_id, slug, title | Synthesize room memories → document |

## Web UI (SvelteKit)

### Structure

```
uteke-web/
├── src/
│   ├── routes/
│   │   ├── +page.svelte          # Dashboard: recent docs, stats
│   │   ├── +layout.svelte        # Nav shell
│   │   └── d/[slug]/+page.svelte # Document viewer (public share)
│   ├── lib/
│   │   ├── Document.svelte        # Markdown rendered view
│   │   └── api.ts                # uteke-serve API client
├── static/
└── svelte.config.js
```

### Deployment Modes

| Mode | Components | Use Case |
|------|-----------|----------|
| **CLI only** | `uteke` binary | Local dev, agents |
| **CLI + API** | `uteke` + `uteke-serve` | Agent fleet, API access |
| **Full** | `uteke` + `uteke-serve` + Web UI | Self-hosted, human viewing |

Web files are external (Docker volume), NOT embedded in binary. This preserves single-binary value prop for CLI-only mode.

### Docker Compose

```yaml
services:
  uteke-serve:
    image: codecoradev/uteke:latest
    command: uteke-serve --host 0.0.0.0 --port 8767 --data /data
    volumes:
      - uteke-data:/data
      - ./web:/opt/uteke/web  # SvelteKit build output
    ports:
      - "8767:8767"
```

## Why Not Tasks in Uteke?

Task lifecycle (assignee, status, priority, due dates, dependencies) has fundamentally different data model than memories:

| Dimension | Memory | Task |
|-----------|--------|------|
| Mutability | Append-only (immutability preferred) | Highly mutable (status changes) |
| Lifecycle | Remember → recall → forget | Create → assign → progress → done |
| Relationships | Semantic similarity | Dependencies, blocking |
| Query pattern | "What do I know about X?" | "What's blocked? What's overdue?" |
| Data model | Content + embedding | Status + assignee + priority + dates |

**Decision: Separation of concerns.** Tasks stay in AgentBoard/Hermes. Uteke provides memory + context + documents. The "Discuss to Task" flow works via:
1. Agents discuss in Uteke Room → shared memory
2. Convert discussion to Task → stored in AgentBoard
3. Task dispatched to agent via Hermes gateway
4. Agent uses Uteke recall for context while working on task
5. Agent reports back to Room

## Versioned Roadmap

### v0.1.0 — Ship Room + MCP + Graph
- Already merged on develop (#300, #301, #302)
- Add #304 semantic room recall, #305 room summary
- Tag release

### v0.2.0 — Document Layer
- Schema v4 migration (documents + document_sections tables)
- CLI commands: doc create/edit/list/export/from-room
- MCP tools: uteke_document_create, uteke_document_export, uteke_document_list, uteke_document_from_room
- API routes on uteke-serve
- Document ↔ Memory bridge

### v0.3.0 — Web UI
- SvelteKit project (separate repo or /web subdir)
- Document viewer with shareable links (/d/:slug)
- Dashboard with recent documents
- Docker image with web files mounted
- Reverse proxy guide (Caddy/Traefik)

### v0.4.0 — Replace Outline
- Migration tool: Outline API → Uteke documents
- Verify all Outline use cases covered
- Deprecate Outline in Hermes

## Competitive Positioning vs Outline

| | Uteke Documents | Outline |
|---|----------------|---------|
| Primary user | AI agents | Humans |
| Write workflow | CLI/MCP/API | Rich web editor |
| Read workflow | API + Web share links | Web app |
| Search | Semantic (vector + FTS5 hybrid) | Full-text only |
| Collab | Room-based (async, agent-to-agent) | Realtime (human-to-human) |
| Hosting | Self-hosted, offline | Self-hosted or cloud |
| Storage | SQLite (single file) | PostgreSQL |
| Setup | Single binary | Docker + PostgreSQL |

## Research Sources

- BridgeMind/BridgeSpace: 16 parallel agents, agentic dev environment
- Auto Claude: 12 parallel agent terminals, git worktrees, AGPL-3.0
- Vibe Kanban: 26.9k stars but sunsetting (Jun 2026) — free user monetization failure
- MCP vs A2A protocols: MCP (agent↔tool/data), A2A (agent↔agent, Google)
- Carta: Svelte markdown editor/viewer for SvelteKit
- Khoj AI: personal KB + AI chat, relevant as alternative to Uteke Documents
