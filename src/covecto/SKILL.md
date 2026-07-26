---
name: covecto
description: "Covecto — Raster-to-SVG vectorization ecosystem in Rust. Convert images to clean vector graphics."
version: 1.0.0
metadata:
  author: CodeCoraDev
  hermes:
    tags: [covecto, vectorization, raster-to-svg, rust, vtracer, potrace, image-processing]
triggers:
  - image to svg
  - raster to vector
  - vectorize image
  - vtracer
  - potrace
  - image vectorization
  - png to svg
  - svg tracing
  - covecto
---

# Covecto — Raster to SVG Vectorization

**Repository:** https://github.com/codecoradev/covecto

Covecto is a high-performance raster-to-SVG vectorization tool built in Rust. It converts bitmap images (PNG, JPEG, BMP) into clean, scalable SVG vector graphics using advanced tracing algorithms.

Covecto uses a dual-engine approach: vtracer for smooth spline-based vectorization and pngtosvg for pixel-exact reproduction. It includes a lightweight custom SVG optimizer, CLI, and HTTP API.

This skill is a class-level reference for converting raster images (PNG, JPEG, etc.) to vector graphics (SVG). It covers the Rust ecosystem, competitive landscape, architecture patterns, and implementation guidance.

## Ecosystem Overview

### Rust-native Solutions

| Library | Crate | Stars | Approach | Best For |
|---------|-------|-------|----------|----------|
| **vtracer** | `vtracer` | 6.4k | Color quantization + spline fitting, O(n) | General-purpose, fast, color images |
| **PNGToSVG** | `pngtosvg` | 105 | Custom algorithm, pixel-art/alpha-aware | Icons, favicons, simple graphics |
| **logolig** | `logolig` | — | Wraps vtracer internally | Favicon generation (GUI app) |
| ~~**oxvg**~~ | `oxvg_optimiser` | — | ~~SVG optimization (SVGO replacement in Rust)~~ | ❌ **DO NOT USE** — unresolvable transitive dep conflict |

### Non-Rust (for comparison)

| Tool | Language | Notes |
|------|----------|-------|
| **potrace** | C | Classic, grayscale only, mature. C binding available via `potracelib`. |
| **autotrace** | C++ | Centerline + outline tracing. Legacy, maintenance mode. |
| **imagetracerjs** | JavaScript | Pure JS, 4-5x slower than vtracer. |
| **neplextech/vectorizer** | Rust core + napi-rs JS binding | Wraps `visioncortex` crate (vtracer) for Node.js. 201 stars. ~530µs/iter. |

### Architecture Pattern: napi-rs Wrapper

The neplextech/vectorizer pattern is common: write core in Rust, expose to JS via napi-rs.

```
User JS/TS Code
    ↓
napi-rs binding layer (cdylib)
    ↓
Rust core (vtracer / custom)
    ↓
SVG string output
```

**Dependencies for this pattern:**
```toml
[dependencies]
napi = { version = "3", features = ["serde-json"] }
napi-derive = "3"
image = "0.25"
visioncortex = "0.8"  # or custom engine

[build-dependencies]
napi-build = "2"

[lib]
crate-type = ["cdylib"]
```

## Quick Start: Using vtracer in Rust

```rust
use vtracer::convert_image_to_svg;
use image::DynamicImage;

fn vectorize(path: &str) -> String {
    let img = image::open(path).unwrap();
    convert_image_to_svg(
        &img,
        vtracer::ColorMode::Color,
        8,   // color_precision
        4,   // filter_speckle
        45,  // splice_threshold
        60,  // corner_threshold
        vtracer::Hierarchical::Stacked,
        vtracer::PathSimplifyMode::Spline,
        5,   // layer_difference
        5,   // length_threshold
        2,   // max_iterations
    )
}
```

## Quick Start: Using pngtosvg (simpler, icon-focused)

