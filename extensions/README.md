# Uteke Extensions for Hermes Agent

Shell hooks that give Hermes agents **automatic memory** — recall relevant memories before each LLM call, and auto-extract takeaways when sessions end.

## How It Works

```
User message → [uteke-recall hook] → relevant memories injected into context → LLM call
Session ends → [uteke-extract hook] → key takeaways saved to Uteke → future sessions benefit
```

## Setup

### 1. Configure hooks in your Hermes `config.yaml`

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

### 2. Set environment variables

```bash
export UTEKE_BASE_URL=http://localhost:8767
export UTEKE_TOKEN=your-token-here
```

### 3. Copy hook files

```bash
mkdir -p ~/.hermes/extensions
cp -r extensions/uteke-recall ~/.hermes/extensions/
cp -r extensions/uteke-extract ~/.hermes/extensions/
```

## Hooks

### uteke-recall (`pre_llm_call`)

Runs **before** each LLM call. Reads the user message, searches Uteke for relevant memories, and injects them as context.

- **Project-aware**: detects project name from file paths → filters by `project:<name>` tag
- **Skill suggestions**: also searches `hermes-skills` room for relevant skill recommendations
- **Skips cron sessions**: doesn't run on automated cron jobs
- **Output**: `{"context": "Recalled memories:\n  1. [0.85] ..."}` (Hermes wire protocol)

### uteke-extract (`on_session_finalize`)

Runs **when a session ends**. Reads assistant messages from `state.db`, extracts structured takeaways (headers, bullets, key-values), and stores them in Uteke.

- **Structured extraction**: prioritizes headers (`#`), bullets (`-`), numbered lists, and key-value pairs
- **Project-aware**: auto-detects project from message content → tags with `project:<name>`
- **Tags**: `auto-extract`, `agent:<name>`, `reason:<finalize_reason>`, `project:<name>`
- **Limits**: max 800 chars per memory, max 10 messages read, min 50 chars total

## Requirements

- Hermes Agent with shell hooks support
- Uteke server running (see [uteke](../src/uteke/))
- `UTEKE_BASE_URL` and `UTEKE_TOKEN` environment variables

## License

MIT
