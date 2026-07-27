# Hybrid Memory

Hybrid memory system combining SQLite (structured data, entity graph) with Uteke (semantic search, recall). Features a 4-tier lifecycle that promotes memories from ephemeral to permanent based on access frequency.

## What It Does

- **SQLite layer:** entities, relationships, staging table, decay tracking. Sub-ms queries.
- **Uteke layer:** semantic recall, keyword search, contradiction detection. ~50ms warm recall.
- **4-tier lifecycle:** Working (24h TTL) → Session (staging) → Knowledge (permanent) → Forgotten (soft-deleted)
- **Frequency-based promotion:** memories accessed 5+ times in 7 days auto-promote to permanent
- **Confidence decay:** unused memories lose confidence (0.05/week) and eventually get archived

## Installation

### Prerequisites

- Hermes Agent with shell hooks support
- Uteke server running (`uteke serve --port 8767`)
- SQLite3

### Step 1: Install the skill

```bash
# Clone and copy
git clone https://github.com/codecoradev/skill-suites.git
cp -r skill-suites/src/hybrid-memory ~/.hermes/skills/
```

### Step 2: Install the extensions (auto-recall + auto-extract hooks)

The skill describes the memory system. For automatic memory recall and extraction, install the shell hooks from the `extensions/` directory:

```bash
cp -r skill-suites/extensions/uteke-recall ~/.hermes/extensions/
cp -r skill-suites/extensions/uteke-extract ~/.hermes/extensions/
```

See [extensions/README.md](../../extensions/README.md) for full hook setup instructions.

### Step 3: Configure

```bash
export UTEKE_BASE_URL=http://localhost:8767
export UTEKE_TOKEN=your-token-here
```

## Usage

```
# Search memories
knowledge(action="search_knowledge", query="API deployment")

# Store a memory
knowledge(action="remember", content="Insight...", tags=["project"])

# Check system health
knowledge(action="stats")
```

## Version

6.0.0

## License

MIT
