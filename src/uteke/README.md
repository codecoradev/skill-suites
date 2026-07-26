# uteke

**Uteke** — Offline-first semantic memory engine for AI agents.

A single Rust binary that gives any AI agent persistent, searchable memory with ~30ms recall. No API keys, no Python runtime needed.

## What's in this skill?

This Hermes skill contains everything you need to use Uteke effectively:

- **CLI reference** — all 25+ commands (`remember`, `recall`, `search`, `room_*`, `pin`, `consolidate`, etc.)
- **API endpoints** — full HTTP API reference for `uteke-serve`
- **Pitfalls & gotchas** — common mistakes and how to avoid them
- **Configuration** — env vars, Docker setup, namespace strategy

## Quick Start

```bash
# Install
curl -sSL https://codecora.dev/install | sh

# Start server
uteke serve --port 8767

# Remember something
echo "Deploy password rotation every 90 days" | uteke remember --namespace ops

# Recall later
uteke recall "password rotation" --namespace ops
```

## Version

| Skill Version | Uteke Binary | Requires uteke-serve |
|---------------|-------------|-------------------|
| 0.10.1 | v0.10.1+ | v0.8.0+ (schema v15) |

## Installation

See the [uteke GitHub repo](https://github.com/codecoradev/uteke) for binary downloads and Docker images.

For Hermes Agent: place this `SKILL.md` in your skills directory (`~/.hermes/skills/uteke/`).

## Related

- **[uteke-coordination](../uteke-coordination/)** — Multi-agent coordination via shared rooms
- **[uteke-tool plugin](../../plugins/uteke-tool/)** — Use Uteke as a Hermes tool/plugin
- **[Extensions](../../extensions/)** — Auto-recall and auto-extract hooks

## License

MIT