```rust
use pngtosvg::convert_file_to_svg;
use std::path::Path;

fn main() {
    let svg = convert_file_to_svg(Path::new("icon.png")).unwrap();
}
```

## Building a Custom Engine from Scratch

If vtracer doesn't cover your needs (e.g., neural network-based vectorization, centerline tracing for handwriting, specialized output formats):

| Component | Rust Crate | Difficulty |
|-----------|-----------|------------|
| Image decoding | `image` (PNG, JPEG, WebP, BMP, TIFF) | ✅ Trivial |
| Color quantization | `k-means` / custom median-cut | ⚠️ Medium |
| Pixel grouping / layering | Custom (connected components) | ⚠️ Medium |
| Path tracing (contour) | Custom marching squares / potrace algorithm port | 🔴 Hard |
| Spline fitting (Bézier) | `lyon` crate (2D path tessellation) | ⚠️ Medium |
| SVG generation | `svg` crate or manual string builder | ✅ Trivial |
| SVG optimization | `oxvg_optimiser` | ✅ Easy |

**Estimated effort:** 2-4 months for vtracer parity (1 dev full-time). vtracer itself is ~136 commits and mature.

## Performance Benchmarks

From neplextech/vectorizer (i7-14700K, Node 24):

| Tool | Avg Time | Output Size (typical) |
|------|----------|----------------------|
| @neplex/vectorizer (sync) | ~530µs | 1.6-168 KB |
| imagetracerjs | ~2.4ms | 1.1-6.9 MB |
| potrace (trace) | ~3.6ms | 736 B-11.9 MB |

vtracer is **4-7x faster** than JS/C alternatives.

## Decision Guide

| Scenario | Recommendation |
|----------|---------------|
| Need a Rust library | `vtracer` directly — mature, 6.4k stars, O(n) |
| Need Node.js binding | `@neplex/vectorizer` — pre-wrapped, built-in optimizer, TS API |
| Need CLI tool | `vtracer` CLI or `pngtosvg` |
| Build-time asset pipeline (JS) | `@neplex/vectorizer` as devDependency — vectorize + optimize in one call |
| Zero npm, pure CLI | `vtracer` binary + separate `svgo` for optimization |
| Building SaaS/API | Wrap vtracer in Axum API + **lightweight custom optimizer** (not oxvg). ~1 week. See covecto architecture below. |
| Custom algorithm needed | Build from scratch with `image` + `lyon`, but reuse vtracer patterns |
| Grayscale/line-art only | `potrace` via C FFI — best quality for that specific domain |

**vtracer vs @neplex/vectorizer:** Same engine (`visioncortex` 0.8.10), identical SVG output. neplex = NAPI-RS wrapper + built-in oxvg optimizer + Preset enum API. vtracer binary = standalone, raw output only. See [references/neplex-vectorizer.md](references/neplex-vectorizer.md) for API pitfalls.

## Pitfalls

### ⚠️ oxvg Has Unresolvable Transitive Dependency Conflict

`oxvg_ast v0.0.5` → `cssparser 0.34.0`, but its own dependency `lightningcss` (alpha) requires `cssparser 0.33.0`. No newer oxvg version exists, no feature flag to disable lightningcss. **Cannot be used in any project.**

**Fix:** Write a lightweight custom SVG optimizer instead. For vtracer/pngtosvg-generated SVGs, the most impactful optimizations are:
1. Remove XML prolog, comments, `<metadata>`, `<title>`, `<desc>`
2. Remove empty self-closing `<g .../>` and `<defs/>`
3. Shorten numeric values (strip trailing zeros: `1.000` → `1`, `0.500` → `0.5`)
4. Collapse redundant whitespace
5. Remove unused attributes (`id` on non-referenced elements)

This covers 80%+ of SVGO's impact for generated SVGs, with zero external deps beyond `roxmltree` (optional, for XML parsing) or pure string ops. See [references/oxvg-conflict.md](references/oxvg-conflict.md) for full error trace.

