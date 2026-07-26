# uteke-coordination

**Uteke Room-based inter-agent coordination** — coordinate multiple AI agents through shared memory rooms.

## What's in this skill?

- **Room patterns** — task routing, alert broadcasting, multi-round discussions, CS handoffs
- **Workflow examples** — 7-round discussion, final-round verdict, single-agent planning
- **Room conventions** — parent/child hierarchy, tag taxonomy, naming standards
- **Pitfalls** — room junction contamination, cross-instance memory leaks, namespace isolation

## Quick Start

```bash
# Create a coordination room
uteke room create --name project-hub --namespace default

# Post a task for any agent to pick up
uteke room remember --room project-hub \
  --content "Deploy v2.1 to staging before EOD" \
  --tags "task,deploy,urgent" \
  --author ops-agent

# Any agent can recall tasks from the room
uteke room recall --room project-hub
```

## Version

| Skill Version | Requires uteke-serve |
|---------------|-------------------|
| 1.0.0 | v0.8.0+ (schema v15) |

## Installation

Place this `SKILL.md` in `~/.hermes/skills/uteke-coordination/`.

## Related

- **[uteke](../uteke/)** — Core Uteke CLI and API reference
- **[Extensions](../../extensions/)** — Auto-recall and auto-extract hooks

## License

MIT
