# Uteke Room Memory Migration

## When to Use

- User says "pindahkan ke room lain" or "jangan simpan ke room itu, pindah ke room X"
- Need to move a memory from one room to another (not copy — move)
- Room was created with wrong ID or content needs reorganization

## Complete Migration Recipe (Proven Jul 2026)

### Prerequisites

- `room_memories` schema: `(room_id TEXT, memory_id TEXT, author TEXT NOT NULL, role TEXT DEFAULT 'participant', joined_at TEXT NOT NULL)`
- `joined_at` is NOT NULL — must always include in INSERT
- `INSERT OR IGNORE` silently drops if any NOT NULL column is missing (no error)

### Step 1: Create Target Room (if it doesn't exist)

```bash
source ~/.env

# HTTP API — field is room_id, NOT id
curl -sf -X POST http://127.0.0.1:8767/room/create \
  -H "Authorization: Bearer $UTEKE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"room_id": "target-room-id", "title": "Room Title", "namespace": "cmo"}'
```

### Step 2: Add Memory to New Room (create junction row)

```python
import sqlite3, datetime

conn = sqlite3.connect('~/.uteke/uteke.db')
now = datetime.datetime.now(datetime.timezone.utc).isoformat()

conn.execute(
    "INSERT OR IGNORE INTO room_memories (room_id, memory_id, author, role, joined_at) VALUES (?,?,?,?,?)",
    ("target-room-id", "<memory-id>", "CMO", "author", now)
)
conn.commit()
```

### Step 3: Delete from Old Room

```python
conn.execute(
    "DELETE FROM room_memories WHERE room_id = ? AND memory_id = ?",
    ("old-room-id", "<memory-id>")
)
conn.commit()
```

### Step 4: Verify

```python
entries = conn.execute('''
    SELECT rm.memory_id, substr(m.content, 1, 80), m.tags
    FROM room_memories rm
    JOIN memories m ON rm.memory_id = m.id
    WHERE rm.room_id = ?
    ORDER BY rm.joined_at
''', ("target-room-id",)).fetchall()

for i, (mid, preview, tags) in enumerate(entries):
    print(f"{i+1}. [{mid[:12]}] {preview}...")
```

### Important Notes

- **Do NOT delete the memory itself** (`DELETE FROM memories WHERE id = ?`) — only delete the `room_memories` junction row
- The memory content stays in the `memories` table — only its room association moves
- Multiple rooms can share the same memory (many-to-many via `room_memories`)
- If the user wants a **copy** (memory in both rooms), skip Step 3

## Why Not Use HTTP API?

`POST /remember` with `room_id` silently fails to create the junction (see pitfall #18a in SKILL.md). `POST /room/create` works fine for room creation, but room association must be done via direct SQLite insert.

## Common Migration Scenarios

| Scenario | Action |
|----------|--------|
| Wrong room | Create correct room → add junction → delete old junction |
| Split room | Create N new rooms → add junctions for each → delete old junctions |
| Merge rooms | Add all memories from room B into room A → delete room B junctions |
| Rename room | `UPDATE rooms SET id = 'new-id' WHERE id = 'old-id'` (cascades to room_memories via FK) |
