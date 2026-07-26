# 7-Round Multi-Agent Discussion Pattern (Proven)

**Used:** 
- June 21, 2026 — Uteke Optimization & Monetization discussion (3 agents, 7 rounds).
- June 21, 2026 — Touch Bar Product evaluation (5 agents, 7 rounds, 35+ delegate_task calls). CONDITIONAL PROCEED verdict.
- June 21, 2026 — Touch Bar Product re-run (context compaction recovery, Outline publish with prefix fix). Same room continued.

**Pattern:** Hybrid (Coord room for persistence + delegate_task for agent feedback collection).

## Why This Pattern

- `discussion.py` (AgentBoard webhook) is deprecated/removed since Jun 2026.
- uteke-serve room API works but delegate_task subagents cannot access it.
- Solution: Coord stores to room, delegate_task collects feedback, leader posts summaries back to room.

## Workflow

```
1. PREP: Load context (uteke skill, outline docs, knowledge search)
2. CREATE ROOM: coord.discuss(topic, leader_draft)
3. POST LEADER DRAFT: coord.reply_discussion(topic, leader_draft)
4. ROUND 1-7 (iterate):
   a. delegate_task × N agents (parallel, max 3 per batch)
   b. Each agent: goal = "[DISCUSSION ROUND N — Topic]" + role + round focus + prior context
   c. Leader synthesizes round output into summary
   d. coord.reply_discussion(topic, "[Round N] summary_text")
5. CLOSE: coord.close_discussion(topic)
6. SAVE: Write synthesis to local file (Outline can fail — don't let it block)
7. LOG: agent_activity DB entry
```

## Proven Round Structure (Product Evaluation)

This structure works for product/business evaluation discussions. Adapt topics per discussion.

| Round | Focus | Key Question | Outcome |
|-------|-------|-------------|---------|
| 1 | **Problem Framing** | What's the current state? Feasibility? Viability? | Initial scores, identify key tensions |
| 2 | **Architecture & Pivot** | How to build? What's the right approach? Any pivots? | Technical direction, alternative angles |
| 3 | **Market & GTM** | Who are users? How to reach them? | Content/social strategy, demand signals |
| 4 | **Deep Dive** | MVP features? Pricing model? Specifics. | Scoping, pricing tiers, differentiation |
| 5 | **Resolution** | Resolve disagreements. Middle ground? | Convergence begins, decouple decisions |
| 6 | **Synthesis & Blind Spots** | What did we miss? Financial closure. | Final risk register, gate criteria |
| 7 | **FINAL VERDICT** | One clear answer per agent. Next steps. | Unanimous/majority verdict + action plan |

### Alternative: Technical Decision

| Round | Focus |
|-------|-------|
| 1 | Problem statement & constraints |
| 2 | Options exploration |
| 3 | Security/performance implications |
| 4 | Implementation complexity |
| 5 | Migration/rollback strategy |
| 6 | Cross-agent validation |
| 7 | Final recommendation |

## Agent Selection Per Round

Not every agent needs to be in every round. Rotate based on relevance:

- research-agent/finance-agent/Bad Sector — rounds 1-2, 4-7 (technical + financial + challenge)
- Kai/Somad — rounds 3, 5-6 (market + GTM + content)
- All agents — rounds 1 (baseline) and 7 (final verdict)

When using 3 agents (research-agent, finance-agent, Bad Sector), all participate every round. When adding Kai/Somad, batch them in rounds where their expertise matters.

## delegate_task Context Template

```python
delegate_task(tasks=[
    {
        "goal": f"""[DISCUSSION ROUND {N} — {Topic}]
Kamu adalah **{ROLE}**. Round {N} fokus pada: **{round_focus}**

## Context dari Round {N-1}:
{prior_round_summary}

## Round {N} Questions:
1. {question_1}
2. {question_2}
...

Indonesia campur English. MAKSIMAL 800 kata.""",
        "context": "Format terstruktur dengan section jelas.",
        "role": "leaf",
        "toolsets": [],  # add ["web"] if research needed
    },
    # ... up to 3 tasks per batch
])
```

### Key Context Patterns

