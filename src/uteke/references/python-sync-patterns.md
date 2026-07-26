# Python REST API Patterns for Uteke

Proven patterns for interacting with `uteke-serve` from Python (stdlib only, no deps).

## Important: Namespace Not in POST /remember Body

The REST API does **not** accept a `namespace` field in the JSON body for `POST /remember`. Namespace is determined by server config. For isolation/filters, use **tags** instead.

## Minimal HTTP Client (stdlib)

```python
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json

UTeke_BASE = "http://127.0.0.1:8767"

def uteke_api(method: str, path: str, body: dict | None = None, timeout: int = 10):
    url = f"{UTeke_BASE}{path}"
    payload = json.dumps(body).encode() if body else None
    req = Request(url, data=payload, method=method, headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())
```

## Deduplication Before Remember

Always recall first to avoid duplicate memories:

```python
def is_already_synced(name: str, description: str = "", threshold: float = 0.95):
    query = f"{name}: {description}" if description else name
    hits = uteke_api("POST", "/recall", {"query": query, "limit": 3})
    for hit in hits:
        if hit.get("score", 0) >= threshold:
            tags = hit.get("tags", [])
            if f"name:{name}" in tags:
                return True
    return False
```

## Batch Sync Pattern (proven: 509+ skills)

Pattern used in `~/scripts/sync_skills_to_uteke.py`:

1. Walk source directory recursively for target files
2. Parse frontmatter for name/description (minimal regex, no PyYAML)
3. **Batched dedup check** — separate phase: recall each skill name (limit=1), collect already-synced names into a set. Configurable batch size via `--batch-size` (default: 50).
4. **Sync only new/changed** — filter out already-synced names, then remember only the remainder.
5. Content truncated to 2000 chars with `[TRUNCATED — original was N characters]`
6. Tags: `[hermes-skills, skill, name:<name>, category:<cat>]` for filtering
7. Metadata: `{source: rel_path, synced_at: ISO_timestamp, skill_name}`

### Why Not Sequential Per-Skill Dedup?

Old approach: for each skill → recall(limit=3) → check similarity → skip or remember. With 509 skills, this means 509+ API calls in the dedup phase alone, each taking ~100-200ms → total ~60-100s. Add the sync phase for new skills and the Hermes cron 120s timeout is easily exceeded.

New approach: two-phase (dedup check → sync). Dedup check uses recall(limit=1) per skill (faster, no need for top-3). Only skills NOT in the synced set get remembered. For typical daily runs where <5 skills changed, this completes in ~30s total.

### Flags

| Flag | Effect |
|------|--------|
| `--batch-size N` | Dedup check batch size (default: 50) — just for progress reporting, each skill is recalled individually |
| `--skip-dedup` | Skip dedup entirely — sync ALL skills (fastest when force-resyncing) |
| `--force` | Same as old: skip dedup, resync everything |
| `--dry-run` | Preview without writing |
| `--verbose` | Per-item output |

### Frontmatter Parser (stdlib only)

```python
import re

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
YAML_FIELD_RE = re.compile(
    r"^(name|description)\s*:\s*(?:(?P<q>['\"])(.*?)(?P=q)|(.+))$",
    re.MULTILINE,
)

def parse_frontmatter(text):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    result = {}
    for match in YAML_FIELD_RE.finditer(m.group(1)):
        val = match.group(2) if match.group(2) is not None else match.group(3)
        if val:
            result[match.group(1)] = val.strip()
    return result
```

### Truncation Helper

```python
def truncate(content: str, limit: int = 2000) -> str:
    if len(content) <= limit:
        return content
    return content[:limit] + f"\n\n[TRUNCATED — original was {len(content)} characters]"
```

## CLI Flags for Batch Scripts

Standard pattern: `--dry-run` (preview), `--verbose` (per-item), `--force` (skip dedup). Exit 0 success, 1 on errors. Summary at end with counts.

## Error Handling

`uteke_api()` raises `RuntimeError` with HTTP status/body or connection reason. Callers catch `RuntimeError` and return False/continue — don't crash the batch.
