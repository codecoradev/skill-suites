# Cora CI Patterns & Pitfalls

## ⚠️ `continue-on-error` is FORBIDDEN on gates (User directive 2026-06-03)

**NEVER use `continue-on-error: true` on the Infisical secrets fetch step or the cora review run step.** These are blocking gates — `continue-on-error` makes them meaningless.

The correct approach: **remove `continue-on-error` entirely** and rely on the natural failure chain + retry logic.

**Natural failure chain (NO continue-on-error needed):**
```
Infisical down → CORA_API_KEY empty → cora CLI errors → check step fails → job ❌
LLM API 504 → cora retry (2x, 10s sleep) → still 504 → exit 1 → check step fails → job ❌
Cora finds blocking issues → exit 2 → check step detects errors → job ❌
All good → exit 0 → check step passes → job ✅
```

**Acceptable `continue-on-error`:** SARIF upload to GitHub Code Scanning only (nice-to-have, not a gate).

**Why `continue-on-error` was tempting but wrong:**
- Transient LLM 504 errors → retry logic handles this (2x, 10s sleep)
- Infisical self-hosted can be down → if secrets can't be fetched, CI MUST fail — blocking on broken infra is correct behavior
- The "Check for blocking issues" step already only fails on actual code issues (exit 2) — but it needs the review step to have actually run successfully

## Transient LLM Errors (504/502/500)

Cora's LLM API calls can hit transient HTTP errors (504 Gateway Timeout, 502, 500). These are **not** code issues — they're LLM provider instability.

**Pattern:** Retry with backoff in the shell script. Do NOT use `continue-on-error` on the step.

```yaml
# In composite action step — NO continue-on-error:
- name: Run cora review
  id: review
  shell: bash
  run: |
    MAX_RETRIES=2
    for i in $(seq 1 $((MAX_RETRIES + 1))); do
      echo "Attempt $i of $((MAX_RETRIES + 1))..."
      cora review --base "$BASE" --format sarif --severity major --quiet \
        > cora-results.sarif 2>cora-stderr.log
      EXIT_CODE=$?
      # 0 = no issues, 2 = blocking issues found, both are valid completions
      if [ $EXIT_CODE -eq 0 ] || [ $EXIT_CODE -eq 2 ]; then break; fi
      # Check for transient HTTP errors (504, 502, 500)
      if grep -qE "504|502|500|timeout|gateway" cora-stderr.log 2>/dev/null; then
        if [ $i -le $MAX_RETRIES ]; then
          echo "::warning::Cora hit transient HTTP error (attempt $i), retrying..."
          sleep 10
          continue
        fi
      fi
      # Non-transient error — stop retrying
      break
    done
```

**Why NO `continue-on-error`:** The retry loop handles transient errors. Permanent failures (auth, config, persistent 504s) should block the CI. `continue-on-error` would make ALL failures silently pass, defeating the gate.

## .cora.yaml v2 Migration Gotcha

**Symptom:** `cora config validate` fails with: `config parse error: ignore: invalid type: sequence, expected struct IgnoreSection`

**Cause:** Cora v2 changed `ignore` from a YAML list to a struct with `files:` and `rules:` sub-keys.

```yaml
# ❌ v1 (BROKEN in cora v2)
ignore:
  - "node_modules/**"
  - "*.min.js"

# ✅ v2 (REQUIRED)
ignore:
  files:
    - "node_modules/**"
    - "*.min.js"
  rules: []
```

**`pkg/**` should NOT be in ignore:** In Go workspace monorepos (Bond, Gofin), `pkg/` contains in-repo Go libraries that SHOULD be reviewed by cora, not third-party vendored code.

**If you see `no API key found`:** Cora reads provider config from `.cora.yaml` (provider, model, base_url) and only needs `CORA_API_KEY` from env. If `.cora.yaml` has no `provider:` section, it falls back to defaults (openai/gpt-4o-mini) which may not match your endpoint.

## SARIF Upload — Default ON (v0.4+)

As of commit `d704dba`, `upload-sarif` in the cora-review composite action defaults to `true`. SARIF is always uploaded to GitHub Code Scanning unless explicitly disabled:

```yaml
# Default (upload ON):
- uses: ./.github/actions/cora-review
  # no upload-sarif needed — already true

# Opt out (upload OFF):
- uses: ./.github/actions/cora-review
  with:
    upload-sarif: 'false'
```