- Round 1: Include full leader draft with market data, product details, constraints.
- Rounds 2-6: Include 3-5 sentence summary of EACH agent's position from prior round. Format: "### Agent (Role): Score X/10\n- Key point 1\n- Key point 2"
- Round 7: Include "Full 6-Round Summary" — compressed consensus points + remaining disagreements.

## Consensus Tracking

Track convergence across rounds:
- Round 1: Agents often diverge (e.g., research-agent 4/10, finance-agent 4/10, Bad Sector KILL)
- By Round 5: Usually converging (e.g., all CONDITIONAL PROCEED)
- Round 7: Should be unanimous or near-unanimous

**If agents don't converge by Round 5**, the discussion has a fundamental disagreement that the user needs to decide. Don't force consensus — document the disagreement clearly.

## Post-Discussion Steps

### 1. Synthesis File (REQUIRED)
Save to `~/profiles/{agent}/discussion-synthesis-{topic}.md`. Structure:
- Executive Summary (verdict + key numbers)
- Round-by-Round Summary
- Hard Consensus Points
- Remaining Disagreements (for the user)
- Decision Gates
- Risk Register
- Next Steps

### 2. Outline Publish (OPTIONAL — may fail)

**Outline publish can fail independently** — save synthesis locally FIRST, then attempt Outline.

**Proven publish pattern (Jun 2026):**
```python
# Use Pattern C from outline skill: env_loader + urllib.request
# Write as .py file (NOT heredoc — heredoc fails in terminal)
# Key: endpoint needs "/" prefix (BASE + "/" + endpoint, not BASE + endpoint)
import sys
sys.path.insert(0, "~/scripts")
from env_loader import get_env
# Then use outline_post() or inline urllib.request
# Use outline skill's references/code_examples.md for full patterns
```

**Common Outline publish pitfalls:**
- `/` prefix required before endpoint name (e.g., `BASE + "/documents.create"`)
- `python3 << 'PYEOF'` heredoc in terminal fails — write `.py` file then `python3 file.py`
- Raw `.env` parsing truncates key at `...` bytes — use `env_loader.get_env()` instead
- Rate limit returns 404 (not 429) — add `time.sleep(1)` between sequential writes
- Content with code blocks (triple backticks) breaks inline Python strings — use file-based approach
- See outline skill `references/code_examples.md` for Pattern C (env_loader) and Pattern D (curl + printf hex)

### 3. Activity Log
```python
import sqlite3, json, uuid
from datetime import datetime, timezone, timedelta
WIB = timezone(timedelta(hours=7))
DB_PATH = "~/hermes_memory.db"
conn = sqlite3.connect(DB_PATH, timeout=10)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute(
    "INSERT INTO agent_activity (id, agent, action, target, details, status, created_at) VALUES (?,?,?,?,?,?,?)",
    (str(uuid.uuid4())[:8], "cto", "multi_agent_discussion", "topic-name",
     json.dumps({"rounds": 7, "participants": [...], "verdict": "..."}, ensure_ascii=False),
     "success", datetime.now(WIB).strftime("%Y-%m-%dT%H:%M:%S+07:00")))
conn.commit(); conn.close()
```

## Key Learnings

