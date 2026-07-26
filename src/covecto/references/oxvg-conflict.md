# oxvg Transitive Dependency Conflict

**Date discovered:** 2026-07-22  
**Affected crate:** `oxvg_optimiser` (depends on `oxvg_ast v0.0.5`)  
**Status:** Unresolvable — DO NOT USE

## Error

```
error[E0277]: the trait bound `cssparser::...: ...` is not satisfied
```

## Root Cause

```
oxvg_ast v0.0.5
  └── cssparser 0.34.0

lightningcss (alpha, pulled by oxvg_ast)
  └── cssparser 0.33.0
```

Both `cssparser 0.34.0` and `0.33.0` are required simultaneously. Rust's semver resolver cannot satisfy both in the same dependency graph.

## Why It Can't Be Fixed

1. Only `oxvg_ast v0.0.5` exists on crates.io — no newer version with the fix
2. No feature flag on `oxvg_ast` to disable `lightningcss`
3. `lightningcss` is not a direct dependency — it's transitive through `oxvg_ast`
4. Pinning `cssparser = "0.34"` breaks `lightningcss`; pinning `0.33` breaks `oxvg_ast`

## Workaround

Write a lightweight custom SVG optimizer instead. For generated SVGs (vtracer/pngtosvg output), target these optimizations:

| Optimization | Impact | Difficulty |
|-------------|--------|------------|
| Remove XML prolog `<?xml ...?>` | Low | Trivial |
| Remove comments `<!-- ... -->` | Low | Trivial |
| Remove `<metadata>`, `<title>`, `<desc>` | Medium | Easy |
| Remove empty self-closing `<g .../>`, `<defs/>` | Medium | Easy |
| Shorten numbers (`1.000` → `1`) | **High** | Easy |
| Collapse whitespace | Low | Trivial |
| Remove unused attributes (`id`) | Low | Medium |

The "shorten numbers" optimization alone typically saves 15-30% of SVG file size for vtracer output.