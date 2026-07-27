# Uteke Extensions for Hermes Agent

Shell hooks that give Hermes agents automatic memory: recall relevant memories before each LLM call, and auto-extract takeaways when sessions end.

## Architecture

```
┌─────────────┐    ┌──────────────────┐    ┌─────────┐
│ User message │───▶│ uteke-recall hook │───▶│ LLM call │
│              │    │ (pre_llm_call)   │    │         │
└─────────────┘    │ → search uteke   │    │ context  │
                   │ → inject results  │───▶│ injected │
                   └──────────────────┘    └─────────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │ Session ends │
                                          └──────┬───────┘
                                                 ▼
                                        ┌──────────────────┐
                                        │ uteke-extract hook│
                                        │(on_session_finalize)│
                                        │ → read messages  │
                                        │ → extract key    │
                                        │   takeaways      │
                                        │ → store in uteke │
                                        └──────────────────┘
```

## Prerequisites

- Hermes Agent with [shell hooks](https://hermes-agent.nousresearch.com/docs) support
- Uteke server running (`uteke serve --port 8767`)
- Uteke CLI installed ([install guide](https://github.com/codecoradev/uteke))

## Companion Skill

These extensions automate memory operations. For the full memory system (4-tier lifecycle, SQLite staging, confidence decay, entity graph), install the [hybrid-memory skill](../src/hybrid-memory/) alongside these extensions.

**In short: install both for the complete experience.**

## Installation

### Step 1: Copy extension files

```bash
# Clone this repo
git clone https://github.com/codecoradev/skill-suites.git

# Copy extensions to your Hermes directory
mkdir -p ~/.hermes/extensions
cp -r skill-suites/extensions/uteke-recall ~/.hermes/extensions/
cp -r skill-suites/extensions/uteke-extract ~/.hermes/extensions/
```

### Step 2: Set environment variables

Add to your Hermes profile's environment (or `~/.bashrc`):

```bash
export UTEKE_BASE_URL=http://localhost:8767
export UTEKE_TOKEN=your-token-here   # Generate: uteke token create
```

### Step 3: Configure hooks in Hermes `config.yaml`

Edit `~/.hermes/profiles/<your-profile>/config.yaml`:

```yaml
hooks:
  pre_llm_call:
  - command: python3 ~/.hermes/extensions/uteke-recall/handler.py
    timeout: 20
  on_session_finalize:
  - command: python3 ~/.hermes/extensions/uteke-extract/handler.py
    timeout: 20
hooks_auto_accept: true
```

### Step 4: Restart Hermes gateway

```bash
hermes restart -p <your-profile>
```

## Usage

### It just works, no manual steps needed

Once configured, the hooks run automatically:

1. **Every user message** → uteke-recall searches for relevant past memories and injects them as context
2. **Every session end** → uteke-extract reads the last assistant messages and saves key takeaways

### Example: uteke-recall output

When you ask "how do I deploy the API?", the hook searches Uteke and injects context before the LLM sees your message:

```
Suggested skills (from hermes-skills room):
  1. [0.92] uteke: CLI reference for offline semantic memory...

Recalled memories (uteke):
  1. [0.87] API deployment uses Docker Compose with health check on /health endpoint...
  2. [0.75] Deploy to staging: docker compose -f docker-compose.staging.yml up -d...
  3. [0.68] Always run db migration before deploy: alembic upgrade head...
```

The LLM now has this context and can give you a much better answer.

### Example: uteke-extract behavior

When a session where you discussed "setting up CI/CD pipeline" ends, the hook:

1. Reads the last 10 assistant messages from `state.db`
2. Extracts structured content (headers, bullets, key-values)
3. Stores in Uteke with tags: `auto-extract`, `agent:default`, `reason:complete`, `project:myproject`

Next time you ask about CI/CD, uteke-recall will find this memory automatically.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `UTEKE_BASE_URL` | `http://localhost:8767` | Uteke server URL |
| `UTEKE_TOKEN` | *(required)* | Auth token, generate with `uteke token create` |
| `HERMES_PROFILE` | *(auto-detected)* | Agent profile name (usually auto-detected from cwd) |

### Tuning (edit constants in handler.py)

| Constant | Default | Description |
|----------|---------|-------------|
| `_SKILL_RECALL_LIMIT` | 5 | Max skill suggestions to inject |
| `MAX_CONTENT_CHARS` | 800 | Max chars stored per extracted memory |
| `MAX_MESSAGES` | 10 | Max assistant messages to read on extract |
| `MIN_CONTENT_LEN` | 50 | Skip sessions with less content |

## How Memory Flows

```
Session 1: "Set up PostgreSQL with pgvector extension"
    → uteke-extract saves takeaway
    → Tagged: project:myapp, auto-extract

Session 2: User asks "how do I add vector search?"
    → uteke-recall finds Session 1's takeaway
    → Injects: "PostgreSQL with pgvector extension..."
    → LLM gives contextual answer based on your past work
```

## Troubleshooting

### Hook not running

```bash
# Check if hooks are in config
grep -A5 'pre_llm_call' ~/.hermes/profiles/*/config.yaml

# Test hook manually
echo '{"user_message": "test database", "session_id": "manual_test", "cwd": "~"}' | \
  python3 ~/.hermes/extensions/uteke-recall/handler.py
# Expected: {"context": "..."} or empty if no memories yet
```

### No memories being extracted

- Check `UTEKE_TOKEN` is set and valid
- Check uteke server is running: `curl -sf http://localhost:8767/health`
- Sessions must have 10+ messages with 50+ chars total to trigger extraction
- Cron sessions are automatically skipped

### Wrong agent namespace

The hook auto-detects agent name from:
1. `cwd` field in hook payload (most reliable)
2. `HERMES_PROFILE` env var
3. `/proc` parent process chain (fallback)

If detection fails, it defaults to `default`.

## Hooks

### uteke-recall (`pre_llm_call`)

Runs **before** each LLM call. Searches Uteke for relevant memories and injects them.

- Project-aware: detects project from file paths → filters by `project:<name>` tag
- Skill suggestions: also searches for relevant skill recommendations
- Skips: cron sessions, very short messages (<5 chars), empty messages

### uteke-extract (`on_session_finalize`)

Runs **when a session ends**. Extracts structured takeaways and stores in Uteke.

- Structured extraction: prioritizes headers, bullets, numbered lists, key-values, tables
- Project-aware: auto-detects project from message content → tags appropriately
- Tags: `auto-extract`, `agent:<name>`, `reason:<finalize_reason>`, `project:<name>`

## License

MIT
