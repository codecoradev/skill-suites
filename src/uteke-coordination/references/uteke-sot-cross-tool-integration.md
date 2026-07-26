# Uteke SoT — Cross-Tool Integration Reference

Architecture and setup for using Uteke as Source of Truth across multiple coding tools (Hermes, Pi.dev, Claude Code, Cursor, humans).

## Architecture Overview

```
                    ┌──────────────────────────┐
                    │     UTEKE (SoT)          │
                    │   uteke-serve on server   │
                    │                          │
                    │  MCP endpoint: /mcp       │
                    │  REST API: /remember etc  │
                    │  Rooms per project        │
                    └─────────┬────────────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
      ┌──────▼─────┐   ┌──────▼─────┐   ┌──────▼─────┐
      │   Hermes    │   │  Pi.dev    │   │   Human     │
      │ uteke-tool  │   │ MCP (HTTP) │   │ CLI / Web  │
      │ plugin      │   │            │   │             │
      │ (auto)      │   │ (on-demand)│   │             │
      └─────────────┘   └────────────┘   └─────────────┘
             │                │
             └───────┬────────┘
                     │
            ┌────────▼────────┐
            │  GitHub (Code)   │
            │  PR + Commits    │
            └──────────────────┘
```

## Why Uteke SoT over Multica/GitHub Projects

| Criteria | Uteke (SoT) | Multica AI | GitHub Projects |
|----------|-------------|-------------|-----------------|
| Focus | Knowledge + decisions | Task coordination | Issue tracking |
| What's stored | Context, architecture, specs | Task status | Issues, PRs |
| Pi.dev + Hermes sync | Shared knowledge base | Via coordinator layer | Manual |
| Semantic search | Built-in (vector) | No | No (text only) |
| Infra overhead | Zero (already running) | PostgreSQL + Docker + daemon | Zero (hosted) |
| Visual board | No | Full web dashboard | Basic board |
| Multi-agent orchestration | Tool-agnostic (read same source) | Vendor-neutral coordination | None |

**Decision rule:** If you need JIRA-like visual boards + agent task lifecycle management → Multica. If you need shared knowledge/decisions across tools → Uteke SoT. If you just need issue tracking → GitHub Projects.

## Multica Comparison Detail

Multica (v0.4.2, 40.7k GitHub stars) is "JIRA for AI agents":
- Supports 14 coding tools: Claude Code, Codex, Hermes, Pi, Cursor, Copilot, OpenCode, OpenClaw, Kimi, Kiro CLI, Antigravity, Qoder, Trae CLI
- Full task lifecycle: enqueue → claim → start → complete/fail
- Real-time WebSocket progress streaming
- Desktop app + iOS client + web dashboard
- Open source (Go + Next.js + PostgreSQL)
- Self-host or cloud SaaS

**Verdict for our setup (solo indie, 2 tools):** Overkill. Worth revisiting if using 3+ coding tools heavily or needing team visibility dashboard.

## MCP Transport Options

| Transport | Binary | Daemon | Remote | Best For |
|-----------|--------|--------|--------|----------|
| Stdio | `uteke-mcp` | No | No | Local agents, single machine |
| HTTP | `uteke-serve` | Yes | Yes | Shared/team, remote access |

### Stdio Setup (local agents)

```jsonc
// Pi.dev — ~/.pi/mcp.json or project .mcp.json
{
  "mcpServers": {
    "uteke": {
      "command": "uteke-mcp"
    }
  }
}
```

### HTTP Setup (remote server)

```jsonc
// Pi.dev — ~/.pi/mcp.json or project .mcp.json
{
  "mcpServers": {
    "uteke": {
      "url": "http://localhost:8767/mcp",
      "headers": {
        "Authorization": "Bearer <UTEKE_AUTH_TOKEN>"
      }
    }
  }
}
```

### Memory Provider (DEPRECATED since v0.8.0 — use MCP HTTP transport instead)

> **⚠️ Deprecated.** `uteke init --agent <name> --memory-provider` was the old way to auto-inject memories per LLM turn. Since v0.8.0, use uteke-tool plugin (Hermes) or MCP HTTP transport (Pi.dev, Claude Code, Cursor). MemoryProvider is no longer maintained.

## uteke-serve Auth Setup

**Production SoT:** `http://localhost:8767` (Docker internal service name) / `http://localhost:8767/` (Traefik + TLS). All agents MUST write to this instance. `localhost:8767` / `127.0.0.1:8767` should only be used for local testing — they may point to a separate uteke-serve instance with a different database.

⚠️ **CLI vs uteke-serve storage split still applies:** `uteke` CLI reads/writes `~/.uteke` (local SQLite). `POST /remember` via uteke-serve writes to the uteke-serve database (which may or may not be `~/.uteke` depending on how uteke-serve was started). **On the production server, uteke-serve on `localhost:8767` IS the canonical store** — always verify via `curl http://localhost:8767/health` and `/room/stats` before assuming data is persisted.

### Enable auth in uteke.toml

```toml
[server]
enabled = true
host = "uteke"
port = 8767
auth_token = "your-strong-token-here"
```

Or via env var:
```bash
UTEKE_AUTH_TOKEN="your-token" uteke-serve --host uteke --port 8767
```

### Security checklist for remote exposure

| Setting | Value | Why |
|---------|-------|-----|
| `--host` | `uteke` (Docker internal) | Docker service name; use Traefik reverse proxy for public access |
| `UTEKE_AUTH_TOKEN` | Strong random token | Required for remote — without it, anyone reads/writes memories |
| TLS | Reverse proxy (Traefik/Caddy/CF Tunnel) | Encrypts traffic — required for remote |
| `--read-only-token` | Separate token | GET-only access for Pi.dev if only reading is needed |

## Domain + TLS Setup

Pick ONE method based on your infra:

### Traefik (if running on same server)

```yaml
http:
  routers:
    uteke:
      rule: "Host(`localhost:8767`)"
      entryPoints:
        - websecure
      tls:
        certResolver: myresolver
      service: uteke

  services:
    uteke:
      loadBalancer:
        servers:
          - url: "http://localhost:8767"
```

### Caddy (simplest)

```
localhost:8767 {
    reverse_proxy localhost:8767
}
```

### Cloudflare Tunnel (if no reverse proxy on server)

```bash
cloudflared tunnel route dns your-tunnel localhost:8767
```

## MCP JSON-RPC 2.0 Quick Reference

All MCP communication uses JSON-RPC 2.0 over POST `/mcp`:

```bash
# Initialize (handshake)
curl -s -X POST http://localhost:8767/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize",
       "params":{"protocolVersion":"2025-06-18","capabilities":{},
       "clientInfo":{"name":"pi","version":"0.1"}}}'
# Response: {"result":{"capabilities":{"tools":{},"protocolVersion":"2025-06-18",
#            "serverInfo":{"name":"uteke","version":"0.9.1"}}}

# List tools
curl -s -X POST http://localhost:8767/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

# Call tool
curl -s -X POST http://localhost:8767/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call",
       "params":{"name":"uteke_room_list","arguments":{}}}'
```

## Namespace Isolation

MCP server uses `default` namespace by default. Pass `namespace` argument to any tool for isolation:

```jsonc
// Each agent gets own namespace — memories never cross
{
  "mcpServers": {
    "uteke": {
      "command": "uteke-mcp"
    }
  }
}
// Then in tool calls: {"name":"uteke_recall","arguments":{"query":"...","namespace":"pi"}}
```

For shared rooms (SoT pattern), all agents use the same namespace (e.g., `default` or `codecora`) when accessing project rooms.
