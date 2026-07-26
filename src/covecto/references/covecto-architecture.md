# covecto — Dual-Engine Image Vectorizer (Pure Rust)

**Repo:** `codecoradev/covecto` | **License:** MIT | **Edition:** 2024

## Architecture

Dual-engine: vtracer (smooth curves) + pngtosvg (pixel-exact). Auto-selection heuristic based on image size. Output formats: SVG, PDF, EPS.

## Workspace

```
covecto/
├── Cargo.toml                  # edition 2024, 3 members
├── crates/
│   ├── core/                   # covecto-core: engines, config, optimizer, error, export
│   │   └── src/
│   │       ├── config.rs       # Engine, VectorizeConfig, SplinePreset, OptimizePreset
│   │       ├── engine/
│   │       │   ├── spline.rs          # vtracer wrapper
│   │       │   └── pixel_exact.rs     # pngtosvg wrapper
│   │       ├── optimize.rs     # lightweight SVG optimizer (NO oxvg)
│   │       ├── export.rs       # SVG→PDF (svg2pdf) + SVG→EPS (usvg tree walker)
│   │       ├── error.rs        # thiserror + load_image/load_image_from_bytes
│   │       └── lib.rs          # vectorize(), auto-engine heuristic
│   ├── cli/                    # covecto: clap CLI (vectorize + serve)
│   └── api/                    # covecto-api: Axum HTTP server
│       └── src/
│           ├── lib.rs          # Router + run_server()
│           ├── routes.rs       # /v1/vectorize, /v1/optimize, /v1/health, /v1/metrics
│           └── state.rs        # AppState (Arc<AtomicU64> for metrics)
```

## Key Dependencies

- `vtracer = "0.6.5"` — spline engine (visioncortex 0.8.10)
- `pngtosvg = "0.6"` — pixel-exact engine
- `image = "0.25"` — image decoding
- `roxmltree = "0.20"` — XML parsing (optimizer)
- `usvg = "0.45"` — SVG parsing (pinned to match svg2pdf)
- `svg2pdf = "0.13.0"` (features: image, text) — SVG→PDF conversion
- `axum = "0.8"` — HTTP API
- `tower-http = "0.6"` — CORS, body limit, tracing
- `clap = "4"` (derive) — CLI

**NOT used:** oxvg (see oxvg-conflict.md), napi-rs, any Node.js.

## Export Module (export.rs)

Converts SVG output to PDF and EPS formats.

### SVG → PDF
Uses `svg2pdf::to_pdf(&tree, ConversionOptions::default(), PageOptions::default())` which returns `Result<Vec<u8>>` directly. Input SVG is parsed via `usvg::Tree::from_str()`.

### SVG → EPS
Lightweight PostScript generator that walks the usvg tree. Handles Path nodes with fill/stroke. Uses `usvg::tiny_skia_path::PathSegment` for path iteration. Coordinate transform flips Y axis (SVG top-left → PS bottom-left origin).

**Limitations:** Skips text/image nodes. QuadTo segments approximated as lines (PostScript has no native quad curves). Gradients/patterns skipped — only solid `Paint::Color` fills and strokes rendered.

## Optimizer (optimize.rs)

Lightweight SVG optimizer with presets (Default, Safe, None). Runs automatically when `optimize: true` (default).

**Critical bug fixed:** `shorten_path_numbers()` was scoped to entire SVG string, stripping dots from URLs like `w3.org`. Now scoped to only `d="..."` attribute values. See SKILL.md pitfall: "Byte-Level SVG Number Shortening Must Be Scoped to Path Data".

Passes: remove XML prolog → remove comments → remove metadata/title/desc elements → remove empty groups/defs → shorten path numbers → clean empty attributes → trim whitespace. Optional multipass mode.

## Engine Selection

Auto heuristic: `w < 64 && h < 64` → PixelExact, otherwise → Spline. User can override.

## vtracer Integration

`convert()` returns SVG string. `ColorImage` uses flat `Vec<u8>` RGBA (same layout as `image::RgbaImage::as_raw()`). Pass `img.as_raw()` directly — no conversion needed.

## CLI

```bash
covecto vectorize input.png -o output.svg
covecto vectorize icon.png --engine pixel-exact
covecto vectorize photo.jpg --preset photo --optimize
covecto vectorize ./images/ --output ./vectorized/
covecto serve --port 3000
```

## API

```bash
curl -X POST http://localhost:3000/v1/vectorize -F "file=@photo.jpg"
```

## CI

Jobs: check → format → clippy → test → build. Release on `v*` tags (must be on `main`).