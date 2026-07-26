# neplextech/vectorizer — Detailed Breakdown

## What It Actually Is

NOT a pure JavaScript library. Core is **Rust** compiled to native via **napi-rs** (Node.js N-API bindings).

- **Repo:** github.com/neplextech/vectorizer
- **Stars:** 201
- **Core engine:** `visioncortex` crate v0.8.10 (vtracer)
- **JS binding:** napi-rs
- **Last commit:** Jul 2026, active
- **Performance:** ~530µs/iter (4-7x faster than imagetracerjs/potrace)

## Cargo.toml (Rust core)

```toml
[package]
name = "vectrace"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
fastrand     = "2.4.1"
image        = "0.25.10"
napi         = { version = "3.0.0", features = ["serde-json"] }
napi-derive  = "3.0.0"
oxvg_ast = { version = "0.0.5", features = ["parse", "roxmltree"] }
oxvg_optimiser = "0.0.5"
serde_json = "1.0"
visioncortex = "0.8.10"

[build-dependencies]
napi-build = "2"
```

## API Surface

| Function | Description |
|----------|-------------|
| `vectorize(data, config, signal)` | Async: image buffer → SVG string |
| `vectorizeSync(data, config)` | Sync: image buffer → SVG string |
| `vectorizeRaw(data, args, config, signal)` | Async: raw RGBA pixel data → SVG |
| `vectorizeRawSync(data, args, config)` | Sync: raw RGBA pixel data → SVG |
| `vectorizeToCallback(data, config, callback)` | Streaming: emits SVG chunks + progress 0-100 |
| `readImage(data, args, signal)` | Decode image buffer to ImageData (width/height/pixels) |
| `colorExistsInImage(image, color, signal)` | Check if RGB color exists in decoded image |
| `findUnusedColorInImage(image, options, signal)` | Find a color not present in the image |
| `optimize(svg, options, signal)` | SVG optimization (wraps oxvg, SVGO-compatible plugins) |
| `optimizeSync(svg, options)` | Synchronous SVG optimization |
| `isEOF(chunk, progress)` | Check if callback chunk is the final SVG chunk |

## Optimization Pipeline

Uses `oxvg_optimiser` (Rust SVGO replacement). Supports:
- Presets: `Default`, `Safe`, `None`
- SVGO-compatible plugin config
- Multipass optimization (run until stable or iteration limit)
- Plugin omit list

## API Pitfall: Config is Preset Enum, Not Object

**`vectorizeSync(buffer, config)` — the `config` param is a `Preset` enum integer, NOT a JS config object.**

```js
const { vectorizeSync, optimizeSync, Preset, OptimizePreset } = require('@neplex/vectorizer');

// ✅ CORRECT — use Preset enum
const svg = vectorizeSync(buffer, Preset.Poster);       // 0=Bw, 1=Poster, 2=Photo
const optimized = optimizeSync(svg, OptimizePreset.Default); // 0=Default, 1=Safe, 2=None

// ❌ WRONG — no JsConfig object, will crash or return garbage
const svg = vectorizeSync(buffer, { colorMode: 'Color' });
```

**Enums (discovered via `Object.getOwnPropertyNames(Preset)`):**
- `Preset`: `Bw=0`, `Poster=1`, `Photo=2`
- `OptimizePreset`: `Default=0`, `Safe=1`, `None=2`

No `ColorMode` or `PathSimplifyMode` JS enums are exposed — those are Rust-internal. The Preset enum selects a pre-tuned combination internally.

## Node Module Resolution from Non-Project Scripts

If your CJS script lives outside `web/` but `node_modules/` is inside `web/`, `require('@neplex/vectorizer')` fails with MODULE_NOT_FOUND. Use absolute path:

```js
const { vectorizeSync, optimizeSync, Preset, OptimizePreset } =
  require('/absolute/path/to/web/node_modules/@neplex/vectorizer');
```

## Key Insights

1. The "JavaScript library" is really a thin napi-rs wrapper over vtracer + oxvg
2. Raw SVG output is large — optimization step is recommended
3. Async APIs may not work in browsers due to WASI limitations; sync APIs work in Web Workers
4. Benchmark shows sync is fastest, callback is slowest (within vectorizer)
5. vtracer crate on crates.io is at v0.6.5 but neplextech uses visioncortex v0.8.10 (likely a newer/different publish)
6. **@neplex/vectorizer and visioncortex/vtracer produce identical SVG output** — same `visioncortex` crate v0.8.10. Only difference: neplex adds built-in SVG optimization (oxvg) + TypeScript API. Choose neplex when you need JS API + optimizer in one package; choose vtracer binary when you want zero npm.

## Competitors Found on GitHub (Rust)

| Repo | Stars | Notes |
|------|-------|-------|
| mayuso/PNGToSVG | 105 | Rust-native, `pngtosvg` crate, icon-focused, active (Jul 2026) |
| mikaeladev/pixel-to-svg | 0 | WIP, pixel-art specific |
| salvagit/jpg2svg | 0 | Batch CLI wrapper around vtracer |
| Pablushka/rsvg | 0 | Small Rust tool for PNG/JPG/BMP → SVG |