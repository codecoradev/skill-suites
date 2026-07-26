# Phase 1 Implementation Notes

## Source

PR #354 (`feat/phase1-static-token-embedding`), merged Jul 22 2026.

## Key Decision: Vendored vs Re-extraction

Original plan: run extraction script locally (needs GPU, ~6-10h CPU on 4-core VM).
Actual: vendored pre-built `code_vectors.bin` from CBM repo. Same model, same format.
No extraction needed unless vocab changes.

## Delegation Pitfall

Parallel `delegate_task` calls overwrote `src/embed/tokens.rs` — one wrote
nomic-embed-code approach, the other wrote hashing trick. The second clobbered
the first. **Lesson: don't parallel-delegate writes to the same file.**
Resolution: kept both approaches as dual backends in separate files.

## Size Correction

The skill previously said ~12MB. Actual size is ~30MB (40,856 × 768 bytes + 8 header = 31,377,416 bytes).
The 12MB figure was from CBM docs assuming a smaller vocab subset.

## File Structure Added

```
src/embed/
├── mod.rs           # Module root + #![allow(dead_code)]
├── tokens.rs        # Hashing trick backend + tokenizer + split_identifier()
└── token_vocab.rs   # Pre-trained nomic backend + OnceLock token map

vendored/nomic/
├── code_vectors.bin  # 31,377,416 bytes (int8, 40856×768)
├── code_tokens.txt   # 40,856 lines (one token per line)
├── LICENSE           # Apache-2.0 (nomic-embed-code)
└── NOTICE            # Attribution notice

THIRD_PARTY.md         # License attribution
scripts/
└── extract_code_tokens.py  # Reference extraction script (not needed normally)
```

## Test Coverage

36 embed-specific tests: binary format verification, normalization,
similarity quality, tokenizer edge cases (camelCase, snake_case, acronyms),
determinism, dimension checks. 695 total tests pass.