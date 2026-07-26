"""uteke-extract shell hook — auto-extracts key takeaways on session finalize.

Reads JSON context from stdin (Hermes shell hook wire protocol),
reads session messages from state.db, extracts key takeaways,
and stores them via uteke remember.

Project-aware: auto-detects project name from file paths in session messages
and tags memories with `project:<name>` for noise-free recall.

Race-safe: only reads state.db (no writes), per-session invocation.
"""

import json
import os
import pathlib
import re
import sqlite3
import sys
import urllib.request
import urllib.error

_PROFILES_DIR = pathlib.Path("~/.hermes/profiles")
# Known project directories — used to detect project name from file paths
_REPOS_DIR = pathlib.Path("~/repos")

# Uteke HTTP API — source of truth
UTEKE_BASE_URL = os.environ.get("UTEKE_BASE_URL", "http://localhost:8767")
UTEKE_TOKEN = os.environ.get("UTEKE_TOKEN", "")


def _resolve_agent_from_cwd(cwd: str) -> str:
    """Extract agent name from cwd path (~/.hermes/profiles/{agent}).

    Hermes wire protocol always includes the gateway's working directory
    in the ``cwd`` field.  This is the most reliable source — works
    regardless of process parentage (main thread, asyncio, expiry watcher).
    """
    if not cwd:
        return ""
    try:
        p = pathlib.Path(cwd).resolve()
        if p.parent == _PROFILES_DIR and p.name:
            return p.name
    except Exception:
        pass
    return ""


def _resolve_agent_from_proc() -> str:
    """Extract agent name from parent process cmdline (hermes -p {agent}).

    Fragile: shell hooks run as child subprocesses.  The /proc PPid chain
    may not reach the gateway process when invoked from an asyncio background
    task (e.g. session expiry watcher).  Used only as fallback.
    """
    # 1. Parent PID from /proc/self/status
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("PPid:"):
                    ppid = line.split(":")[1].strip()
                    with open(f"/proc/{ppid}/cmdline", "rb") as pf:
                        parts = pf.read().split(b"\x00")
                    for i, part in enumerate(parts):
                        if part == b"-p" and i + 1 < len(parts):
                            return parts[i + 1].decode("utf-8", errors="ignore").strip()
                    break
    except Exception:
        pass

    # 2. Grandparent: slash_worker → gateway
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("PPid:"):
                    gpid = line.split(":")[1].strip()
                    with open(f"/proc/{gpid}/status") as gf:
                        for gline in gf:
                            if gline.startswith("PPid:"):
                                gpid = gline.split(":")[1].strip()
                                with open(f"/proc/{gpid}/cmdline", "rb") as gpf:
                                    parts = gpf.read().split(b"\x00")
                                for i, part in enumerate(parts):
                                    if part == b"-p" and i + 1 < len(parts):
                                        return parts[i + 1].decode("utf-8", errors="ignore").strip()
                                break
                    break
    except Exception:
        pass

    return ""


def _resolve_agent_name(cwd: str = "") -> str:
    """Resolve agent name with reliable priority order.

    Priority: cwd (payload) → HERMES_PROFILE env → /proc chain → cto default.
    """
    # 1. cwd from Hermes wire payload — always reliable
    name = _resolve_agent_from_cwd(cwd)
    if name:
        return name

    # 2. HERMES_PROFILE env var
    name = os.environ.get("HERMES_PROFILE", "")
    if name:
        return name

    # 3. /proc chain (fragile, but better than hardcoding)
    name = _resolve_agent_from_proc()
    if name:
        return name

    return "default"


def _remember_uteke(content: str, tags: list, agent: str) -> bool:
    """Store a memory via uteke HTTP API (source of truth)."""
    if not UTEKE_TOKEN:
        return False
    payload = json.dumps({
        "content": content,
        "namespace": agent,
        "tags": tags,
    }).encode()
    req = urllib.request.Request(
        f"{UTEKE_BASE_URL}/remember",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {UTEKE_TOKEN}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 201)
    except (urllib.error.URLError, urllib.error.HTTPError, Exception):
        return False


