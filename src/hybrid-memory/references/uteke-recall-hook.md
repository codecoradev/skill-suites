# uteke-recall and uteke-extract Shell Hooks

Two shell hooks that automate memory with Uteke. Recall runs before each LLM call. Extract runs when sessions end.

## Active Hooks

| Hook | Event | Purpose |
|------|-------|---------|
| uteke-recall | `pre_llm_call` | Search Uteke for relevant memories, inject into prompt |
| uteke-extract | `on_session_finalize` | Extract key takeaways from session, store in Uteke |

## How It Works

```
User message → pre_llm_call hook fires
  → handler.py runs uteke recall (namespace={agent}, limit=5)
  → returns {"context": "Recalled memories:\n1. [0.72] ..."}
  → Hermes injects context into user message before LLM
```

No plugin needed for hooks. Uses uteke CLI binary (model stays warm from uteke-serve).

## Config (per-agent)

```yaml
hooks:
  pre_llm_call:
    - command: "python3 ~/.hermes/extensions/uteke-recall/handler.py"
      timeout: 20
  on_session_finalize:
    - command: "python3 ~/.hermes/extensions/uteke-extract/handler.py"
      timeout: 20
hooks_auto_accept: true
```

## Hook Wire Protocol (pre_llm_call)

**Input (stdin):**
```json
{
  "hook_event_name": "pre_llm_call",
  "session_id": "...",
  "extra": {
    "user_message": "...",
    "is_first_turn": true
  }
}
```

**Output (stdout):**
```json
{"context": "Optional text to inject into the user message"}
```

No stdout (exit 0) = no injection.

## Agent Resolution

Handler extracts agent name from `cwd` field (most reliable). Fallback: `/proc/self/status` → PPid → parent cmdline → `-p` flag.

## Project-Aware Recall

Both hooks detect project context from file paths in messages and filter recall by `project:<name>` tag.

## uteke-serve

| Property | Value |
|----------|-------|
| Endpoint | `http://localhost:8767` |
| Recall latency | ~59ms (warm) |
| RAM | ~208MB |
| Auth | Bearer token required |

Hooks use uteke CLI (not HTTP) for simplicity. uteke-serve keeps the ONNX model warm, making CLI calls fast.
