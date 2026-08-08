---
name: titen
version: 0.4.2
license: AGPL-3.0-only
description: "Titen — Self-hosted Threads API manager. Schedule posts, manage accounts, track analytics, automate Threads presence."
metadata:
  author: CodeCoraDev
  hermes:
    tags: [titen, threads, scheduling, social-media, automation, hitl, analytics, mcp]
triggers:
  - titen
  - threads scheduling
  - threads api
  - threads automation
  - manage threads accounts
  - threads post scheduler
  - threads analytics
---

# Titen — Self-hosted Threads API Manager

**Repository:** https://github.com/codecoradev/titen
**Latest:** v0.4.2 | **License:** AGPL-3.0-only

Titen is a self-hosted Threads (Meta) API manager built in Rust. It provides a web dashboard, REST API, CLI, and MCP server for managing Threads accounts, scheduling posts with human approval, tracking analytics, and automating engagement.

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/codecoradev/titen.git
cd titen
cp .env.example .env
# Edit .env: set TITEN_API_KEY, TITEN_ENCRYPTION_KEY
docker compose up -d
```

Web dashboard available at `http://localhost:3000`. Login with your API key.

### Pre-built images (GHCR)

```bash
# In .env:
WEB_IMAGE=ghcr.io/codecoradev/titen:latest-web
API_IMAGE=ghcr.io/codecoradev/titen:latest-api

docker compose pull && docker compose up -d
```

### Native binary

