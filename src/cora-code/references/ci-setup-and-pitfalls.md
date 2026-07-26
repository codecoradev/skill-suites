# CI Setup & Pitfalls — Composite Action, Org Secrets, Adoption

## CI Composite Action Setup

For CI-based review (GitHub Actions), use the composite action at `.github/actions/cora-review/action.yml`.
Copy from `templates/action.yml` in this skill directory.

### CI Action `action.yml` — Key Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `base-branch` | `origin/develop` | Branch to diff against — match repo's default (e.g., `origin/dev` for termul) |
| `severity` | `major` | Min severity to report |
| `cora-version` | `latest` | cora-cli version tag (ALWAYS use `latest`) |
| `upload-sarif` | `false` | Upload SARIF to Code Scanning |
| `github-token` | Required | `${{ secrets.GITHUB_TOKEN }}` for PR comments |
| `cora-api-key` | Required | `${{ secrets.CORA_API_KEY }}` — LLM API key (from org secrets) |
| `cora-base-url` | Required | `${{ secrets.CORA_BASE_URL }}` — LLM endpoint |
| `cora-model` | Required | `${{ secrets.CORA_MODEL }}` — Model ID |

### ⚠️ Composite Action `secrets.*` Context Limitation — CRITICAL

**GitHub Actions composite actions CANNOT access `${{ secrets.* }}` context.** Only `reusable workflows` and `jobs.*.steps` (direct steps) can access secrets. Composite actions only have `inputs`, `env`, and `steps` contexts.

**Implication:** When a composite action needs secrets (e.g., API keys), the **parent workflow** must pass them as `inputs`:

```yaml
# Workflow caller — HAS access to secrets
- uses: ./.github/actions/cora-review
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    cora-api-key: ${{ secrets.CORA_API_KEY }}        # ← pass as input
    cora-base-url: ${{ secrets.CORA_BASE_URL }}      # ← pass as input
    cora-model: ${{ secrets.CORA_MODEL }}             # ← pass as input

# Composite action — receives via inputs, NOT secrets
inputs:
  cora-api-key:
    description: 'LLM API key'
    required: true
runs:
  steps:
    - name: Run cora
      env:
        CORA_API_KEY: ${{ inputs.cora-api-key }}      # ← use inputs
```

**Note:** GitHub automatically masks `secrets.*` values in logs. When passed as `inputs`, the masking still applies — the secret value is never exposed in workflow logs. This is safe.

### Org Secrets Pattern

All repos now use **GitHub org-level secrets** directly (Infisical removed 2026-06-02):

| Secret | Description | Set at |
|--------|-------------|--------|
| `CORA_API_KEY` | LLM API key | Org `codecoradev` (public repos) |
| `CORA_BASE_URL` | LLM API base URL | Org `codecoradev` |
| `CORA_MODEL` | LLM model ID | Org `codecoradev` |
| `CARGO_REGISTRY_TOKEN` | crates.io publish token | Org `codecoradev` |
| `CLOUDFLARE_API_TOKEN` | CF Pages deploy token | Repo or org |
| `CLOUDFLARE_ACCOUNT_ID` | CF account ID | Repo or org |

**Setup per new repo:** Add org secrets in `codecoradev` org settings → "Secrets and variables" → "Actions" → "Organization secrets". Set visibility to "Public repositories" or specific repos.

**⚠️ NEVER replace existing review workflows — this is CRITICAL.** When adding cora review to a repo (especially forked repos with upstream owners), ADD a new workflow file (`cora-review.yml`) alongside existing review workflows. Do NOT modify or delete the upstream's existing review workflow (e.g., Claude Code Review, CodeRabbit). Both reviewers run side-by-side.

**⚠️ NEVER open PR to upstream without local validation first.** Correct sequence: (1) push branch to fork, (2) test CI on fork, (3) verify cora review works, (4) THEN open PR to upstream.

