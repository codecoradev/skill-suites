# covecto

Covecto: Raster-to-SVG vectorization ecosystem in Rust. Convert images to clean, editable vector graphics.

## Contents

- Pipeline overview, Neplex vectorizer, OxVG backend
- CLI commands, config options, quality tuning
- Pitfalls (OxVG conflicts, vtracer vs potrace tradeoffs, SVG cleanup)
- Architecture diagrams and Neplex algorithm details

## Quick Start

```bash
# Convert PNG to SVG (default: vtracer)
covecto convert input.png -o output.svg

# Use potrace backend
covecto convert input.png --backend potrace -o output.svg

# Batch convert
covecto batch ./images/ --output-dir ./vectors/
```

## Version

| Skill Version | Covecto Binary |
|---------------|----------------|
| 1.0.0 | v1.0.0+ |

## Installation

Place this `SKILL.md` in `~/.hermes/skills/covecto/`.

## Related

- [Covecto repo](https://github.com/codecoradev/covecto), Source code

## License

MIT
