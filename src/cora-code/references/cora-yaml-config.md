# .cora.yaml Reference

## Key Fields

| Field | Default | Description |
|-------|---------|-------------|
| `provider.provider` | — | LLM provider (`openai`, `anthropic`, `groq`, `ollama`, `zai`, `custom`) |
| `provider.model` | — | Model name |
| `provider.base_url` | — | Custom endpoint URL |
| `llm.temperature` | `0` | Sampling temperature (0 = deterministic) |
| `llm.max_tokens` | `4096` | Max response tokens |
| `llm.max_tokens_param` | `auto` | Parameter name: `auto`/`max_tokens`/`max_output_tokens`/`max_completion_tokens` |
| `llm.timeout` | `120` | HTTP timeout seconds |
| `llm.cache_ttl` | `1440` | Cache TTL minutes (0 = disabled) |
| `severity` | `major` | Min severity to report |
| `hook.mode` | `warn` | Pre-commit mode (`warn`/`block`/`off`) |
| `hook.max_diff_size` | `51200` | Max diff chars before refusal |
| `ignore.files` | — | Glob patterns to exclude |
| `review.system_prompt_file` | — | Custom prompt file (path traversal guarded) |
| `review.response_format` | `none` | Opt-in `json_object` for compatible providers |

## v2 Format

`ignore` requires struct (v1 list format causes silent parse error):

```yaml
# ✅ v2
ignore:
  files:
    - "node_modules/**"
    - "generated/**"
  rules: []
```

## Top Pitfalls

1. **Per-repo `.cora.yaml` overrides global silently** — check `cat .cora.yaml` when auth issues arise
2. **`cora auth status` reports success with stale/revoked keys** — verify with real `cora review --base develop`
3. **API key source:** `~/.cora/auth.toml` (single key) or env vars: `CORA_PROVIDER`, `CORA_MODEL`, `CORA_BASE_URL`, `CORA_API_KEY`
4. **`--base branch` compares branches, not working tree** — use `--unstaged` for uncommitted changes
5. **`cora scan` sends full file content to LLM** — large files (>30KB) cause 502. Use `--batch-files 3` or prefer `cora review` (diff-based)
6. **GLM models may return invalid severity** — `"severity": "performance"` is not a valid variant. Batch skipped, non-blocking
7. **`.cora/` should be gitignored** — contains review history, not config
8. **Bifrost `x-bf-vk` vs Cora `Authorization: Bearer` mismatch** — use Z.AI direct endpoint for Cora