**⚠️ ALWAYS confirm before pushing to external repos — NO EXCEPTIONS.**

### CI Workflow — Standalone Pattern (v3)

**Recommended:** Use a standalone `cora-review.yml` workflow instead of embedding in `ci.yml`:

```yaml
# .github/workflows/cora-review.yml
name: Cora AI Code Review

on:
  pull_request:
    branches: [develop]
    types: [opened, synchronize, ready_for_review, reopened]

concurrency:
  group: cora-review-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read
  security-events: write
  pull-requests: write
  id-token: write

jobs:
  cora-review:
    name: Cora Review
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@08c6903cd8c0fde910a37f88322edcfb5dd907a8 # v5.0.0
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: ./.github/actions/cora-review
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          cora-api-key: ${{ secrets.CORA_API_KEY }}
          cora-base-url: ${{ secrets.CORA_BASE_URL }}
          cora-model: ${{ secrets.CORA_MODEL }}
          upload-sarif: 'false'
```

**Notes:**
- Use SHA-pinned `checkout@v5.0.0` — not tag-only `@v4`
- `persist-credentials: false` for security
- Add `id-token: write` permission if using Infisical OIDC (not needed for org secrets)
- Set `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` in top-level `env:` block (see Node 24 section)

### Adding Cora Review to a Forked Repo (for Upstream PR)

1. **Sync fork first** — `git fetch upstream && git merge upstream/<branch>`
2. **Create feature branch from synced fork** — `git checkout -b feat/cora-review`
3. **Add (NOT replace) workflow** — New file `.github/workflows/cora-review.yml` + composite action
4. **Push to fork, test on fork first** — Verify CI passes on your fork before opening PR
5. **Open PR to upstream** — Upstream must set up their own secrets
6. **PR description MUST list required secrets**

**⚠️ Fork CI vs upstream CI:** `pull_request` on upstream may NOT run for fork PRs. May need `pull_request_target` but has security implications. Test on fork CI first.

### Per-Repo Adoption Config

| Repo | `base-branch` | Pattern | `upload-sarif` |
|---|---|---|---|
| cora-cli | `origin/develop` | Standalone action (`cora-review-action@v1`) | `true` (default) |
| uteke | `origin/develop` | Standalone action (`cora-review-action@v1`) | `true` (default) |
| corin | `origin/develop` | Standalone action (`cora-review-action@v1`) | `true` (default) |
| bond | `origin/develop` | Composite action | `true` |
| gofin-full | `origin/develop` | Composite action | `true` |
| termul | `origin/dev` | Composite action | `true` |

**Pattern:** Repos migrated to `codecoradev/cora-review-action@v1` (standalone published GitHub Action) use `secrets.*` directly in workflow — no composite action wrapper needed. Older repos still use the inline composite action pattern (`.github/actions/cora-review/action.yml`).

### Adoption Steps (per repo)

**For repos using `cora-review-action@v1` (recommended):**
1. Create standalone `.github/workflows/cora-review.yml` with `uses: codecoradev/cora-review-action@v1`
2. Pass `cora-api-key`, `cora-base-url`, `cora-model` from org secrets
3. Set `base-branch`, `severity`, `upload-sarif` as needed
4. Verify with a test PR

**For repos using composite action (legacy):**
1. Copy `action.yml` from `templates/action.yml`
2. Adapt config inputs (base-branch, upload-sarif)
3. Create standalone `.github/workflows/cora-review.yml` (separate from ci.yml)
4. Remove cora-review job from `.github/workflows/ci.yml`
5. Verify with a test PR — confirm Cora Review job runs and passes

### Adoption Pitfalls (learned from cora-cli PR #107)

