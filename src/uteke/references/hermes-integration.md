# Uteke ↔ Hermes Integration (v0.10.0)

**Last updated:** July 23, 2026

> ⚠️ **Mode B (MemoryProvider) removed June 29, 2026.** Current Hermes integration uses **Mode A** (uteke-tool plugin, manual) + **Mode C** (uteke-memory Python plugin, auto-recall via `pre_llm_call` hook). The Mode B sections are historical reference only.
>
> **Extension template rewritten (Jul 23, 2026):** `extensions/hermes-memory-provider/` is now a standard Hermes Python plugin (v2.0.0). Uses `ctx.register_hook("pre_llm_call", _pre_llm_call)` — in-process, no subprocess spawn, full contextvar access, circuit breaker. The old shell hook approach is replaced. For Hermes: copy to `~/.hermes/plugins/uteke-memory/`, enable in `plugins.enabled`. See branch `feat/hermes-plugin-pre-llm-call`.

## Current Integration Modes

```
Hermes Agent
├── Mode A: uteke-tool (manual)     → agent calls uteke(action=...) via uteke-serve HTTP
└── Mode C: uteke-memory (plugin)   → auto-recall via pre_llm_call Python hook
```

| | Mode A (`uteke-tool`) | Mode C (`uteke-memory` plugin) | ~~Mode B~~ |
|---|---|---|---|
| **Install** | `uteke init --agent hermes` | Copy plugin to `~/.hermes/plugins/` | ~~removed~~ |
| **Invocation** | Agent calls `uteke(action="recall")` | Automatic every turn | ~~Automatic~~ |
| **Transport** | HTTP → `uteke-serve` | subprocess or HTTP | ~~subprocess~~ |
| **Daemon** | Required | No / optional (HTTP) | ~~No~~ |
| **Rooms** | Yes | Yes (HTTP) | ~~No~~ |
| **Hermes config** | Plugin auto-loads | `plugins.enabled: [uteke-memory]` | ~~`memory.provider: uteke`~~ |
| **Best for** | Explicit memory + rooms | Lightweight auto-recall | ~~Drop-in replacement~~ |

**Recommended:** Mode A + Mode C side by side.

## Mode C: uteke-memory Plugin (Jul 2026)

### Why Plugin, Not Shell Hook?

| Aspect | Shell Hook (old) | Python Plugin (new) |
|--------|-----------------|---------------------|
| Registration | `hooks.pre_llm_call` in config.yaml | `ctx.register_hook("pre_llm_call", cb)` |
| Runs in | Subprocess | Gateway process (in-process) |
| Contextvars | ❌ | ✅ Full access |
| Performance | Process spawn per turn | Direct function call |
| Agent name | Parse `cwd` from payload | `HERMES_HOME` basename |

### Install

```bash
cp -r extensions/hermes-memory-provider ~/.hermes/plugins/uteke-memory/
cd ~/.hermes/plugins/uteke-memory/
for f in *.tmpl; do mv "$f" "${f%.tmpl}"; done
hermes config set plugins.enabled.0 uteke-memory
```

### Config (`~/.hermes/uteke.json` or env vars)

| Variable | Default | Description |
|----------|---------|-------------|
| `UTEKE_BIN` | (search PATH) | Path to uteke binary |
| `UTEKE_NAMESPACE` | (agent profile name) | Memory namespace |
| `UTEKE_SERVER_URL` | (empty) | HTTP URL for uteke-serve |
| `UTEKE_TOKEN` | (empty) | Bearer token |
| `UTEKE_RECALL_LIMIT` | `5` | Memories per turn |
| `UTEKE_RECALL_MIN_SCORE` | `0.40` | Min score |
| `UTEKE_RECALL_TIMEOUT` | `15` | Max seconds |

### How It Works

1. `register(ctx)` → `ctx.register_hook("pre_llm_call", _pre_llm_call)`
2. Every turn: hook receives `user_message`, `session_id`, `conversation_history`, etc.
3. Truncates query to 500 chars, runs `uteke recall` (subprocess or HTTP)
4. Filters by `recall_min_score`, formats as `<recalled-memories>` XML
5. Returns `{"context": "..."}` → injected into user message (preserves system prompt cache)
6. Circuit breaker: 5 consecutive failures → 120s cooldown

## Mode B: memory-provider (HISTORICAL)

> Removed June 29, 2026. The `MemoryProvider` class, `on_session_end` extraction, and `memory.provider: uteke` config are all non-functional in current Hermes.

### How Mode B Worked

- `prefetch()` on background thread → subprocess `uteke recall --json`
- `on_session_end()` → `uteke import --extract` for fact distillation
- Circuit breaker: 5 failures → 120s pause
- Config: `~/.hermes/uteke.json` > env vars > defaults

## LLM Fact Extraction (`import --extract`)

Part of v0.5.0. Distills transcripts into atomic facts.

**System prompt:** Extract ONLY a JSON array of strings. Each string is ONE self-contained fact. Drop ephemeral content. Resolve pronouns.

| Setting | Default | Env Var |
|---------|---------|--------|
| Model | `gpt-4o-mini` | `UTEKE_EXTRACT_MODEL` |
| Base URL | `https://api.openai.com/v1` | `UTEKE_EXTRACT_BASE_URL` |
| API Key | (required) | `UTEKE_EXTRACT_API_KEY` |
| Max facts | 20 | — |

## Index Corruption & Repair

**Fix:** `kill uteke-serve` → `rm -f ~/.uteke/uteke_index.*` → `uteke repair` → `uteke doctor`

## SOUL.md Injection = Race Condition

⚠️ NEVER inject dynamic data into SOUL.md from hooks. Shared file = race condition under concurrent sessions. Use per-agent temp files or plugin hooks instead.

## `init.rs` Template (v0.10.0)

`init_hermes()` generates the Mode A `uteke-tool` plugin (tool.py + plugin.yaml) and optionally copies the Mode C memory-provider template. **Template bugs fixed Jul 24, 2026 (PR #775):** dynamic namespace via `HERMES_PROFILE`, `_get_room_id()` helper, namespace in all room API calls. Plugin version `0.3.2`.

⚠️ `init_hermes_memory_provider()` still installs the Mode B template path (deprecated). Only run `uteke init --agent hermes` (without `--memory-provider`).