### ⚠️ vtracer `ColorImage` is `Vec<u8>` Flat RGBA

vtracer's `ColorImage` uses flat `Vec<u8>` (RGBA interleaved), NOT `Vec<(u8,u8,u8,u8)>`. When converting from `image::RgbaImage`, use `img.as_raw()` directly — it's already in the right layout.

### ⚠️ usvg 0.45 / svg2pdf 0.13 API Gotchas

usvg changed its public API significantly between 0.43 and 0.47. **Always pin `usvg` to match `svg2pdf`'s transitive version** (`svg2pdf 0.13` → `usvg 0.45`).

Key API differences from what docs/blog posts may assume:

| Assumed API | Actual usvg 0.45 API |
|-------------|---------------------|
| `usvg::Fill::Color(c)` / `usvg::Fill::None` | `Fill` is a **struct**. Use `fill.paint()` → `Paint::Color(c)` |
| `usvg::Stroke::Color(c)` / `usvg::Stroke::None(_)` | `Stroke` is a **struct**. Use `stroke.paint()` → `Paint::Color(c)` |
| `path.transform()` | → `path.abs_transform()` (most useful for EPS/rendering) |
| `path.stroke_width()` | → `stroke.width().get()` (returns `f32`) |
| `path.fill()` returns `&Fill` | → Returns `Option<&Fill>` (unwrap first) |
| `usvg::PathSegment` | → `usvg::tiny_skia_path::PathSegment` (re-exported from tiny-skia-path) |
| `Transform` fields (`sx`, `ky`, etc.) are `f64` | All `f32` in tiny-skia-path 0.11 |
| `svg2pdf::convert()` returns doc object | → `svg2pdf::to_pdf(&tree, ConversionOptions, PageOptions)` returns `Result<Vec<u8>>` |
| `svg2pdf::Options` | → `svg2pdf::ConversionOptions` + `svg2pdf::PageOptions` (two separate structs) |
| `usvg::Size::width()` returns `f64` | Returns `f32` |

**Re-export chain:** `usvg` re-exports from `tiny_skia_path`: `Size`, `Transform`, `Rect`, `NonZeroRect`. Access via `usvg::Size`, `usvg::Transform`, etc.

**Finding the actual source** when API is unclear:
```bash
# Find the registry source dir
find ~/.cargo/registry/src -name 'usvg-0.45*' -type d
# Key files:
# tree/mod.rs — Fill, Stroke, Path, Group, Node, Paint, Color structs
# tree/geom.rs — re-exports from tiny_skia_path
# size.rs (in tiny-skia-path) — Size struct (width/height return f32)
```

**Path segments** use `PathSegment::MoveTo(Point)`, `LineTo(Point)`, `CubicTo(Point, Point, Point)`, `QuadTo(Point, Point)`, `Close` — where `Point` is `tiny_skia_path::Point { x: f32, y: f32 }`.

### ⚠️ Byte-Level SVG Number Shortening Must Be Scoped to Path Data

When building a custom SVG optimizer that shortens numbers (e.g. `1.000` → `1`, `0.50` → `0.5`), **you MUST scope the parser to only operate within `d="..."` attribute values**. A naive byte-level scanner that treats any `.` as a decimal point will corrupt URLs in attributes:

```
Input:  xmlns="http://www.w3.org/2000/svg"
Parser sees: ...3. → "3." with no decimal digits → strips the dot
Output: xmlns="http://www.w3org/2000/svg"   ← BROKEN, usvg can't parse this
```

**Root cause:** The parser finds a digit (`3`), then a dot (`.`), then non-digits (`o`, `r`, `g`). It concludes the dot is a trailing decimal point with zero decimal digits and removes it.

**Why this is insidious:** The corruption happens in a post-processing optimizer step, NOT in the SVG generation code. Debug prints in the generator show correct output. The bug only manifests after `optimize_svg()` transforms the string. This makes it look like a memory corruption or `write!` bug, wasting hours of debugging.

