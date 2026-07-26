# MCP + Docker Deployment Guide

**Date:** June 30, 2026

## Transport Options

| Transport | Docker Available? | How |
|-----------|-------------------|-----|
| **stdio** (`uteke-mcp` binary) | ❌ **NOT in image** — CI only builds `-p uteke-cli -p uteke-server` | Would need Dockerfile patch |
| **HTTP** (`POST /mcp` via `uteke-serve`) | ✅ **Available** — `uteke-serve` exposes `POST /mcp` endpoint on port 8767 | Use `hermes mcp add uteke --url` |

**Protocol version:** `2025-06-18` (Streamable HTTP spec). 1 MiB body limit.

## Quick Start (HTTP Transport)

```bash
# 1. Start uteke via Docker
docker run -d --name uteke \
  -p 127.0.0.1:8767:8767 \
  -v uteke-data:/data \
  ghcr.io/codecoradev/uteke:latest

# 2. Verify
curl http://localhost:8767/health

# 3. Register in Hermes via HTTP transport
hermes mcp add uteke --url http://127.0.0.1:8767/mcp

# 4. Test MCP endpoint manually
curl -X POST http://127.0.0.1:8767/mcp \
  -H "Content-Type: application/json" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}'
```

## MCP Tools via HTTP

| Tool | Description |
|------|-------------|
| `uteke_remember` | Store a memory (supports type, room, author, tags) |
| `uteke_recall` | Semantic search (supports tags filter, min_score) |
| `uteke_search` | Keyword text search |
| `uteke_list` | List memories (supports pagination via offset) |
| `uteke_forget` | Delete a memory by ID |
| `uteke_stats` | Memory store statistics |

## Non-Hermes Agents (Claude Desktop, Cursor)

These agents typically only support **stdio** transport. Options:

1. **Build uteke-mcp locally** — `cargo install --git https://github.com/codecoradev/uteke --path crates/uteke-mcp` then point agent config to the binary
2. **Use HTTP proxy** — Some MCP clients support HTTP endpoints (Hermes does via `hermes mcp add --url`)
3. **Patch Docker image** — Add `uteke-mcp` binary to Dockerfile (see CI gap below)

## Image Registries

| Registry | Image |
|----------|-------|
| **GitHub Container Registry** | `ghcr.io/codecoradev/uteke:latest` |
| **Docker Hub** | `codecoradev/uteke:latest` |

Release workflow pushes to both in a single build. Docker Hub is conditional on `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` org secrets — falls back to GHCR-only if absent.

## Multi-Container Shared Volume (Hermes + Uteke)

When running Uteke in a separate Docker container alongside Hermes, both need access to the same data folder.

### Topology

```
HOST: ~/.hermes/.uteke/
  ├── bind mount → Hermes container (~/.uteke/) → uteke CLI (local)
  └── bind mount → Uteke container (/data/)              → uteke-serve (HTTP API)
```

### UID Mismatch Pitfall

| Container | Runtime User | UID:GID |
|-----------|-------------|---------|
| Hermes | `hermes` (s6-overlay) | `10000:10000` |
| Uteke image | `uteke` | `1000:1000` |

Uteke Dockerfile: `useradd --system --uid 1000 --gid uteke`. Files created by Hermes are 10000:10000 → **permission denied** if Uteke container runs as default user.

**Fix:** Override user in compose to match Hermes UID:

```yaml
services:
  uteke:
    image: ghcr.io/codecoradev/uteke:latest
    container_name: uteke
    user: "10000:10000"          # ← match Hermes UID
    ports:
      - "127.0.0.1:8767:8767"
    volumes:
      - ~/.hermes/.uteke:/data   # host path (NOT named volume)
    environment:
      - UTEKE_AUTH_TOKEN=${UTEKE_TOKEN}
      - UTEKE_HOME=/data
    restart: unless-stopped
    command: ["uteke-serve", "--host", "0.0.0.0", "--port", "8767"]
```

### Named Volume vs Bind Mount

Use **bind mount** (host path), NOT named Docker volume. Hermes compose uses `~/.hermes:~` (bind mount). Named volumes live in `/var/lib/docker/volumes/` — they don't share data with Hermes bind mounts without extra symlink/config complexity.

### Image Size (Model Duplication)

| Component | Size |
|-----------|------|
| Debian slim base | ~75MB |
| Binaries (uteke, uteke-serve, uteke-mcp) | ~15MB |
| **Embedding model (EmbeddingGemma Q4)** | **~120MB** |
| **Total** | **~200MB** |

