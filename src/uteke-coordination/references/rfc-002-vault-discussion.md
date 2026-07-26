# RFC-002: Uteke Vault — 4-Round Multi-Agent Decision Discussion

**Date:** July 9, 2026 | **Room:** `disc:uteke-vault-credential-store` | **Namespace:** cto
**Participants:** research-agent, finance-agent, legal-agent, ops-agent, marketing-agent (5 agents)
**Memories:** 17 (1 research + 4 rounds x 4 agents)
**Verdict:** UNANIMOUS APPROVE — Build P0+P1+P2

## Context

the user asked whether Uteke (Rust memory engine) should also serve as a credential store to replace plaintext `.env` files across the Hermes agent fleet. Quantified problem: 9 `.env` files, 9 unique credential types, 40+ total credential entries, all plaintext.

## Pattern Used: CLI-Direct Multi-Agent Discussion

Orchestrator (research-agent) created the room and seeded research. Each round, 4 agent subagents were dispatched via `delegate_task`. Each subagent recalled the room via `uteke room recall`, analyzed from their role, and stored their response via `uteke remember --room`.

## Round-by-Round Summary

### Round 1: Opening Positions

| Agent | Position | Key Argument |
|-------|----------|-------------|
| **finance-agent** | CONDITIONAL GO (P0-P1 only) | 3-4 weeks too expensive. .env templating script (1 afternoon) solves 80%. Crypto maintenance = perpetual liability. Revenue impact ~zero. |
| **legal-agent** | CAUTION | Crypto is fine but key management is the real risk — `UTEKE_VAULT_MASTER_KEY` env var = same plaintext problem. Interactive unlock required. Audit trail should be P1. |
| **ops-agent** | BUILD P0-P3, defer P4 | Rotation pain is real (edit 5 files, has failed before). Single point of failure is showstopper — requires degraded/offline mode. |
| **marketing-agent** | POSITIONING RISK | Ship as "operator convenience" not "vault/security". GUI = HARD NO. CLI-only. More GitHub stars from search quality, not crypto. |

### Round 2: Synthesis + Rebuttal

Key tensions resolved:
- finance-agent's .env script: Partially solves duplication but not discovery or per-profile scoping. Script wins on speed; vault wins on operational visibility.
- legal-agent's separate SQLite: All agents agreed — `vault.db` separate from memories DB. Isolates corruption blast radius, simplifies backup.
- ops-agent's degraded mode: Clarified as encrypted SQLite decryption (CLI-only, master key required), NOT plaintext cache. 2s timeout requirement.
- marketing-agent's no-GUI: Unanimous agreement. CLI-only is correct UX.

### Round 3: Decision Proposal + Conditional Votes

**research-agent Decision Proposal:**
- Scope: P0+P1+P2 (~550 LOC)
- Master key: Interactive prompt (primary) + `--key-file` escape hatch (headless). NOT env var.
- Timebox: 2 weeks (10 working days). Day 5 P0 gate: miss = kill, ship .env script.
- Build vs .env script: BUILD vault. Ship .env script FIRST as fallback.

| Agent | Vote | Condition |
|-------|------|-----------|
| **finance-agent** | CONDITIONAL ACCEPT | P0 only, 10 days, CodeCora priority if contested |
| **legal-agent** | CONDITIONAL APPROVE | AES-256-GCM mandatory, no env var master key, auto-lock (later deferred) |
| **ops-agent** | CONDITIONAL SHIP | Shadow mode 4 weeks, `UTEKE_VAULT_ENABLED=false` rollback, 2s timeout |

### Round 4: Final Resolution + Sign-Off

**research-agent Final Consensus:**
- P0 (Day 1-6): vault CLI + AES-256-GCM + Argon2id + interactive unlock + separate vault.db (~350 LOC)
- P1 (Day 7-8): encrypted fallback + emergency export (~100 LOC)
- P2 (Day 9-10): Hermes integration (~100 LOC)
- finance-agent kill switch: P0 incomplete by Day 6 → terminate, ship .env script
- legal-agent conditions fully accepted: AES-256-GCM, master key never in env, separate vault.db
- ops-agent conditions accepted: shadow mode 4 weeks, rollback flag, 2s timeout

| Agent | Final Vote |
|-------|-----------|
| finance-agent | ✅ APPROVE |
| legal-agent | ✅ APPROVE (auto-lock deferred acceptable for solo setup) |
| ops-agent | ✅ APPROVE (shadow mode + rollback confirmed) |
| marketing-agent | ✅ APPROVE (CLI-only, operator convenience positioning) |

## Key Design Decisions Locked

1. **Master Key:** Interactive prompt (primary) + `--key-file` for headless. NOT env var.
2. **Storage:** Separate `vault.db` SQLite, chmod 600, isolated from memory DB.
3. **Encryption:** AES-256-GCM + Argon2id KDF (RustCrypto crates, MIT/Apache-2.0).
4. **Degraded Mode:** CLI-only decryption, master key required, 2s timeout.
5. **Migration:** Shadow mode 4 weeks → promote vault → kill .env after 8 weeks incident-free.
6. **GUI:** None. CLI-only.

## P4-P5 Triggers (When to Build More)

| Trigger | What it Unlocks |
|---------|-----------------|
| 2nd human operator | P3 scope + P4 audit |
| Compliance requirement | P4 audit + P5 logging |
| Multi-server deployment | P4 proxy injection |
| Credential leak incident | Immediate full build |
| >10 agents | P3 compartmentalization |

## What Made This Discussion Successful

1. **CLI-direct pattern** — subagents read/wrote to the room themselves via uteke CLI. No coordination.py complexity, no API split issues.
2. **4 rounds was sufficient** — Round 1 (positions) → Round 2 (synthesis) → Round 3 (votes) → Round 4 (sign-off). No need for 7 rounds on a technical RFC.
3. **Structured conditions** — Each agent's approval carried explicit, actionable conditions that research-agent reconciled in Round 4.
4. **Kill switch built in** — finance-agent's Day 5 gate + .env script fallback prevents sunk cost fallacy.
5. **marketing-agent kept scope honest** — "no GUI" and "don't call it a vault" prevented feature creep from Round 1.