**Fix pattern:**
```rust
// ❌ WRONG — scans all bytes, corrupts URLs
fn shorten_path_numbers(s: &str) -> String { /* scans entire string */ }

// ✅ CORRECT — only processes inside d="..." attributes
fn shorten_path_numbers(s: &str) -> String {
    // Look for d="..." attribute boundaries
    // Only parse numbers between the quotes
    // Pass through all other bytes verbatim
}
```

**Regression test (always include):**
```rust
#[test]
fn test_shorten_numbers_preserves_urls() {
    let input = r#"<svg xmlns="http://www.w3.org/2000/svg" width="100"><path d="M1.0 2.0"/></svg>"#;
    let result = shorten_path_numbers(input);
    assert!(result.contains("w3.org"));
    assert!(result.contains(r#"d="M1 2""#));
}
```

**Real case (covecto):** Took 2 hours to debug. Hex dumps showed the dot present in generator output, present after `push_str`, present after `format!+push_str`, but missing in final result. The "corruption" was the optimizer removing it.

### ⚠️ pngtosvg Zero Config, Limited Output

`pngtosvg::convert_image_to_svg(img)` takes `&DynamicImage` and returns SVG string. No configuration options at all. Output uses only M/h/v/Z path commands (no curves). Good for pixel-exact reproduction, bad for smooth vector art.

## Dual-Engine Product Architecture (covecto)

Reference implementation: `codecoradev/covecto` — dual-engine image vectorizer with CLI + HTTP API.

### Engine Selection Heuristic

```
Input image
    ├── width < 64 && height < 64  → PixelExact (pngtosvg)
    └── otherwise                    → Spline (vtracer)
    └── user override: --engine spline|pixel-exact|auto
```

### Workspace Structure

```
covecto/
├── Cargo.toml              ← workspace: covecto-core, covecto (CLI), covecto-api
├── crates/
│   ├── core/               ← engines, config, optimizer, error types
│   │   └── src/
│   │       ├── config.rs   ← Engine, VectorizeConfig, SplineConfig, OptimizeConfig
│   │       ├── engine/
│   │       │   ├── spline.rs       ← vtracer wrapper
│   │       │   └── pixel_exact.rs  ← pngtosvg wrapper
│   │       ├── optimize.rs ← lightweight SVG optimizer
│   │       └── error.rs    ← thiserror + load_image helpers
│   ├── cli/                ← clap CLI: vectorize + serve
│   └── api/                ← Axum HTTP: /v1/vectorize, /v1/optimize, /v1/health
```

### Key Pattern: Config with Presets

```rust
pub enum SplinePreset { Default, Bw, Poster, Photo }
pub enum Engine { Auto, Spline, PixelExact }
pub enum OptimizePreset { Default, Safe, None }
```

Presets fill in all individual params (color_precision, filter_speckle, etc.) — if preset is set, individual params are ignored. If no preset, individual params use vtracer defaults.

### API Endpoints

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/v1/health` | GET | — | `{ status: "ok", version: "..." }` |
| `/v1/metrics` | GET | — | `{ request_count, avg_processing_ms }` |
| `/v1/vectorize` | POST | multipart (file + params) | `{ svg, engine_used, metadata }` |
| `/v1/optimize` | POST | multipart (SVG file + preset) | `{ svg, original_size, optimized_size, reduction_pct }` |

## References

- [references/covecto-architecture.md](references/covecto-architecture.md) — covecto workspace structure, deps, export module (PDF/EPS), API endpoints
- [references/neplex-vectorizer.md](references/neplex-vectorizer.md) — neplextech/vectorizer breakdown (napi-rs pattern, API surface, preset enum pitfall)
- [references/oxvg-conflict.md](references/oxvg-conflict.md) — oxvg transitive dependency conflict (cssparser version clash)
