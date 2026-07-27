# Humanizer

Remove AI-generated writing patterns from text. Based on Wikipedia's "Signs of AI writing" guide.

## What It Does

Detects and fixes 30+ AI writing patterns:
- Inflated symbolism and promotional language
- Em dash overuse
- Rule of three constructions
- AI vocabulary words ("delve", "tapestry", "realm")
- Vague attributions ("many experts say")
- Passive voice clusters
- Negative parallelisms ("not just X, but Y")
- Filler phrases and signposting

## Quick Start

```python
# Load the skill
skill_view(name="humanizer")

# Review text for AI patterns
# The skill provides a numbered checklist of patterns to scan for
```

## Installation

```bash
# Copy to your Hermes skills directory
cp -r src/humanizer ~/.hermes/skills/creative/
```

## Files

| File | Description |
|------|-------------|
| `SKILL.md` | Main skill with 30+ pattern rules and fix examples |
| `references/indonesian-localization.md` | Bahasa Indonesia specific patterns |
| `templates/wa-followup-generator.py` | WhatsApp follow-up message generator |

## Version

2.8.0

## License

MIT
