# Titen

Self-hosted Threads API manager. Schedule posts, manage multiple accounts, track analytics, and automate your Threads presence from your own server.

## Features

- **Multi-account management** — Connect unlimited Threads accounts with automatic token refresh
- **Post scheduling** — Plan content with a calendar view and timezone-aware scheduling
- **Human-in-the-loop approval** — Draft → approve → publish workflow for team safety
- **Analytics dashboard** — Track views, likes, replies, reposts, and quota usage
- **Comment sentiment** — Fetch and analyze comment sentiment per post
- **Mentions monitoring** — Track who mentioned your accounts
- **Media library** — Upload and manage images for carousel posts
- **MCP server** — Built-in Model Context Protocol server for AI agent integration
- **CLI client** — Full-featured terminal client for scripting and automation
- **Web dashboard** — Responsive admin UI with mobile support

## Install

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### Quick Start (Docker)

```bash
# Clone
git clone https://github.com/codecoradev/titen.git
cd titen

# Configure
cp .env.example .env
# Edit .env: set TITEN_API_KEY and OAuth credentials

# Start
docker compose up -d
```

The web dashboard will be available at `http://localhost:3000`.

### Pre-built Images (GHCR)

```bash
# Pull latest
docker pull ghcr.io/codecoradev/titen:latest-web
docker pull ghcr.io/codecoradev/titen:latest-api

# Or specific version
docker pull ghcr.io/codecoradev/titen:0.4.2-web
docker pull ghcr.io/codecoradev/titen:0.4.2-api
```

Set `WEB_IMAGE` and `API_IMAGE` in your `.env` file to skip local builds.

### Native Binary

Download from [GitHub Releases](https://github.com/codecoradev/titen/releases/latest):

```bash
# Linux x86_64
curl -fsSL https://github.com/codecoradev/titen/releases/latest/download/titen-x86_64-unknown-linux-gnu-v0.4.2.tar.gz | tar xz

# Start the API server
./titen-api
```

## Configuration

Key environment variables (see `.env.example` for full list):

| Variable | Required | Description |
|----------|----------|-------------|
| `TITEN_API_KEY` | Production | API key for authentication |
| `TITEN_ENCRYPTION_KEY` | Production | AES-256-GCM key for token encryption at rest |
| `TITEN_CORS_ORIGINS` | Optional | Comma-separated allowed origins |
| `TITEN_DB_PATH` | Optional | SQLite database path (default: `~/.codecora/titen/titen.db`) |
| `TITEN_SCHEDULER_INTERVAL_SECS` | Optional | Scheduler interval (default: 60) |

Generate encryption key:

```bash
openssl rand -hex 32
```

## Connecting a Threads Account

1. Go to **Settings** in the web dashboard
2. Enter your Meta App ID and App Secret
3. Click **Add Account** — you will be redirected to Meta OAuth
4. Authorize the app — your account appears in the Accounts page

Alternatively via CLI:

```bash
titen accounts add --token <ACCESS_TOKEN>
```

## Usage

### Web Dashboard

Navigate to `http://localhost:3000` (or your configured URL). Login with your API key.

### CLI

```bash
# List accounts
titen accounts list

# Create a post
titen posts create --account <ID> --text "Hello Threads!"

# Schedule a post
titen schedules create --account <ID> --text "Scheduled post" --at "2026-08-10T09:00:00Z"

# Check token status
titen accounts check-tokens

# Get analytics
titen analytics --account <ID>
```

### MCP Server (AI Agent Integration)

Titen includes a built-in MCP server (`titen-mcp`) for use with Claude Desktop, Cursor, or other MCP clients:

```json
{
  "mcpServers": {
    "titen": {
      "command": "/path/to/titen-mcp",
      "env": {
        "TITEN_DB_PATH": "~/.codecora/titen/titen.db"
      }
    }
  }
}
```

Available MCP tools: `list_accounts`, `create_post`, `schedule_post`, `list_schedules`, `cancel_schedule`, `refresh_token`, `check_tokens`, `fetch_comments`, `get_post_sentiment`, `get_post_insights`, `get_account_analytics`, `delete_post`, `create_container`, `publish_container`.

## API Reference

All endpoints require `X-API-Key` header (or session cookie from web login).

### Accounts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/accounts` | List all accounts |
| POST | `/api/accounts` | Add account |
| PUT | `/api/accounts/{id}` | Update account |
| DELETE | `/api/accounts/{id}` | Delete account |
| POST | `/api/accounts/{id}/refresh-token` | Refresh access token |
| GET | `/api/accounts/{id}/profile` | Get Threads profile |
| GET | `/api/accounts/{id}/insights` | Get account insights |
| GET | `/api/accounts/{id}/publishing-limit` | Check quota |
| GET | `/api/accounts/check-tokens` | Check all tokens |

### Posts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/posts` | List posts |
| POST | `/api/posts` | Create post |
| GET | `/api/posts/{id}` | Get post details |
| DELETE | `/api/posts/{id}` | Delete post |
| GET | `/api/posts/{id}/insights` | Post metrics |

### Scheduling (HITL)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/schedules` | List schedules |
| POST | `/api/schedules` | Create schedule (starts as draft) |
| PUT | `/api/schedules/{id}` | Update schedule |
| PATCH | `/api/schedules/{id}` | Partial update |
| DELETE | `/api/schedules/{id}` | Delete schedule |
| POST | `/api/schedules/{id}/approve` | Approve draft → pending |
| POST | `/api/schedules/{id}/reject` | Reject draft |
| GET | `/api/schedules/upcoming` | List upcoming schedules |

### Analytics and Comments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/posts` | Post analytics summary |
| GET | `/api/analytics/posts/{id}/trend` | Post trend over time |
| GET | `/api/posts/{id}/comments` | List stored comments |
| POST | `/api/posts/{id}/comments/fetch` | Fetch from Threads API |
| GET | `/api/posts/{id}/comments/sentiment` | Sentiment analysis |

### Media and Threads

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/media` | List media |
| POST | `/api/media` | Upload media |
| DELETE | `/api/media/{id}` | Delete media |
| POST | `/api/oauth/exchange` | Exchange OAuth code for token |
| POST | `/api/threads/container` | Create container |
| POST | `/api/threads/container/{id}/publish` | Publish container |
| POST | `/api/threads/reply` | Reply to a post |
| POST | `/api/threads/search` | Search Threads |

## Production Deployment

### Behind Traefik (recommended)

```env
TRAEFIK_ENABLED=true
TITEN_HOST=titen.yourdomain.com
TITEN_COOKIE_SECURE=true
TITEN_REQUIRE_ENCRYPTION=true
```

### Token Encryption

Production deployments **must** set `TITEN_ENCRYPTION_KEY`. Without it, tokens are stored plaintext.

```env
TITEN_ENCRYPTION_KEY=<openssl rand -hex 32>
TITEN_REQUIRE_ENCRYPTION=true
```

## Version

0.4.2 — See [CHANGELOG](https://github.com/codecoradev/titen/blob/develop/CHANGELOG.md) for release history.

## License

AGPL-3.0-only

## Links

- [Repository](https://github.com/codecoradev/titen)
- [Releases](https://github.com/codecoradev/titen/releases)
- [Issues](https://github.com/codecoradev/titen/issues)