Dockerfile bundles model via `COPY models/ /data/models/embeddinggemma-q4`. When using bind mount `~/.hermes/.uteke:/data`, the volume's `models/` directory takes precedence — **the image-bundled model is unused wasted 120MB**.

Updates only re-pull changed layers (~15MB binary layer) since model layer stays cached.

### Auth Required for Public Access

Without `UTEKE_AUTH_TOKEN`, all endpoints are open. For public deployment behind reverse proxy:

```yaml
environment:
  - UTEKE_AUTH_TOKEN=${UTEKE_TOKEN}           # full access
  - UTEKE_READ_ONLY_TOKEN=${UTEKE_READ_TOKEN} # GET-only (optional)
```

## CI Gap: uteke-mcp Missing from Docker Build

**Source:** `.github/workflows/release.yml`

```
# CI only builds these:
cargo build --release --target ${{ matrix.target }} -p uteke-cli -p uteke-server

# Docker extraction only copies:
mv ../binaries/uteke ../binaries/uteke-amd64
mv ../binaries/uteke-serve ../binaries/uteke-serve-amd64
# uteke-mcp is NOT extracted, NOT in image
```

**Fix needed in release.yml:**
1. Add `-p uteke-mcp` to cargo build command
2. Add `uteke-mcp` to binary extraction and Dockerfile COPY

## Docker Deployment Pitfalls

For cross-container volume sharing (Hermes + Uteke UID mismatch fix), `libmvec.so.1` glibc mismatch fix (v0.6.2/v0.6.3 — trixie-slim), Debian t64 package rename (`libssl3` → `libssl3t64`), and image size breakdown, see `references/docker-deployment-pitfalls.md` in the `uteke-dev` skill (`release-pitfalls.md`).

## Known Issue: uteke-mcp Missing from Pre-built Releases

See `references/known-issues.md` — `uteke-mcp` is also missing from `install.sh` and GitHub release archives. Currently requires building from source. Issue #501 filed.

## Shared Volume: Hermes Container + Uteke Container

**Problem:** Hermes agents run inside a container and use `uteke` binary locally (uteke-tool plugin, NOT HTTP). A separate Uteke container needs access to the same DB for public API exposure.

**Hermes container topology** (from `/opt/hermes/docker-compose.yml`):
```yaml
services:
  gateway:
    network_mode: host
    volumes:
      - ~/.hermes:~    # ← bind mount, NOT named volume
```

This means `~/.hermes/.uteke` on host = `~/.uteke` inside Hermes container.

**Solution: Bind mount the same host path into Uteke container.**

```yaml
# docker-compose.uteke.yml
services:
  uteke:
    image: ghcr.io/codecoradev/uteke:latest
    container_name: uteke
    ports:
      - "127.0.0.1:8767:8767"
    volumes:
      - ~/.hermes/.uteke:/data    # ← same host path Hermes uses
    environment:
      - UTEKE_AUTH_TOKEN=${UTEKE_AUTH_TOKEN}
      - UTEKE_HOME=/data
    restart: unless-stopped
    command: ["uteke-serve", "--host", "0.0.0.0", "--port", "8767"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8767/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

**Why bind mount, NOT named volume:**
- Named volumes live in `/var/lib/docker/volumes/` — completely separate from `~/.hermes/.uteke`
- Hermes container bind-mounts `~/.hermes:~` — no way to inject a named volume into a subfolder of an existing bind mount
- Bind mount shares the same host path both containers read from

**Critical rules:**
1. Hermes agents use `uteke` CLI binary locally (uteke-tool plugin, stdio) — they do NOT talk to uteke-serve HTTP. DB must be shared via filesystem.
2. Do NOT run `uteke-serve` inside Hermes container AND a separate Uteke container against the same DB simultaneously — SQLite WAL contention.
3. `--host 0.0.0.0` is required inside Uteke container (default `127.0.0.1` only listens locally).
4. Always set `UTEKE_AUTH_TOKEN` when exposing beyond localhost — without it, all endpoints (including `DELETE /forget`) are open.

**Two-tier auth tokens:**

| Token | Scope | Use case |
|-------|-------|----------|
| `UTEKE_AUTH_TOKEN` | Full read+write | Internal agents, admin scripts |
| `UTEKE_READ_ONLY_TOKEN` | GET only (recall, search, list, stats, graph) | Public integrations, monitoring |

## References

- Docker image: `ghcr.io/codecoradev/uteke:latest`
- Docker docs: `docs/docker.md` in repo (does NOT mention MCP — gap)
- MCP crate: `crates/uteke-mcp/README.md`
- Hermes integration: `docs/integrations/hermes.md` (MCP section minimal — 2 lines)
