# uteke-tool

Semantic memory plugin for Hermes via [uteke](https://github.com/codecoradev/uteke).

## Setup

1. Install uteke: `curl -fsSL https://raw.githubusercontent.com/codecoradev/uteke/main/install.sh | sh`
2. Start daemon: `uteke-serve --port 8767` (or use Docker container)
3. This plugin is installed in `~/.hermes/plugins/uteke-tool/`
4. Start a new Hermes session (plugin loads automatically)

### MCP Server (alternative)

For MCP-compatible agents, use the uteke MCP server instead:

```bash
hermes mcp add uteke --command uteke-mcp
```

## Usage

### Memory Operations

```python
uteke(action="remember", content="User prefers dark mode", tags="preference,ui")
uteke(action="recall", content="user preferences")
uteke(action="search", content="dark mode")
uteke(action="list", limit=10)
uteke(action="stats")
uteke(action="forget", id="abc12345")
```

### Room Operations (multi-agent collaboration)

```python
# Create a shared room
uteke(action="room_create", room_id="sprint-planning", title="Sprint Planning")

# Recall from a room (semantic search)
uteke(action="room_recall", room_id="sprint-planning", query="deadline")
# Note: `query` param is preferred. `content` also works as fallback.

# List all memories in a room (no query = chronological listing)
uteke(action="room_recall", room_id="sprint-planning")

# List all rooms
uteke(action="room_list")

# Room analytics
uteke(action="room_stats", room_id="sprint-planning")
uteke(action="room_summary", room_id="sprint-planning")
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `UTEKE_SERVER_URL`  | `https://localhost:8767` | uteke server URL (domain or Docker internal) |
| `UTEKE_BASE_URL`    | (none) | Alternative env var for server URL |
| `UTEKE_TOKEN`       | (none) | Bearer token for authentication |
