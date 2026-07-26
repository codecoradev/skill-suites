# CI Setup — Composite Action, Org Secrets, Adoption

## Quick Setup

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
      - uses: codecoradev/cora-review-action@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          cora-api-key: ${{ secrets.CORA_API_KEY }}
          cora-base-url: ${{ secrets.CORA_BASE_URL }}
          cora-model: ${{ secrets.CORA_MODEL }}
```

## Org Secrets (codecoradev)

| Secret | Description |
|--------|-------------|
| `CORA_API_KEY` | LLM API key |
| `CORA_BASE_URL` | LLM endpoint |
| `CORA_MODEL` | Model ID |

## Key Pitfalls

1. **Composite actions CANNOT access `secrets.*`** — parent workflow must pass as `inputs`
2. **`|| true` swallows LLM failures** — use `; EXIT_CODE=$?` + fail when non-zero AND empty SARIF (<10 bytes)
3. **Fork PRs can't get OIDC tokens** — GitHub security by design
4. **Never replace existing review workflows** — ADD `cora-review.yml` alongside
5. **`.cora.yaml` v2 `ignore` requires struct:** `ignore: { files: [...], rules: [] }`
6. **Always SHA-pin actions** — tags can be reassigned

## CI Failure Detection

```bash
cora review ... > cora-results.sarif 2>cora-stderr.log; EXIT_CODE=$?
SARIF_BYTES=$(wc -c < cora-results.sarif)
if [ "$EXIT_CODE" -ne 0 ] && [ "$SARIF_BYTES" -lt 10 ]; then
  echo "::error::Cora review failed (exit=$EXIT_CODE, $SARIF_BYTES bytes)."
  exit 1
fi
```

## Node 24 Migration

Set `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` in every workflow. Bump `actions/upload-artifact` to `@v7`.

## Pinned Action SHAs (verify before use)

| Action | SHA |
|--------|-----|
| `actions/checkout` v5.0.0 | `08c6903cd8c0fde910a37f88322edcfb5dd907a8` |
| `actions/github-script` v9.0.0 | `d746ffe35508b1917358783b479e04febd2b8f71` |
| `github/codeql-action/upload-sarif` v4.36.0 | `f52b05f4acaaa234e44466e66d29050e135ea9ef` |

See `ci-setup-and-pitfalls.md` in `devops/cora-cli` references for full details (being consolidated).
