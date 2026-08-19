# CodeCora Skill Suites

AI agent skill suites for Uteke, Cora Code, Covecto, and more.

Clone a skill, drop it in your Hermes skills folder, done.

## Suites

### Product Skills

| Suite | Description |
|-------|-------------|
| [uteke](src/uteke/) | Offline-first semantic memory engine, persistent, searchable AI memory with ~30ms recall |
| [uteke-coordination](src/uteke-coordination/) | Room-based inter-agent coordination, shared memory rooms for multi-agent task routing, alerts, discussions |
| [cora-code](src/cora-code/) | Code intelligence platform, symbol extraction, hybrid search, brain mode (BYOK) |
| [covecto](src/covecto/) | Raster-to-SVG vectorization, convert bitmap images to clean vector graphics in Rust |
| [titen](src/titen/) | Self-hosted Threads API manager, post scheduling, multi-account management, analytics, MCP server |

### Workflow Skills

| Suite | Description |
|-------|-------------|
| [humanizer](src/humanizer/) | Remove AI-generated writing patterns from text, 30+ detection rules |
| [copywriting](src/copywriting/) | Copywriting frameworks and persuasion principles for natural text |
| [hybrid-memory](src/hybrid-memory/) | SQLite + Uteke hybrid memory with 4-tier lifecycle and frequency-based promotion |

### Plugins

| Plugin | Description |
|--------|-------------|
| [uteke-tool](plugins/uteke-tool/) | Hermes agent plugin for Uteke API, remember, recall, rooms, documents, tags |

## Prerequisites

Product skills require their respective binary installed. Download from GitHub Releases:

| Product | Latest | Download |
|---------|--------|----------|
| [Uteke](https://github.com/codecoradev/uteke) | v0.15.0 | [Releases](https://github.com/codecoradev/uteke/releases/latest) (Linux, macOS, Windows) |
| [Cora Code](https://github.com/codecoradev/cora-code) | v0.13.0 | [Releases](https://github.com/codecoradev/cora-code/releases/latest) (Linux, macOS, Windows) |
| [Covecto](https://github.com/codecoradev/covecto) | v0.1.1 | [Releases](https://github.com/codecoradev/covecto/releases/latest) (Linux, macOS, Windows) |

Each release ships binaries for x86_64 and aarch64 on Linux/macOS, plus x86_64 on Windows.

### Quick Install (Linux/macOS)

```bash
# Uteke
curl -fsSL https://github.com/codecoradev/uteke/releases/latest/download/uteke-x86_64-unknown-linux-gnu.tar.gz | tar xz

# Cora Code
curl -fsSL https://github.com/codecoradev/cora-code/releases/latest/download/cora-x86_64-unknown-linux-gnu.tar.gz | tar xz

# Covecto
curl -fsSL https://github.com/codecoradev/covecto/releases/latest/download/covecto-x86_64-unknown-linux-gnu.tar.gz | tar xz
```

Workflow skills (humanizer, copywriting, hybrid-memory) have no external dependencies.

## Installation

```bash
# Clone the repo
git clone https://github.com/codecoradev/skill-suites.git

# Copy desired skill to your Hermes skills directory
cp -r skill-suites/src/uteke ~/.hermes/skills/
cp -r skill-suites/src/cora-code ~/.hermes/skills/
cp -r skill-suites/src/covecto ~/.hermes/skills/
cp -r skill-suites/src/titen ~/.hermes/skills/
cp -r skill-suites/src/humanizer ~/.hermes/skills/creative/
cp -r skill-suites/src/copywriting ~/.hermes/skills/
```

### Plugin (uteke-tool)

```bash
# Copy plugin to your Hermes plugins directory
cp -r skill-suites/plugins/uteke-tool ~/.hermes/plugins/

# Configure environment variables
export UTEKE_BASE_URL=http://localhost:8767  # Your Uteke server URL
export UTEKE_TOKEN=your-token-here            # Your auth token
export UTEKE_NAMESPACE=default                # Your namespace

# Restart your Hermes gateway to load the plugin
```

## Usage

### Uteke (Semantic Memory)

```bash
uteke remember "Deployed v2.1 to staging" --tags deploy,staging --type decision
uteke recall "when did we deploy?" --namespace default
```

### Cora Code (Code Intelligence)

```bash
cora init /path/to/project
cora index
cora search "authentication middleware"
```

### Covecto (Image Vectorization)

```bash
covecto input.png -o output.svg
covecto input.jpeg --format svg --quality high
```

## Configuration

### Uteke

| Env Var | Default | Description |
|---------|---------|-------------|
| `UTEKE_BASE_URL` | `http://localhost:8767` | Uteke server URL |
| `UTEKE_TOKEN` | (none) | Bearer token for authentication |
| `UTEKE_NAMESPACE` | `default` | Default namespace for operations |

### Cora Code

Cora Code uses BYOK (Bring Your Own Key) model:

```bash
export CORA_LLM_PROVIDER=openai  # or anthropic, ollama
export CORA_LLM_API_KEY=your-key
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch strategy, validation checklist, and PR process.

## Products

- [Uteke](https://github.com/codecoradev/uteke) — Offline-first semantic memory engine
- [Cora Code](https://github.com/codecoradev/cora-code) — Code intelligence platform
- [Titen](https://github.com/codecoradev/titen) — Self-hosted Threads API manager
- [Covecto](https://github.com/codecoradev/covecto) — Dual-engine image-to-SVG vectorization (Rust)

---

By [CodeCoraDev](https://github.com/codecoradev)