1. **delegate_task is reliable** for multi-agent simulation. Each agent gets isolated context — no bleeding between rounds.
2. **Max 3 concurrent tasks** — for 4+ agents, batch into groups.
3. **Context compaction matters** — after ~3 rounds, summarize prior rounds into 2-3 sentences per agent per round.
4. **Room is the source of truth** — post summaries so any agent can recall later.
5. **PYTHONPATH needed** — `sys.path.insert(0, '~/scripts')` before importing `coordination`.
6. **Bad Sector role is essential** — without devil's advocate, groupthink dominates. Always include contrarian voice.
7. **Verdicts converge naturally** — don't force consensus early. Let agents evolve positions through rounds.
8. **"CONDITIONAL PROCEED" is the most common verdict** — it's the rational outcome when risks are manageable but real. Document the conditions clearly.
9. **Save synthesis locally before Outline** — Outline publish can fail independently due to API timeouts, credential masking, etc.
10. **800 word limit per agent response** — keeps responses focused and prevents context bloat in later rounds.
11. **Context compaction can occur mid-discussion** — if Hermes compacts context mid-turn, the compaction summary carries all prior state. Read the "Historical In-Progress State" and "Historical Remaining Work" sections carefully before resuming. Don't re-do completed work; pick up from where the summary says you left off.
12. **When resuming after compaction, verify room state first** — check what rounds have been posted to the room via `coord` methods before repeating work. The room is the source of truth.
13. **Investigate before discussing** — if the discussion topic involves a factual claim about codebase behavior, verify the claim first (grep source, check files). A wrong premise wastes entire discussion rounds. See "Investigate Before Discuss" section in SKILL.md.
14. **3-round pattern works for technical investigations** — for focused technical decisions, 3 rounds (positions -> synthesis -> decision) is sufficient. Don't default to 7 rounds for everything. See the "3-Round Hybrid Pattern" section in SKILL.md.
15. **Predictable roles can be posted directly** — legal-agent's position is often predictable (compliance = SHA256 mandatory, etc.). Post it directly via API instead of using a delegate_task slot, freeing the slot for agents with more variable positions.
16. **Verify deployment context before discussing** — Bare metal vs Docker vs CI changes everything. A code-level fix (Rust engine.rs) is irrelevant if the problem is in Docker image build (Dockerfile + release.yml). Ask the user to confirm context early. A single "ini di Docker" clarification can save an entire round of misguided discussion.
17. **CLI `uteke room recall` can timeout on large rooms (180s default)** — When using the CLI-based discussion pattern (not uteke-serve API), `uteke room recall` on rooms with 20+ memories can timeout. Workaround: use the uteke-serve HTTP API (`curl -X POST http://127.0.0.1:8767/room/recall`) which is faster, or use `uteke remember` CLI to write (one command per memory, typically fast) and read via API.
18. **uteke-serve API `tags` parameter is a JSON array, not string** — When posting memories via the HTTP API, `tags` must be `["tag1", "tag2"]` not `"tag1,tag2"`. A string value causes `"invalid type: string ... expected a sequence"` JSON parse error. Also, the `/room/recall` endpoint requires a `query` field — there is no chronological "list all" endpoint (that's the separate `GET /room/memories` endpoint added in PR #570).
19. **uteke-serve and CLI binary use SEPARATE storage backends** — `uteke remember` CLI writes to `~/.uteke` (local file-based store). `curl POST http://localhost:8767/remember` writes via uteke-serve (which may use the same `~/.uteke` if configured, but verify). Don't assume data written via one is visible to the other without checking.
20. **Hermes kanban idempotency keys are board-scoped** — When using `hermes kanban create --idempotency-key`, the key is checked against the current active board's DB only (`~/kanban/boards/{slug}/kanban.db`), NOT the global `kanban.db`. Scripts that sync external data to kanban must: (a) add `"board": "slug"` to their config, (b) run `hermes kanban boards switch {slug}` before creating tasks, and (c) check idempotency keys against BOTH the board-specific AND global DBs. Without this, duplicate tasks can appear across boards or existing tasks won't be detected as duplicates on the current board.
21. **GitHub issues belong to the correct repo** — Infrastructure bugs (Hermes agent config, webhook templates, coordination scripts) go to `codecoradev/uteke`, NOT to product repos (corin, bond, etc.). Server-side runtime config changes (`webhook_subscriptions.json`) don't need GitHub issues at all — they're hot-reloaded runtime files, not source code. Only open GitHub issues for changes that require a PR (source code, docs, config tracked in git).

## Anti-Patterns

- ❌ Trying to import `discussion.py` — it's gone.
- ❌ Expecting delegate_task subagents to read from uteke-serve — they can't.
- ❌ Passing 10+ rounds of context verbatim — summarize after 3-4 rounds.
- ❌ Running 4+ delegate_tasks in one batch — max 3 concurrent.
- ❌ Skipping Bad Sector/contrarian role — groupthink kills discussion quality.
- ❌ Forcing consensus in Round 1-3 — let disagreement surface before resolving.
- ❌ Blocking on Outline publish — save locally first, Outline is bonus.
- ❌ Using web_search/web_extract in delegate_task — use fc.py patterns or toolsets=["web"].
- ❌ Parsing `.env` with string splitting for Outline key — use `env_loader.get_env()` (binary-mode read avoids truncation at `...` byte sequence).