**1. Checksum file exists but no matching entry:** Guard with `[ -s file ]` AND `grep ... || true` (pipefail-safe).
**2. `grep` inside `$(...)` with pipefail:** Place `|| true` INSIDE the subshell: `EXPECTED=$(grep "pattern" file | awk '{print $1}' || true)`. Placing it outside does NOT work.
**3. Required check context survives workflow extraction:** Job name preserved when extracting to standalone workflow.
**4. Top-level permissions cleanup:** Remove elevated permissions if only needed for cora.

---

## CI Pitfalls

### ⚠️ Silent False Negative — LLM Returns Invalid JSON

**Observed:** uteke PR #94 — cora exits code 1, CI writes `{}` to SARIF, posts "✅ No issues found" — review was never performed.

**Root cause chain:**
1. LLM returns JSON with invalid escape sequences
2. `serde_json` fails to parse → cora exits code 1
3. CI action catches exit code 1, writes `::warning::`
4. SARIF file empty/missing → action writes `{}`
5. GitHub Script posts false "No issues found" comment

**Two-layer fix (Rust-side + CI-side):**

| Layer | Fix | Version |
|-------|-----|---------|
| **Rust: JSON repair** | `repair_invalid_escapes()` — doubles lone `\` before non-JSON-escape chars | v0.1.4 |
| **Rust: auto-retry** | If parse still fails → retry LLM request once | v0.1.4 |
| **CI: stderr capture** | `2>cora-stderr.log` instead of `2>/dev/null` → `::warning::` annotation | v0.1.7 |
| **CI: empty SARIF detection** | File size <10 bytes → "⚠️ Review could not complete" not false "no issues" | v0.1.7 |

### ⚠️ `|| true` Swallows LLM API Failures — Must Be Blocking

**Observed:** PR #142 — `|| true` allowed LLM API failures (504, auth errors) to produce empty SARIF while job showed SUCCESS.

**Fix:** Capture exit code, fail job only when cora exits non-zero AND SARIF is empty:

```bash
cora review ... > cora-results.sarif 2>cora-stderr.log; EXIT_CODE=$?
SARIF_BYTES=$(wc -c < cora-results.sarif)
if [ "$EXIT_CODE" -ne 0 ] && [ "$SARIF_BYTES" -lt 10 ]; then
  echo "::error::Cora review failed (exit=$EXIT_CODE, $SARIF_BYTES bytes)."
  exit 1
