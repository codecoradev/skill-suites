# Uteke Database Health Check Script

Reusable Python script to audit Uteke DB integrity. Works while uteke-serve is running (read-only queries).

## Quick Run

```python
import sqlite3
DB = "~/.uteke/uteke.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# === ORPHANED REFERENCES ===
for table, fk_col in [("memory_edges", "source_id"), ("memory_edges", "target_id"),
                       ("memory_tags", "memory_id"), ("timeline_events", "memory_id"),
                       ("room_memories", "memory_id"), ("room_memories", "room_id")]:
    cur.execute(f"SELECT COUNT(*) FROM {table} t LEFT JOIN memories m ON t.{fk_col} = m.id WHERE m.id IS NULL")
    print(f"Orphaned {table}.{fk_col}: {cur.fetchone()[0]}")

# === DEPRECATED RATIO ===
cur.execute("SELECT COUNT(*) FROM memories WHERE deprecated=1")
dep = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM memories")
total = cur.fetchone()[0]
print(f"\nDeprecated: {dep}/{total} ({dep/total*100:.1f}%)")

# === FTS SYNC CHECK ===
cur.execute("SELECT COUNT(*) FROM memories_fts")
fts_total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM memories m JOIN memories_fts f ON m.rowid = f.rowid WHERE m.deprecated=1")
dep_in_fts = cur.fetchone()[0]
print(f"FTS total: {fts_total}, Deprecated in FTS: {dep_in_fts}")
print(f"{'⚠️ BUG: deprecated in FTS!' if dep_in_fts > 0 else '✅ FTS clean'}")

# === MEMORY TYPE DISTRIBUTION ===
print("\nMemory types:")
cur.execute("SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type ORDER BY COUNT(*) DESC")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

# === NAMESPACE DISTRIBUTION ===
print("\nNamespaces:")
cur.execute("SELECT namespace, COUNT(*) FROM memories GROUP BY namespace ORDER BY COUNT(*) DESC")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

# === IMPORTANCE DISTRIBUTION ===
print("\nImportance buckets:")
cur.execute("""SELECT CASE 
    WHEN importance < 0.1 THEN 'junk'
    WHEN importance < 0.3 THEN 'low'
    WHEN importance < 0.5 THEN 'medium'
    WHEN importance < 0.7 THEN 'high'
    ELSE 'critical'
  END, COUNT(*) FROM memories GROUP BY 1 ORDER BY MIN(importance)""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

# === EMBEDDING COVERAGE ===
cur.execute("SELECT COUNT(*) FROM memories WHERE embedding IS NULL")
no_emb = cur.fetchone()[0]
print(f"\nNo embedding: {no_emb}/{total} ({no_emb/total*100:.1f}%)")

# === CONTENT INTEGRITY ===
cur.execute("SELECT COUNT(*) FROM memories WHERE content IS NULL OR content = ''")
print(f"Empty content: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM memories WHERE length(content) < 10")
print(f"Tiny content (<10 chars): {cur.fetchone()[0]}")

# === DUPLICATE CONTENT ===
cur.execute("SELECT content, COUNT(*) as cnt FROM memories WHERE length(content) > 10 GROUP BY content HAVING cnt > 1 LIMIT 5")
dupes = cur.fetchall()
print(f"\nDuplicate content groups: {len(dupes)}")
for row in dupes:
    print(f"  [{row[1]}x] {row[0][:60]}...")

# === SCHEMA VERSION ===
cur.execute("SELECT version, applied_at FROM schema_version ORDER BY version DESC LIMIT 1")
row = cur.fetchone()
print(f"\nSchema version: v{row[0]} ({row[1]})")

# === UNUSED TABLES ===
for table in ["graph_nodes", "graph_edges"]:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    print(f"{table}: {count} rows {'(unused, candidate for removal)' if count == 0 else ''}")

conn.close()
```

## Orphan Cleanup Queries

After health check, if orphans found:

```sql
-- Clean orphaned memory_edges
DELETE FROM memory_edges WHERE source_id NOT IN (SELECT id FROM memories);
DELETE FROM memory_edges WHERE target_id NOT IN (SELECT id FROM memories);

-- Clean orphaned memory_tags
DELETE FROM memory_tags WHERE memory_id NOT IN (SELECT id FROM memories);

-- Clean orphaned timeline_events
DELETE FROM timeline_events WHERE memory_id NOT IN (SELECT id FROM memories);

-- Clean orphaned room_memories
DELETE FROM room_memories WHERE memory_id NOT IN (SELECT id FROM memories);
DELETE FROM room_memories WHERE room_id NOT IN (SELECT id FROM rooms);
```

## Known Baseline (Jul 20, 2026)

| Metric | Value | Notes |
|--------|-------|-------|
| Total memories | 5,977 | 19 namespaces |
| Deprecated | 3,689 (61.7%) | Intentional aging, Jun 28 spike (3,437) |
| Orphaned memory_edges | 269 | FK not enforced |
| Orphaned memory_tags | 106 | FK not enforced |
| Orphaned timeline_events | 3,011 | FK not enforced |
| Orphaned room_memories | 12 | Room deleted |
| Embedding coverage | 99.9% | 5970/5977 |
| graph_nodes/edges | 0 | Unused, redundant |
| Deprecated in FTS | 3,689 | **BUG** — should be 0 (pitfall #66) |
