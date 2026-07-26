# cora-code

**Cora Code** — AI-powered code review and code intelligence platform. BYOK (Bring Your Own Key).

## What's in this skill?

- **Usage guide** — `cora review`, `cora scan`, `cora brain search`, CLI flags
- **Architecture** — symbol extraction, hybrid search (AST + embedding), Brain Mode
- **Brain Mode** — deep code understanding with BYOK AI providers
- **CI integration** — pre-commit hooks, GitHub Actions, CI pitfalls and gotchas
- **Embedding strategy** — dimension tuning, false positive handling, tree-sitter patterns
- **Configuration** — YAML config reference, CI setup

## Quick Start

```bash
# Install
pip install cora-code

# Review current branch
cora review

# Scan for issues (no AI needed)
cora scan

# Brain mode — deep code intelligence
cora brain search "where is authentication handled?"
```

## Version

| Skill Version | Cora Code Binary |
|---------------|-----------------|
| 4.3.0 | v4.3.0+ |

## Installation

Place this `SKILL.md` in `~/.hermes/skills/cora-code/`.

## Related

- **[Cora Code repo](https://github.com/codecoradev/cora-code)** — Source code

## License

MIT