fi
```

**Behavior matrix:**

| Scenario | `EXIT_CODE` | SARIF | Result |
|----------|-------------|-------|--------|
| LLM API fails (504, timeout, auth) | `!= 0` | `< 10 bytes` | 🔴 **FAIL** |
| LLM fails but partial results | `!= 0` | `≥ 10 bytes` | ⚠️ **Pass** — stderr warning |
| LLM succeeds, no issues | `0` | valid SARIF | ✅ **Pass** |
| LLM succeeds, issues found | `0` | valid SARIF | ✅ **Pass** — blocking check downstream |

**Key insight:** Use `; EXIT_CODE=$?` (semicolon, no pipe) to capture exit code without triggering `set -e`.

### ⚠️ CI Diff Too Large for Default `max_diff_size`

**Observed:** PR #112 — `Error: Diff too large (58118 chars, max 51200)`.

**Fix options:**
1. **`CORA_CONFIG` env var** (works with any version): `printf 'hook:\n  max_diff_size: 200000\n' > .cora-ci.yaml && CORA_CONFIG=".cora-ci.yaml" cora review ...`
2. **`--max-diff-size` CLI flag** (v0.2.0+ only)
3. **`.cora.yaml` config** (affects local pre-commit too — not recommended for CI-only)

### ⚠️ Archived GitHub Actions Orgs — `actions-rs` is Dead

**Observed:** PR #112 — subagent used `actions-rs/audit-check@<SHA>` (archived late 2023).
**Fix:** Use `rustsec/audit-check` (official, maintained by RustSec team).

### ⚠️ `tls_built_in_root_certs(false)` Disables ALL System Roots

**Observed:** PR #112 — Cora self-review caught a 🔴 Error in `REQUESTS_CA_BUNDLE` implementation.
**Fix:** Add custom cert alongside built-in roots — do NOT disable built-in certs:
```rust
// ❌ WRONG — disables ALL system roots
builder = builder.tls_built_in_root_certs(false).add_root_certificate(cert);
// ✅ CORRECT — adds custom cert alongside system roots
builder = builder.add_root_certificate(cert);
```

### ⚠️ `ignore` Crate `WalkBuilder.require_git()` Default

**Observed:** PR #112 — `.require_git(true)` means gitignore rules only applied inside git repos.
**Fix:** Add `.require_git(false)` to apply gitignore rules even outside git repos.

### ⚠️ Pinning `cora-version` to a Specific Tag

**Observed:** uteke action.yml had `cora-version` defaulting to `v0.1.2`.
**Fix:** Always set `cora-version` default to `latest`. Copy template from `templates/action.yml`.

### ⚠️ Cross-Repo CI Action Version Comparison Pattern

| Action | Check |
|--------|-------|
| `actions/checkout` | v4 vs v5 SHA-pinned? |
| `actions/upload-artifact` | v4 vs v7 (v4 deprecated for Node 24)? |
| `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` | Present in env block? (deadline: 2026-06-16) |
| Fallback version in action.yml | Matches latest cora release? |
| Infisical vs org secrets | Which pattern? |

**Fetch remote action.yml without cloning:** `gh api repos/OWNER/REPO/contents/.github/actions/cora-review/action.yml --jq '.content' | base64 -d`

### ⚠️ OIDC Token Unavailable in Two Distinct Scenarios

| # | Scenario | Why OIDC Fails | Fix |
|---|----------|----------------|-----|
| **A** | **Fork PR** | GitHub never generates OIDC token from fork PRs — security by design | **No CI-level fix.** Works after merge. |
| **B** | **Composite action** | Composite action steps don't get OIDC token | Move Infisical step to workflow level |

**How to tell:** If Infisical is inside composite action AND PR is from fork, both apply.

### Fork PR CI Failures — Checklist

| # | Error | Cause | Fix |
|---|-------|-------|-----|
| 1 | `Unable to get ACTIONS_ID_TOKEN_REQUEST_URL` | OIDC unavailable (fork or composite) | After merge (fork), or move to workflow level (composite) |
| 2 | `Missing identity ID` | Secret not set in upstream repo | Upstream owner must add secret |
| 3 | `Resource not accessible by integration` | Fork PR can't write PR comments | `pull_request_target` or PAT |
| 4 | Job runs but shows `skipping` | Branch rules don't require check | Coordinate with upstream owner |

### Hardcoding Infisical Identity ID for Testing — Safe

The identity ID is an identifier, not a secret. Without the GitHub OIDC token (runtime-only), it cannot fetch secrets. Hardcoding for testing on external/fork repos is safe. Use `secrets.INFISICAL_IDENTITY_ID` for production.

### ⚠️ LLM Review False Positives on Dead Code Removal

**Observed:** PR #112 — Cora flagged 3 🔴 Errors on intentional dead code removal.
**Root cause:** LLM reviews diff text only — cannot run `cargo check` or grep callers.
**Handle:** Verify with `cargo check` + `cargo test`. Add explanatory comments for merged match arms. Future: inject static analysis context into prompt (#140).

### Composite Action Pitfalls (v0.1.7+)

17. **Stderr suppression** — `2>/dev/null` discards all error output. Redirect to log file.
18. **Empty SARIF** — Check `sarifFileSize < 10` before "no issues".
19. **Fallback version staleness** — Update after every cora release.
20. **`fs.statSync` crashes when SARIF missing** — Wrap in try/catch.
21. **Pin third-party actions to commit SHA** — Tags can be reassigned.
22. **Pass composite action inputs via env vars** — Avoids "template injection" noise.
23. **Download-to-temp-file pattern** — Never pipe curl directly to tar.
24. **SHA256 checksum verification** — Download checksums, verify before extract.
25. **NEVER fabricate commit SHAs** — Always resolve from GitHub API.
26. **INFISICAL_IDENTITY_ID ≠ Machine ID** — It's the OIDC identity ID.
27. **`grep` exit code 1 with pipefail** — `|| true` INSIDE subshell.
28. **Empty checksums file guard** — Check `[ -s ]` before grep.
29. **`let body;` declaration in GitHub Script** — Prevents redeclaration error in strict mode.
30. **Missing checksum elif vs nested if** — Separate hash mismatch (fatal) from missing entry (warning).

### `.cora.yaml` v1 vs v2 Format — `ignore` Field

**Observed:** Bond PR #248 — v1 list format causes parse error in v0.2+.

```yaml
# ❌ v1 — causes parse error in v0.2+
ignore:
  - "node_modules/**"
