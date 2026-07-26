"""uteke-recall shell hook — recalls relevant memories on pre_llm_call.

Reads JSON context from stdin (Hermes shell hook wire protocol),
runs uteke recall, and outputs {"context": "..."} to stdout.

Hermes injects this context into the user message before each LLM call.

Project-aware: detects project name from user_message (file paths, project names)
and filters recall by `--tags project:<name>` for noise-free results.

Race-safe: no shared file writes, per-call invocation.
"""

import json
import os
import pathlib
import re
import sys
import urllib.request
import urllib.error

_PROFILES_DIR = pathlib.Path("~/.hermes/profiles")
_REPOS_DIR = pathlib.Path("~/repos")

# Uteke HTTP API — source of truth
UTEKE_BASE_URL = os.environ.get("UTEKE_BASE_URL", "http://localhost:8767")
UTEKE_TOKEN = os.environ.get("UTEKE_TOKEN", "")


def _resolve_agent_from_cwd(cwd: str) -> str:
    """Extract agent name from cwd path (~/.hermes/profiles/{agent}).

    Hermes wire protocol always includes the gateway's working directory
    in the ``cwd`` field.  This is the most reliable source.
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

    Fragile: used only as fallback when cwd is unavailable.
    """
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

    # Grandparent: slash_worker → gateway
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
    name = _resolve_agent_from_cwd(cwd)
    if name:
        return name
    name = os.environ.get("HERMES_PROFILE", "")
    if name:
        return name
    name = _resolve_agent_from_proc()
    if name:
        return name
    return "default"



_SKILLS_ROOM = "hermes-skills"  # Uteke room containing compact skill index
_SKILL_RECALL_LIMIT = 5         # Max skill suggestions to inject


def _uteke_search(query: str, namespace: str, limit: int = 5, tag: str = "") -> list:
    """Search uteke via HTTP API (source of truth). Returns list of {content, score}."""
    if not UTEKE_TOKEN:
        return []
    payload = {"query": query, "namespace": namespace, "limit": limit}
    if tag:
        payload["tag"] = tag
    req = urllib.request.Request(
        f"{UTEKE_BASE_URL}/search",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {UTEKE_TOKEN}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if not isinstance(data, list):
                return []
            results = []
            for item in data:
                mem = item.get("memory", item) if isinstance(item, dict) else item
                if isinstance(mem, dict):
                    results.append({
                        "content": mem.get("content", ""),
                        "score": item.get("score", 0) if isinstance(item, dict) else 0,
                    })
            return results
    except (urllib.error.URLError, urllib.error.HTTPError, Exception):
        return []


def _recall_skills_from_room(query: str, limit: int = 5) -> list:
    """Recall relevant skills from hermes-skills room via HTTP API."""
    return _uteke_search(query, "default", limit=limit, tag="hermes-skills")


def _detect_project_from_message(message: str) -> str:
    """Detect project name from user message.

    Strategies (priority order):
    1. File paths containing ~/repos/<project>/
    2. Known project name mentions (when _REPOS_DIR exists, scan directory names)
    Returns lowercase project name or empty string.
    """
    if not message:
        return ""

    # Strategy 1: file paths
    matches = re.findall(r"~/repos/([a-zA-Z0-9_.-]+)/", message)
    seen = set()
    for proj in matches:
        proj_lower = proj.lower()
        if proj_lower not in ("", ".git", "__pycache__", "node_modules"):
            return proj_lower  # First match wins

    # Strategy 2: known project names (if repos dir exists)
    if _REPOS_DIR.exists():
        for proj_dir in _REPOS_DIR.iterdir():
            if proj_dir.is_dir() and not proj_dir.name.startswith("."):
                # Check if the project name is mentioned as a word in the message
                if re.search(rf'\b{re.escape(proj_dir.name)}\b', message, re.IGNORECASE):
                    return proj_dir.name.lower()

    return ""


def _recall_uteke(query: str, limit: int = 5, agent: str = "cto", project: str = "") -> list:
    """Recall memories from uteke via HTTP API (source of truth)."""
    # Build query with project tag filter if detected
    tag = f"project:{project}" if project else ""
    return _uteke_search(query, agent, limit=limit, tag=tag)


def main():
    # Read hook context from stdin (Hermes shell hook wire protocol)
    try:
        raw = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    if not isinstance(raw, dict):
        sys.exit(0)

    # Resolve agent name from cwd (payload) — most reliable source
    cwd = raw.get("cwd", "")
    agent = _resolve_agent_name(cwd)

    # Hermes wire protocol: user_message lives in "extra" dict
    # Top-level keys: hook_event_name, session_id, extra
    extra = raw.get("extra", {})
    if not isinstance(extra, dict):
        extra = {}

    # user_message can be in extra or top-level
    message = extra.get("user_message") or raw.get("user_message", "")
    if not isinstance(message, str) or not message.strip():
        sys.exit(0)
    message = message.strip()[:500]

    if len(message) < 5:
        sys.exit(0)

    # Skip cron sessions
    session_id = raw.get("session_id", "")
    if isinstance(session_id, str) and session_id.startswith("cron_"):
        sys.exit(0)

    # Recall relevant memories from agent namespace
    project = _detect_project_from_message(message)
    memories = _recall_uteke(message, limit=5, agent=agent, project=project)

    # Recall relevant skills from hermes-skills room (cross-namespace)
    skill_suggestions = _recall_skills_from_room(message, limit=_SKILL_RECALL_LIMIT)

    if not memories and not skill_suggestions:
        sys.exit(0)

    # Build context text
    lines = []

    # Skill suggestions first (for routing)
    if skill_suggestions:
        lines.append("Suggested skills (from hermes-skills room):")
        for i, mem in enumerate(skill_suggestions, 1):
            content = mem.get("content", "")
            score = mem.get("score", 0)
            if len(content) > 250:
                content = content[:247] + "..."
            lines.append(f"  {i}. [{score:.2f}] {content}")
        lines.append("")  # blank separator

    # Agent namespace memories
    if memories:
        lines.append("Recalled memories (uteke):")
        for i, mem in enumerate(memories, 1):
            content = mem.get("content", "")
            score = mem.get("score", 0)
            if len(content) > 200:
                content = content[:197] + "..."
            lines.append(f"  {i}. [{score:.2f}] {content}")

    ctx_text = "\n".join(lines)

    # Output Hermes wire protocol: {"context": "..."}
    json.dump({"context": ctx_text}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
