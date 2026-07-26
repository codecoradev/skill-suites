# 7-Round Multi-Agent Discussion Pattern

## When to Use

Multi-agent discussion for product evaluation, technical decisions, or strategic planning. 3-7 agents, 7 rounds, verdict at the end.

For focused technical decisions, 3 rounds (positions, synthesis, decision) is sufficient. Don't default to 7 rounds for everything.

## Workflow

1. PREP: Load context (skill, docs, knowledge search)
2. CREATE ROOM: coord.discuss(topic, leader_draft)
3. POST LEADER DRAFT: coord.reply_discussion(topic, leader_draft)
4. ROUND 1-7 (iterate):
   a. delegate_task x N agents (parallel, max 3 per batch)
   b. Each agent: goal = "[DISCUSSION ROUND N, Topic]" + role + round focus + prior context
   c. Leader synthesizes round output into summary
   d. coord.reply_discussion(topic, "[Round N] summary_text")
5. CLOSE: coord.close_discussion(topic)
6. SAVE: Write synthesis to local file
7. LOG: Activity DB entry

## Proven Round Structure (Product Evaluation)

| Round | Focus | Key Question | Outcome |
|-------|-------|-------------|--------|
| 1 | Problem Framing | Current state? Feasibility? | Initial scores, key tensions |
| 2 | Architecture | How to build? Pivots? | Technical direction |
| 3 | Market | Users? Reach? | Content strategy |
| 4 | Deep Dive | MVP features? Pricing? | Scoping, pricing |
| 5 | Resolution | Resolve disagreements | Convergence begins |
| 6 | Synthesis | What did we miss? | Risk register |
| 7 | VERDICT | One clear answer per agent | Verdict + action plan |

## Key Learnings

1. delegate_task is reliable. Each agent gets isolated context.
2. Max 3 concurrent tasks. For 4+ agents, batch into groups.
3. Summarize prior rounds after 3-4 rounds to prevent context bloat.
4. Room is the source of truth. Post summaries for later recall.
5. Include a contrarian role. Without it, groupthink dominates.
6. Verdicts converge naturally. Don't force consensus early.
7. CONDITIONAL PROCEED is the most common rational outcome.
8. 800 word limit per response keeps things focused.
9. If agents don't converge by Round 5, document the disagreement for the user.
10. Save synthesis locally before publishing externally.

## Anti-Patterns

- Passing 10+ rounds of context verbatim. Summarize after 3-4 rounds.
- Running 4+ delegate_tasks in one batch. Max 3 concurrent.
- Skipping contrarian role. Groupthink kills discussion quality.
- Forcing consensus in Round 1-3. Let disagreement surface first.
- Blocking on external publish. Save locally first.
