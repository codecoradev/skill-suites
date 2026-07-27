# CodeCora Branch Protection Standard

This is the branch protection standard applied across all CodeCora repositories.

## Workflow

```
feature/xxx  →  PR  →  develop  →  PR  →  main  →  tag (release)
```

## Branches

| Branch | Role |
|--------|------|
| `develop` | Default branch. All integration happens here. |
| `main` | Release branch. Merged from `develop` via PR only. |

## Protection Rules

Both `develop` and `main` have identical protection:

| Setting | Value |
|---------|-------|
| Require PR | Yes |
| Required approvals | 0 |
| Dismiss stale reviews | No |
| Require code owner reviews | No |
| Enforce admins | Yes |
| Allow force pushes | No |
| Allow deletions | No |

## Release Flow

1. Feature branches merge to `develop` via PR
2. Maintainer creates release PR: `develop` → `main`
3. After merge to `main`, create version tag (e.g. `v1.0.0`)
4. Tags are only created from `main` — never from `develop`

## Repos Using This Standard

All public CodeCora repositories:

uteke, cora-code, covecto, corin, sinau-lms, coflui, titen, trapfall, rungu, drawover, skill-suites, cora-review-action, codecora-theme, website

Private repositories (nginjen, cora-api, web-landing, hompimpah, cira, marketing, .github, demo-repository) require GitHub Pro for branch protection and cannot use this standard on a free plan.