**SARIF tool branding:** The SARIF output includes `fullName: "codecoradev/cora-cli"` in the driver, so it appears as "Cora (codecoradev/cora-cli)" in GitHub Code Scanning.

**Note:** The upload step uses `continue-on-error: true` (acceptable — SARIF upload is nice-to-have, not a gate).

## LLM Model Compatibility — Z.AI Reasoning Models

**Critical gotcha:** `glm-5`, `glm-5-turbo`, and `glm-5.1` on Z.AI direct endpoints return empty `content` field — all output goes to `reasoning_content` (they are thinking/reasoning models). Cora needs structured JSON in `content`, so these models **don't work directly**.

**Solution:** Use LiteLLM proxy (`http://litellm:4000`) which extracts reasoning output into the `content` field. All `glm-5.x` models work correctly through LiteLLM.

| Endpoint | Model | `content` | Works with Cora? |
|---|---|---|---|
| `api.z.ai/api/coding/paas/v4` | glm-5.1 | Empty (reasoning only) | ❌ |
| `api.z.ai/api/coding/paas/v4` | glm-4.6 | ✅ Has content | ✅ |
| `litellm:4000` | glm-5.1 | ✅ Extracted by proxy | ✅ |

**Recommendation:** All `.cora.yaml` configs should use `base_url: http://litellm:4000` for maximum model compatibility.

## Pre-commit Hook Env Sourcing

**Symptom:** Hook exits with `command not found` errors from random strings in `.env`.

**Cause:** `set -a; source .env` executes shell metacharacters (`&`, `@`, `!`) in env values.

```bash
# ❌ BROKEN — executes metacharacters in ALL env values
set -a
source <local-machine>
set +a

# ✅ SAFE — only exports specific CORA_ vars
while IFS='=' read -r key val; do
    case "$key" in
        CORA_*) export "$key=$val" ;;
    esac
done < <(grep -E '^CORA_' <local-machine> || true)
```

## `on_violation` Config (v0.5+)

**Problem:** Pre-commit hook skips review on oversized diffs (262K > 50K limit) with only a warning. Commits pass without code review.

**Solution:** New `on_violation` field in `hook:` config:

```yaml
hook:
  max_diff_size: 51200
  on_violation: disallow  # NEW: exit 2 (block commit) instead of exit 1 (warn)
```

| Value | Exit Code | Behavior |
|-------|-----------|----------|
| `warn` (default) | 1 | Warning only, commit proceeds — backward compatible |
| `disallow` | 2 | Commit blocked — `git commit --no-verify` override |

**Default is `warn`** — existing repos unaffected. Only blocks when explicitly set to `disallow`.

## `--ci` Flag (v0.5+)

For CI workflows — always review full PR diff regardless of size, hard gate on any findings:

```yaml
# .github/workflows/ci.yml
- run: cora review --ci --base ${{ github.base_ref }} --format sarif --quiet
```

`--ci` behavior:
- **Skips `max_diff_size` check** — CI always reviews full PR diff (no 50K limit)
- **Hard gate on any finding** — exit 2 if ANY issue found (independent of `on_violation` config)
- **NOT for pre-commit hooks** — hooks use `on_violation` config instead

| Scenario | `on_violation` | `--ci` | Exit Code |
|----------|----------------|--------|-----------|
| Normal review, no issues | warn | No | 0 |
| Normal review, issues found | warn | No | 0 (mode=warn) or 2 (mode=block) |
| Oversized diff | warn | No | 1 (error, commit proceeds) |
| Oversized diff | disallow | No | 2 (blocked) |
| Any finding in CI | — | Yes | 2 (hard gate) |
| No findings in CI | — | Yes | 0 |

## Blocking vs Non-blocking Exits

| Exit Code | Meaning | Should Block? |
|-----------|---------|---------------|
| 0 | No issues | No |
| 1 | Cora error (config, API, network) or oversized diff with `on_violation: warn` | **Yes** (retry handles transient, persistent = fail) |
| 2 | Blocking issues found OR oversized diff with `on_violation: disallow` OR any finding with `--ci` | **Yes** |

The "Check for blocking issues" step reads the SARIF output and only `exit 1` when it finds `level: error` results. This means the gate correctly blocks on code issues found by cora, AND on persistent infrastructure/API failures.
