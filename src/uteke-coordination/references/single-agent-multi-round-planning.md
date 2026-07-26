# Single-Agent Multi-Round Product Planning Pattern

**Used:** Jul 2026 — Cora.ai API Platform Strategy (5 rounds, 1 agent role-rotating research-agent/finance-agent).

**Pattern:** One agent writes all discussion rounds via `coord.reply_discussion()`, role-playing different C-level perspectives. No delegate_task needed when the agent has full domain expertise for all roles.

## When to Use

- Product planning where one agent has deep knowledge across all dimensions (technical + financial + DX)
- Multi-round structured analysis that needs persistence in a Uteke room
- Faster than delegate_task pattern when cross-validation isn't needed
- Draft/blueprint generation before external review

## Workflow

```
1. Create room: coord.discuss(topic, opening_position)
2. For each round:
   a. Write comprehensive round content (2,000-4,000 words per round)
   b. Include [Round N | ROLE | tags] prefix in message
   c. coord.reply_discussion(topic, round_content)
3. Close: coord.close_discussion(topic, summary)
```

## Proven Round Structure (API Platform Planning)

| Round | Role | Focus | Output |
|-------|------|-------|--------|
| 1 | finance-agent | Pricing, business model, coins | Tier structure, coin pricing, payment methods |
| 2 | marketing-agent | Marketing, GTM, launch channels | Launch strategy, content plan, community |
| 3 | research-agent | Architecture, API gateway, infra | Language choice, auth, rate limiting, DB schema, cold start |
| 4 | finance-agent | Financial model, unit economics | P&L projection, break-even, churn, sensitivity |
| 5 | research-agent | SDK design, developer experience | Python SDK, REST API, webhooks, docs, DX comparison |

## Content Quality Checklist

Each round should include:
- **Concrete numbers** — dollar amounts, request volumes, percentages, timelines
- **Tables** — comparison matrices, pricing tiers, P&L projections
- **Code examples** — SQL schemas, Go code snippets, Python SDK usage, curl commands
- **ASCII diagrams** — architecture flow diagrams showing request routing
- **Trade-off analysis** — explicit Go vs Rust vs Node.js comparison with decision rationale
- **Error handling** — retry policies, timeout strategies, error code tables
- **Monitoring plan** — metrics to track, alert thresholds, tooling stack
- **Sensitivity analysis** — worst-case scenarios, break-even calculations, risk modeling

## Pitfall: Existing Room Content Quality

When writing rounds to a room that already has content from a previous session:

1. **Always check existing content first** — `coord._room_recall(room, limit=10)` to see what's there
2. **Look for corruption artifacts** — `/usr/bin/bash` in dollar amounts (from shell escaping), truncated content, duplicate entries
3. **Decision: overwrite or append** — If existing content has quality issues (artifacts, truncated, incomplete), write fresh rounds rather than trying to patch
4. **Duplicates are acceptable** — Uteke rooms are append-only. Better to have duplicate good content than to leave corrupted content as the latest entry
5. **Verify after writing** — `coord.get_discussion_summary(topic)` to confirm new rounds landed

## Pitfall: Dollar Amounts in Terminal Content

When writing content with `$` signs via Python heredoc (`<< 'PYEOF'`), bash may interpret `$0.01` as a variable. This produces `/usr/bin/bash.01` in the stored content. 

**Fix**: Use single-quoted heredoc (`<< 'PYEOF'`) to prevent variable expansion. Already standard practice — just verify stored content doesn't contain artifacts.

## coordination.py Pattern

```python
import sys; sys.path.insert(0, '~/scripts')
from coordination import Coord
coord = Coord(agent='cto')

# Check existing content first
result = coord._room_recall('disc:api-platform-strategy', limit=10)

# Write each round
round_content = """[Round N | research-agent | architecture, api-gateway, cold-start]

# Round Title

## Section 1
...comprehensive content (2,000-4,000 words)...
"""

result = coord.reply_discussion(topic='api-platform-strategy', message=round_content)
print(f"Round N: {result.get('exit_code')}")

# Verify
summary = coord.get_discussion_summary('api-platform-strategy')
print(f"Total memories: {summary['data']['total_memories']}")
```

## Proven 8-Round Pattern (Cora.ai API Platform, Jul 2026)

Extended from 5 rounds to 8 rounds. Rounds 1-2 used delegate_task. Rounds 3-5 used delegate_task batch A (succeeded). Rounds 6-8 delegate_task batch B timed out — fell back to manual terminal writes.

| Round | Role | Topic | Method |
|-------|------|-------|--------|
| 1 | finance-agent | Pricing, business model, coins | delegate_task |
| 2 | marketing-agent | GTM, branding, launch | delegate_task |
| 3 | research-agent | API Gateway Architecture | delegate_task batch A |
| 4 | finance-agent | Financial Model & Unit Economics | delegate_task batch A |
| 5 | research-agent | SDK Design & DX | delegate_task batch A |
| 6 | marketing-agent | Marketing Strategy & Content Plan | Manual (delegate_task timeout) |
| 7 | legal-agent | Legal, Compliance & Risk | Manual (delegate_task timeout) |
| 8 | CEO | Strategic Roadmap & Resources | Manual (delegate_task timeout) |

**Lesson:** For 6+ round discussions, the hybrid approach works best: delegate first 3-5 rounds, then write remaining manually. This avoids repeated timeout cycles.

**Delegate_task batch strategy for long discussions:**
- 3 rounds per batch is the sweet spot (566s for 3 rounds vs 600s timeout)
- Dispatch 2 batches in parallel (max concurrent = 3 delegate_tasks)
- If one batch times out, write remaining rounds directly via terminal + coordination.py
- Always verify room/document after each batch to confirm writes landed

## When NOT to Use This Pattern

- When you need genuine cross-validation from other agents (different perspectives surface blind spots)
- When the finance-agent role requires domain-specific financial expertise the research-agent agent lacks
- When the discussion outcome will drive significant investment decisions (use delegate_task for adversarial review)
- When Bad Sector adversarial review is needed (single-agent pattern can't challenge its own assumptions)