# ✅ v2 — cora v0.2+
ignore:
  files:
    - "node_modules/**"
  rules: []
```

**Fix:** Run `cora init --force` for valid v2 template.

### Invalid Top-Level Sections in `.cora.yaml`

**Observed:** Bond had `review: severity, max_issues, focus` — NOT valid.

```yaml
# ❌ WRONG
review:
  severity: major
# ✅ CORRECT
hook:
  min_severity: major
focus:
  - security
```

### Squash Merge vs Regular Merge

Some repos (uteke) disallow merge commits — use `gh pr merge --squash`. Generally preferred: 1 PR = 1 commit.

### `gh pr merge --admin` for Blocked PRs

**Cause A:** Bot review `COMMENTED` state (not `APPROVED`). Fix: `--admin`.
**Cause B:** Branch protection check name vs workflow job name mismatch. Diagnosis: `gh api repos/OWNER/REPO/branches/BRANCH/protection --jq '.required_status_checks.checks[].context'` vs `gh pr checks`. Fix: Update protection rules or use `--admin`.

### Pinned Action SHA Reference (verify before use — SHAs go stale)

| Action | Tag | SHA |
|--------|-----|-----|
| `actions/checkout` | v5.0.0 | `08c6903cd8c0fde910a37f88322edcfb5dd907a8` |
| `actions/github-script` | v9.0.0 | `d746ffe35508b1917358783b479e04febd2b8f71` |
| `github/codeql-action/upload-sarif` | v4.36.0 | `f52b05f4acaaa234e44466e66d29050e135ea9ef` |
| `step-security/harden-runner` | v2 | `ab7a9404c0f3da075243ca237b5fac12c98deaa5` |
| `actions/upload-artifact` | v7 | `b43b2398a3b6af7e2fadae6e8e91770a5e678d21` |

**⚠️ ALWAYS verify SHAs:** `gh api repos/OWNER/ACTION/git/ref/tags/TAG --jq '.object.sha'`

**⚠️ Node 24 migration:** Set `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` in every workflow. Bump `actions/upload-artifact` to `@v7`. Deadline: 2026-06-16.

### v2 Features (over legacy)

| Feature | v2 | Legacy |
|---|---|---|
| Action SHA pinning | ✅ All actions pinned to commit SHA | ❌ Uses tags |
| Checksum verification | ✅ SHA256 verify (graceful if missing) | ❌ No verification |
| Empty SARIF detection | ✅ `< 10 bytes` → warning | ❌ Silent false "no issues" |
| Stderr capture | ✅ `cora-stderr.log` + `::warning::` | Mixed |
| Fallback version | `v0.1.7` + 3x resolve retry | Missing |
| Concurrency control | ✅ Group per ref | ❌ No dedup |
| Standalone workflow | ✅ `cora-review.yml` | ❌ Inline in `ci.yml` |
| LLM API failure blocking | ✅ Exit code capture + empty SARIF → fail | ❌ `|| true` swallows all |