# Configurable limits
MAX_CONTENT_CHARS = 800       # max chars stored per memory
MAX_MESSAGES = 10             # max assistant messages to read
MIN_CONTENT_LEN = 50          # skip sessions with <50 chars total


def _get_assistant_messages(session_id: str, state_db: pathlib.Path) -> list:
    """Read non-empty assistant messages from session DB for the given session."""
    if not state_db.exists():
        return []
    try:
        conn = sqlite3.connect(str(state_db), timeout=5)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT content FROM messages "
            "WHERE session_id = ? AND role = 'assistant' AND active = 1 "
            "  AND content IS NOT NULL AND length(content) > 30 "
            "ORDER BY id DESC LIMIT ?",
            (session_id, MAX_MESSAGES),
        )
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in reversed(rows)]
    except Exception:
        return []


def _detect_project_from_messages(messages: list) -> str:
    """Detect project name from file paths in session messages."""
    if not messages or not _REPOS_DIR.exists():
        return ""
    project_counts = {}
    for msg in messages:
        matches = re.findall(r"~~/repos/([a-zA-Z0-9_.-]+)/", msg)
        for proj in matches:
            proj_lower = proj.lower()
            if proj_lower in ("", ".git", "__pycache__", "node_modules"):
                continue
            project_counts[proj_lower] = project_counts.get(proj_lower, 0) + 1
    if not project_counts:
        return ""
    return max(project_counts, key=project_counts.get)


def _extract_takeaway(messages: list) -> str:
    """Extract structured takeaway from the last substantive assistant message."""
    if not messages:
        return ""
    for msg in reversed(messages):
        content = msg.strip()
        if len(content) > MIN_CONTENT_LEN:
            structured = _extract_structured(content, MAX_CONTENT_CHARS)
            if structured:
                return structured
            return content[:MAX_CONTENT_CHARS].rsplit("\n", 1)[0].strip()
    return ""


def _extract_structured(content: str, max_chars: int) -> str:
    """Extract structured lines (headers, bullets, key-values) from content."""
    lines = content.split("\n")
    structured = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("```"):
            continue
        if stripped.startswith("#"):
            structured.append(stripped)
        elif len(stripped) > 1 and stripped[0] in "-•*│┌└◆►▼█▓░":
            structured.append(stripped)
        elif len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".)":
            structured.append(stripped)
        elif ":" in stripped and len(stripped) < 200:
            structured.append(stripped)
        elif stripped.startswith("|") and stripped.endswith("|"):
            structured.append(stripped)
    if not structured:
        return ""
    result = "\n".join(structured)
    if len(result) > max_chars:
        result = result[:max_chars].rsplit("\n", 1)[0]
    return result.strip()


def main():
    # Read hook payload from stdin
    try:
        raw = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    if not isinstance(raw, dict):
        sys.exit(0)

    # Resolve agent name from cwd (payload) — most reliable source
    cwd = raw.get("cwd", "")
    agent = _resolve_agent_name(cwd)
    state_db = pathlib.Path(f"~/.hermes/profiles/{agent}/state.db")

    # Hermes wire protocol: session_id at top level
    session_id = raw.get("session_id", "")
    extra = raw.get("extra", {})
    if not session_id:
        session_id = extra.get("session_id", "")
    if not isinstance(session_id, str) or not session_id.strip():
        sys.exit(0)
    session_id = session_id.strip()

    # Skip cron sessions
    if session_id.startswith("cron_"):
        sys.exit(0)

    # Get session messages
    messages = _get_assistant_messages(session_id, state_db)
    if not messages:
        sys.exit(0)

    # Extract key takeaway
    takeaway = _extract_takeaway(messages)
    if not takeaway:
        sys.exit(0)

    # Store via uteke
    reason = extra.get("reason", raw.get("reason", "unknown"))
    tags = [
        "auto-extract",
        f"agent:{agent}",
        f"reason:{reason}",
    ]

    # Auto-detect project from session messages
    project = _detect_project_from_messages(messages)
    if project:
        tags.append(f"project:{project}")

    _remember_uteke(takeaway, tags, agent)


if __name__ == "__main__":
    main()
