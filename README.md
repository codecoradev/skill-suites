# CodeCoraDev Skill Suites

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

## Installation

### Skills

```bash
# Clone the repo
git clone https://github.com/codecoradev/skill-suites.git

# Copy desired skill to your Hermes skills directory
cp -r skill-suites/src/uteke ~/.hermes/skills/
cp -r skill-suites/src/cora-code ~/.hermes/skills/
cp -r skill-suites/src/covecto ~/.hermes/skills/
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
# Remember something
uteke remember "Deployed v2.1 to staging" --tags deploy,staging --type decision

# Recall
uteke recall "when did we deploy?" --namespace default

# Via plugin (in agent context)
uteke(action="remember", content="Important decision", tags="decision,infra")
uteke(action="recall", query="deploy timeline", limit=5)
uteke(action="room_recall", room="project-alpha", query="architecture")
```

### Cora Code (Code Intelligence)

```bash
# Index a project
cora init /path/to/project
cora index

# Search
cora search "authentication middleware"
cora brain "How does the auth flow work?"
```

### Covecto (Image Vectorization)

```bash
# Convert raster to SVG
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

Cora Code uses BYOK (Bring Your Own Key) model. Configure your LLM provider:

```bash
export CORA_LLM_PROVIDER=openai  # or anthropic, ollama
export CORA_LLM_API_KEY=your-key
```

## License

MIT, see [LICENSE](LICENSE).

## Contributing

1. Fork this repo
2. Create your feature branch (`git checkout -b feature/amazing-skill`)
3. Commit your changes (`git commit -m 'Add amazing skill'`)
4. Push to the branch (`git push origin feature/amazing-skill`)
5. Open a Pull Request

## Products

- [Uteke](https://github.com/codecoradev/uteke), Offline-first semantic memory engine
- [Cora Code](https://github.com/codecoradev/cora-code), Code intelligence platform
- Covecto: Raster-to-SVG vectorization (coming soon)

---

By [CodeCoraDev](https://github.com/codecoradev)
