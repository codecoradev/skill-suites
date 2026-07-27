# Contributing to Skill Suites

Skill Suites is a library of [Hermes Agent](https://github.com/nousresearch/hermes) skills, a plugin, and extensions maintained by [CodeCora](https://github.com/codecoradev).

## Branch Strategy

| Branch | Purpose |
|--------|--------|
| `develop` | Default branch. All work happens here. |
| `main` | Release branch. Protected. Merge from `develop` for releases. |

## Workflow

1. **Fork** the repo
2. **Create a feature branch** from `develop`:
   ```bash
   git checkout -b feat/your-feature
   ```
3. Make your changes
4. Run validation (see below)
5. **Push** and open a PR targeting `develop`
6. After review and merge to `develop`, a maintainer creates a release PR `develop → main`

## Adding a New Skill

Each skill lives under `src/<skill-name>/` with this structure:

```
src/<skill-name>/
├── SKILL.md          # Skill definition (frontmatter + instructions)
├── VERSION           # Semver version, e.g. "1.2.3"
├── README.md         # Human-readable overview + install instructions
└── references/       # Reference files loaded on demand (each <3k tokens)
    └── *.md
```

### SKILL.md Frontmatter

Required fields:

```yaml
---
name: <skill-name>           # Must match directory name
version: x.y.z               # Semver
license: MIT
description: "One-line description of what the skill does."
metadata:
  hermes:
    tags: [tag1, tag2, ...]  # For skill search discoverability
---
```

### Validation Checklist

Before submitting a PR, run these checks:

- [ ] **Structure**: SKILL.md, VERSION, and README.md all present
- [ ] **Frontmatter**: name matches directory, version and description set, tags present
- [ ] **Links**: All relative links resolve (no dead references)
- [ ] **Token size**: Reference files under 3k tokens (~12KB)
- [ ] **Sanitization**: No internal paths, credentials, or private domains
- [ ] **Syntax**: Python files compile, YAML parses without errors

### Content Guidelines

- SKILL.md is the skill body loaded into the LLM context. Be concise and actionable.
- Reference files are loaded on demand. Keep them focused on one topic each.
- README.md is for humans reading GitHub. Include what it does, install steps, and version.
- Write in English. Avoid AI-slop patterns (excessive em dashes, rule of three, signposting, boldface bullets).
- Use `~/.hermes/` as placeholder for user home paths. Never include real server addresses or tokens.

## Plugin and Extensions

- **Plugin** (`plugins/uteke-tool/`): Hermes plugin for Uteke API access. Requires `plugin.yaml` + `tool.py`.
- **Extensions** (`extensions/`): Optional Uteke shell hooks for auto-recall and auto-extract. Each extension is a single `handler.py`.

See `extensions/README.md` for install instructions.

## PR Types

Use conventional commit prefixes in PR titles:

| Prefix | When |
|--------|------|
| `feat:` | New skill or feature |
| `fix:` | Bug fix or validation fix |
| `docs:` | README, CONTRIBUTING, or documentation changes |
| `refactor:` | Restructure without behavior change |
| `chore:` | .gitignore, config, meta changes |

## Reporting Issues

Open a GitHub issue with:
- What skill or component is affected
- Expected vs actual behavior
- Hermes Agent version you're running
- Steps to reproduce (if applicable)
