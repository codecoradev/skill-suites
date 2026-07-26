# CI Setup & Pitfalls — Composite Action, Org Secrets

## CI Composite Action Setup

Use the composite action at `.github/actions/cora-review/action.yml` (copy from `templates/action.yml` in this skill).

### Key Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `base-branch` | `origin/develop` | Branch to diff against |
| `severity` | `major` | Min severity to report |
| `cora-version` | `latest` | cora-cli version tag |
| `upload-sarif` | `false` | Upload SARIF to Code Scanning |
| `github-token` | Required | `${{ secrets.GITHUB_TOKEN }}` |
| `cora-api-key` | Required | LLM API key |
| `cora-base-url` | Required | LLM endpoint |
| `cora-model` | Required | Model ID |

## Composite Action `secrets.*` Limitation

GitHub Actions composite actions CANNOT access `${{ secrets.* }}` context. Only `reusable workflows` and direct `steps` can access secrets.

When a composite action needs secrets, the parent workflow must pass them as `inputs`:

```yaml
# Workflow caller — HAS access to secrets
- uses: ./.github/actions/cora-review
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    cora-api-key: ${{ secrets.CORA_API_KEY }}
    cora-base-url: ${{ secrets.CORA_BASE_URL }}
    cora-model: ${{ secrets.CORA_MODEL }}
```

Then inside `action.yml`, reference them as `${{ inputs.github-token }}`.

## Common CI Pitfalls

### 1. Base Branch Mismatch

If your repo uses `main` instead of `develop`, update `base-branch`:

```yaml
with:
  base-branch: origin/main
```

### 2. SARIF Upload Requires Permissions

```yaml
permissions:
  contents: read
  security-events: write
```

### 3. cora-cli Not Found in PATH

Composite action installs cora-cli via `cargo install`. If build fails (missing system deps), add a setup step:

```yaml
- uses: dtolnay/rust-toolchain@stable
- run: cargo install cora-cli --locked
```

### 4. API Key in org-level secrets

For multi-repo setups, store `CORA_API_KEY` as an org-level secret and reference via `${{ secrets.CORA_API_KEY }}`. Works across all repos in the org.

### 5. SARIF Upload to Wrong Repo

`upload-sarif: true` uploads to the repo running the workflow. For forked PRs, SARIF upload fails silently (security restriction). Only runs on base repo PRs.

### 6. Review Comment Format

Cora posts review comments using GitHub PR review API. Comments appear as inline annotations. If comments don't appear, check that `github-token` has `pull-requests: write` permission.

## Minimal Workflow Example

```yaml
name: Code Review
on:
  pull_request:
    branches: [main, develop]

permissions:
  contents: read
  pull-requests: write
  security-events: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: ./.github/actions/cora-review
        with:
          base-branch: origin/main
          github-token: ${{ secrets.GITHUB_TOKEN }}
          cora-api-key: ${{ secrets.CORA_API_KEY }}
          cora-base-url: ${{ secrets.CORA_BASE_URL }}
          cora-model: ${{ secrets.CORA_MODEL }}
          upload-sarif: true
```
