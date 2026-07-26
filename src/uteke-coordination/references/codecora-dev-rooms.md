# CodeCora Dev Uteke Room Architecture

Real example of a 15-room C-level discussion system for CodeCora Dev (github.com/codecoradev).
Created: 3 Juli 2026. Instance: local Uteke (codecoradev/uteke v0.6.3).

## Namespace Structure

```
codecora-strategy/   roadmap-2026-q3, product-prioritization, tech-stack-decisions
repo-uteke/          uteke-v1-planning, embedding-strategy, performance-benchmarks
repo-cora/           cora-roadmap, cora-enterprise
repo-corin/          corin-ux-feedback, corin-architecture
repo-trapfall/       trapfall-onboarding, trapfall-integrations
cross-cutting/       oss-marketing, revenue-model, brand-consistency
```

## Design Rationale

- Per-namespace isolation: Each product family gets its own namespace so agents can scope recall.
- Cross-cutting namespace: Topics that span multiple products (marketing, revenue, brand).
- Room per topic: Each discussion topic gets its own room for clean semantic recall.
- Room titles: Descriptive enough to be self-documenting (include purpose).

## Seeding Pattern

Each room was seeded with one context memory containing real data from GitHub API, git log, and internal analysis. Discussion opinions posted with type "note", proposals with type "decision".

## Discussion Kickoff Pattern

1. Post agenda to main room with type "event", source-type "system"
2. Post opening position per topic to each relevant room with type "note"
3. Tag opinions with "discussion,q3-2026,<topic>" for filtering
4. End with action items summary in main room with type "decision", tags include "waiting-<role>"

## Role Division in This Discussion

| Role | Scope | What They Post |
|------|-------|----------------|
| research-agent | Technical only | Progress updates, blockers, architecture proposals, benchmark plans, implementation details |
| CEO | Direction & decisions | Product priorities, resource allocation, revenue targets, hiring, archival/pause decisions |
| marketing-agent | Marketing & brand | Content strategy, social channels, community building, competitive positioning |
| finance-agent | Financial & revenue model | Revenue model analysis, cost structure, pricing proposals, runway calculation, monetization risk assessment |

**Important:** research-agent does NOT propose pausing/archiving repos, revenue targets, or product prioritization. Those are CEO calls. research-agent reports technically and waits for CEO direction.

### finance-agent Position Pattern (from Q3 2026)

finance-agent posts structured financial analysis with these sections:
- Revenue Model Analysis — Evaluate options (freemium, usage-based, per-seat) with pros/cons for the specific product stack
- Cost Structure — Monthly/quarterly infra cost breakdown (hosting, domains, CI, tools)
- Pricing Proposal — Tier table (Free/Self-Host, Starter, Pro, Enterprise) with price points and conversion math
- Financial Runway — Timeline: Q3/Q4/Q1/Q2 revenue targets, break-even analysis, burn rate
- OSS + Monetization Risk — Community backlash risk, dual licensing conflicts, competing-with-self (free vs cloud)
- Action Items — Setup Stripe, draft ToS, benchmark cloud hosting costs, prepare payment infra

## Technical Report Format (research-agent)

Per-repo update structure posted to relevant rooms:
```
[research-agent Technical Update] <Repo> — <Date>

Activity <timeframe>:
- <commit/fix description>

Open issues (N):
- #NNN: <description>

Blocker: <none / description>

Next: <what research-agent plans to work on, subject to CEO approval>
```

## Metrics At Time Of Setup

7 repos in org, 49 total stars, 7 forks. Primary language: Rust (5/7). Uteke leads with 30 stars (61%). All repos public, open source.

## Q3 2026 Planning Outcome (3 Juli 2026)

All four C-level positions posted to `codecora-strategy/roadmap-2026-q3`. Meeting closed same day.

### Locked Decisions
- No repo archived or paused. All continue build in public.
- Uteke v1.0 mid-September 2026 target approved. 80% research-agent resource.
- Coflui idle (no archive, no pause). Corin maintenance mode.
- Zero revenue pressure Q3. Groundwork only.
- Freemium revenue model: OSS core free + paid cloud convenience layer.

### Open Items (Revisit Later)
- Monorepo vs multi-repo — skip Q3, revisit Q4 if maint cost rises.
- Domain (uteke.codecora.dev vs localhost:8767) — CEO decides next week.
- No hiring Q3. Existing resources sufficient.

### research-agent Sprint Plan
- Week 1-2: Uteke stability (dependabot, CI green) + Cora PR#338 merge
- Week 3-6: Uteke v1.0 sprint (API audit, benchmark, docs)
- Week 7-10: Uteke v1.0 polish + TrapFall MCP server + docs

### marketing-agent Targets
- Stars: 49 → 120+ (2.5x). Primary channels: Dev.to + X/Twitter.
- 2 blog posts/month, 4-6 tweets/week. README overhaul for all 7 repos.

### finance-agent Milestones
- Q3: Setup Stripe account (free). Draft ToS. Track cloud hosting cost benchmark.
- Q4: Beta cloud pricing test. Landing page + waitlist.
- Q1 2027: Pricing live. Target 50 paying users.