Download from [Releases](https://github.com/codecoradev/titen/releases/latest). Three binaries per archive:
- `titen-api` — HTTP server
- `titen` — CLI client
- `titen-mcp` — MCP server (stdio)

## Architecture

```
┌─────────────┐         ┌──────────────┐
│  SvelteKit  │         │   Axum API   │
│  SSR (Bun)  │ ──/api──│   (Rust)     │
│  Port 3000  │         │   Port 7845  │
└─────────────┘         └──────────────┘
      │                        │
   Traefik ── HTTPS     SQLite (/data/titen.db)
```

Two-container setup: web (SvelteKit SSR) proxies `/api/*` to the Rust API container. SQLite persists via bind mount.

## Configuration

### Required for production

| Variable | Description |
|----------|-------------|
| `TITEN_API_KEY` | API key for authentication (header: `X-API-Key`) |
| `TITEN_ENCRYPTION_KEY` | AES-256-GCM key for token encryption. Generate: `openssl rand -hex 32` |
| `TITEN_REQUIRE_ENCRYPTION` | Set `true` to panic if encryption key missing |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `TITEN_DB_PATH` | `~/.codecora/titen/titen.db` | SQLite database path |
| `TITEN_CORS_ORIGINS` | (none) | Comma-separated allowed origins |
| `TITEN_SCHEDULER_INTERVAL_SECS` | `60` | How often scheduler runs |
| `TITEN_COOKIE_SECURE` | `false` | Set `true` on HTTPS for Secure cookie flag |
| `TRAEFIK_ENABLED` | `false` | Enable Traefik reverse proxy labels |

## Connecting a Threads Account

### Via Web Dashboard

1. **Settings** page: enter Meta App ID and App Secret
2. **Accounts** page: click **Add Account**
3. Complete Meta OAuth flow
4. Account appears with auto-resolved username and user_id

### Via CLI

```bash
# Token only (auto-resolves user_id + username)
titen accounts add --token <ACCESS_TOKEN>

# Short-lived → long-lived exchange
titen accounts add --token <SHORT_LIVED> --app-secret <APP_SECRET>
```

Tokens auto-refresh before expiry. Token encryption at rest via AES-256-GCM.

## Core Features

### Post Scheduling with HITL

Human-in-the-loop approval workflow for team safety:

```
draft → (human approves) → pending → (scheduler publishes at scheduled time) → published
draft → (human rejects)  → rejected
```

- `auto_approve: true` on CreateSchedule skips the draft state
- Dashboard shows draft count badge and approve/reject buttons
- Status filter tabs: All, Draft, Pending, Published

### Analytics

- Account-level insights (views, reach, follower count over time)
- Per-post metrics (views, likes, replies, reposts, quotes)
- Post trend tracking (time series)
- Publishing quota monitoring

### Comment Sentiment

Fetch comments from Threads API and run built-in sentiment analysis:

```bash
# Via API
POST /api/posts/{id}/comments/fetch   # Pull comments from Threads
GET  /api/posts/{id}/comments/sentiment  # Get sentiment summary
```

### MCP Server Integration

Titen includes `titen-mcp` — a stdio JSON-RPC MCP server for AI agents (Claude Desktop, Cursor, etc):

```json
{
  "mcpServers": {
    "titen": {
      "command": "/path/to/titen-mcp",
      "env": { "TITEN_DB_PATH": "~/.codecora/titen/titen.db" }
    }
  }
}
```

15 MCP tools available: `list_accounts`, `create_post`, `schedule_post`, `list_schedules`, `cancel_schedule`, `refresh_token`, `check_tokens`, `fetch_comments`, `get_post_sentiment`, `get_post_insights`, `get_account_analytics`, `delete_post`, `create_container`, `publish_container`, `get_user_profile`.

## API Endpoints

All endpoints require `X-API-Key` header or `titen_session` cookie.

### Accounts
- `GET /api/accounts` — list all
- `POST /api/accounts` — add (token auto-resolves user_id + username)
- `PUT /api/accounts/{id}` — update
- `DELETE /api/accounts/{id}` — delete
- `POST /api/accounts/{id}/refresh-token` — refresh token
- `GET /api/accounts/{id}/profile` — Threads profile
- `GET /api/accounts/{id}/insights` — account insights
- `GET /api/accounts/{id}/publishing-limit` — quota check
- `GET /api/accounts/check-tokens` — batch token check + auto-refresh

### Posts
- `GET /api/posts` — list
- `POST /api/posts` — create (supports `media_ids` for carousel)
- `GET /api/posts/{id}` — details
- `DELETE /api/posts/{id}` — delete
- `GET /api/posts/{id}/insights` — post metrics

### Scheduling
- `GET /api/schedules` — list all
- `POST /api/schedules` — create (starts as `draft` unless `auto_approve`)
- `PUT /api/schedules/{id}` — full update
- `PATCH /api/schedules/{id}` — partial update (COALESCE, no TOCTOU)
- `DELETE /api/schedules/{id}` — delete
- `POST /api/schedules/{id}/approve` — approve draft → pending
- `POST /api/schedules/{id}/reject` — reject draft
- `GET /api/schedules/upcoming` — upcoming schedules

### Analytics
- `GET /api/analytics/posts` — summary
- `GET /api/analytics/posts/{id}/trend` — time series

### Comments
- `GET /api/posts/{id}/comments` — stored comments
- `POST /api/posts/{id}/comments/fetch` — fetch from Threads API
- `GET /api/posts/{id}/comments/sentiment` — sentiment analysis

### Media
- `GET /api/media` — list
- `POST /api/media` — upload (S3-compatible or local)
- `DELETE /api/media/{id}` — delete

### Threads Integration
- `POST /api/oauth/exchange` — exchange OAuth code for token
- `POST /api/threads/container` — create media container
- `POST /api/threads/container/{id}/publish` — publish container
- `POST /api/threads/container/{id}/status` — check container status
- `POST /api/threads/reply` — reply to a post
- `POST /api/threads/reply/{id}/hide` — hide a reply
- `POST /api/threads/profile-lookup` — lookup user by username
- `POST /api/threads/search` — search Threads
- `POST /api/threads/mentions` — fetch mentions
- `POST /api/threads/share-to-instagram` — cross-post to Instagram

### Auth
- `POST /api/auth/login` — login with API key (sets session cookie)
- `GET /api/auth/session` — check session
- `POST /api/auth/logout` — logout
- `GET /health` — health check (public)

## CLI Reference

```bash
# Accounts
titen accounts list
titen accounts add --token <TOKEN>
titen accounts add --token <TOKEN> --app-secret <SECRET>
titen accounts delete <ID>

# Posts
titen posts create --account <ID> --text "Hello!"
titen posts create --account <ID> --text "Carousel" --media <ID1> <ID2>
titen posts delete <ID>

# Scheduling
titen schedules create --account <ID> --text "Scheduled" --at "2026-08-10T09:00:00Z"
titen schedules approve <ID>
titen schedules reject <ID>
titen schedules list

# Analytics
titen analytics --account <ID>

# Comments
titen comments fetch --post <ID>
titen comments sentiment --post <ID>

# Token management
titen accounts check-tokens

# Start API server
titen serve
```

## Production Checklist

- [ ] `TITEN_API_KEY` set (strong random value)
- [ ] `TITEN_ENCRYPTION_KEY` set (`openssl rand -hex 32`)
- [ ] `TITEN_REQUIRE_ENCRYPTION=true`
- [ ] `TITEN_COOKIE_SECURE=true` (HTTPS only)
- [ ] `TRAEFIK_ENABLED=true` with valid domain
- [ ] Backup `TITEN_ENCRYPTION_KEY` safely (changing it makes existing tokens undecryptable)
- [ ] Docker volume for SQLite persistence (`./data:/data`)

## Threads API Scope

Titen requests 10 of 11 available Meta App permissions:

`threads_basic`, `threads_content_publish`, `threads_manage_insights`, `threads_manage_reply`, `threads_read_replies`, `threads_manage_mentions`, `threads_read_all_content`, `threads_keyword_search`, `threads_share_to_instagram`, `threads_manage_audience`

Only `threads_location_tagging` is skipped.

Some endpoints (search, mentions, share-to-instagram, profile-lookup) require [Meta App Review](https://developers.facebook.com/docs/app-review) approval for production use.
