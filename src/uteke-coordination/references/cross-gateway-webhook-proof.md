# Cross-Gateway Webhook Discussion — Live Test Proof

**Date:** Jul 9, 2026  
**Topic:** Dual Model Uteke + Agent Vault Strategy  
**Method:** Cross-gateway webhook (uteke_coord route)  
**Participants:** research-agent (orchestrator) + finance-agent + legal-agent + marketing-agent + ops-agent  
**Rounds:** 3  
**Outcome:** UNANIMOUS APPROVE WITH CONDITIONS

## Infrastructure Verified

| Agent | Port | Gateway PID | Session Created | LLM Processed | Tools Used |
|-------|------|-------------|:-:|:-:|:-:|
| finance-agent | 8645 | 469802 | ✅ | ✅ | knowledge_search, working_get |
| legal-agent | 8654 | 469806 | ✅ | ✅ | knowledge_search, working_get |
| marketing-agent | 8650 | 566704 | ✅ | ✅ | knowledge_search, skill_view |
| ops-agent | 8653 | 566950 | ✅ | ✅ | knowledge_search, knowledge_remember |

## Key Discovery: Agents Can't Write to Target Room

- Agents use `knowledge` tool (Uteke Hermes plugin), NOT `uteke` CLI
- `knowledge.remember()` stores to agent's own namespace, not the target room
- `uteke room recall` after webhook returns only research-agent's entries
- Workaround: Collect from `state.db` → `messages` table, not from Uteke Room

## Response Collection Pattern

Session key format in `sessions/sessions.json`:
```
agent:main:webhook:webhook:webhook:uteke_coord:{delivery_id}:webhook:uteke_coord
```

Query pattern:
```sql
SELECT content FROM messages
WHERE session_id = (from sessions.json)
  AND role = 'assistant'
ORDER BY rowid DESC LIMIT 1
```

## Round Statistics

| Round | Agents Responded | Total Messages (all agents) |
|-------|:-:|:-:|
| 1 (Opening) | 4/4 | ~107 (avg 26-40 per agent) |
| 2 (Rebuttal) | 4/4 | ~97 |
| 3 (Final) | 4/4 | ~70 |
| **Total** | **12/12** | **~274 + 3 research-agent room entries** |

## Timing

- Webhook send: ~0.1s (all 4 agents parallel)
- Agent processing: ~30s (session created + LLM + tools)
- Wait time used: 120s (generous buffer)
- Total discussion time: ~7 minutes (3 rounds × ~2 min each)

## Decision Outcome

| Decision | Verdict |
|----------|---------|
| Uteke v1.0 = lean memory, no gen LLM | ✅ Unanimous |
| Agent Vault = first-class plugin with SecureStorageInterface | ✅ Unanimous |
| Security requirements = mandatory interface spec | ✅ Unanimous (legal-agent non-negotiable) |
| Generative LLM = v1.5+ query expansion only | ✅ Unanimous |
| Vault ships disabled by default, zero-config onboarding | ✅ Unanimous (marketing-agent condition) |

## Conditions Per Agent

- finance-agent: Mandatory default vault plugin, per-agent key cost tracking
- legal-agent: Access logging non-negotiable (UU PDP Pasal 30), liability chain documented
- marketing-agent: Default experience = zero-config, vault opt-in at enable, marketing stays simple
- ops-agent: Migration runbook from env vars, observability metrics, RFC-001 prerequisite

## Comparison: delegate_task vs Cross-Gateway

Same topic, different methods — quality difference was visible:

| Aspect | Cross-Gateway (this test) | delegate_task (typical) |
|--------|:-:|:-:|
| Agent used own memory/knowledge | ✅ Yes (knowledge_search calls) | ❌ No |
| Domain-specific citations | ✅ finance-agent cited UU PDP, cost tracking | ⚠️ Generic |
| Personality authentic | ✅ legal-agent used informal tone, finance-agent used tables | ⚠️ Uniform tone |
| SOUL.md adherence | ✅ Each stayed in lane | ⚠️ Role blur common |
| Total time | ~7 min | ~5 min |
| Infrastructure needed | Running gateways | None |
