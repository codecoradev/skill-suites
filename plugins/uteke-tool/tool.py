#!/usr/bin/env python3
"""uteke-tool: Semantic memory plugin for Hermes.

Actions:
  Memory: remember, recall, search, list, forget, stats
  Room:   room_create, room_remember, room_recall, room_list, room_summary, room_stats, room_delete
"""
import json
import os
import urllib.request
import urllib.error

UTEKE_URL = os.environ.get("UTEKE_SERVER_URL", os.environ.get("UTEKE_BASE_URL", "https://localhost:8767"))
UTEKE_TOKEN = os.environ.get("UTEKE_TOKEN", "")


def _request(method, path, data=None):
    """Make an HTTP request to the uteke server."""
    url = f"{UTEKE_URL}{path}"
    # Use "is not None" check — {} is falsy in Python but is a valid JSON body.
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if UTEKE_TOKEN:
        req.add_header("Authorization", f"Bearer {UTEKE_TOKEN}")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode(), "status": e.code}
    except urllib.error.URLError:
        return {"error": f"uteke server unreachable at {UTEKE_URL}"}


def uteke(action="recall", **kwargs):
    """Call uteke for memory and room operations.

    Memory actions:
        uteke(action="remember", content="...", tags="t1,t2", namespace="hermes")
        uteke(action="recall", content="query", namespace="hermes", limit=5)
        uteke(action="search", content="query", namespace="hermes")
        uteke(action="list", namespace="hermes", limit=20)
        uteke(action="forget", id="memory-id")
        uteke(action="stats", namespace="hermes")

    Room actions (#395):
        uteke(action="room_create", room_id="planning", title="Sprint Planning")
        uteke(action="room_recall", room_id="planning", query="deadline")
        uteke(action="room_recall", room_id="planning")  # no query = list all
        uteke(action="room_list")
        uteke(action="room_summary", room_id="planning")
        uteke(action="room_stats", room_id="planning")
        uteke(action="room_delete", room_id="planning")
    """
    content = kwargs.get("content", "")
    namespace = kwargs.get("namespace", "hermes")
    tags = kwargs.get("tags", "")
    limit = kwargs.get("limit", 5)

    # -- Memory actions ----
    if action == "remember":
        result = _request("POST", "/remember", {
            "content": content,
            "tags": tags.split(",") if tags else [],
            "namespace": namespace,
        })
        if "error" not in result:
            return f"\u2713 Stored: {content[:80]}"
        return result

    elif action == "recall":
        result = _request("POST", "/recall", {
            "query": content,
            "limit": limit,
            "namespace": namespace,
        })
        if isinstance(result, list) and result:
            lines = []
            for m in result:
                score = m.get("score", 0)
                text = m.get("memory", {}).get("content", "?")
                lines.append(f"[{score:.2f}] {text}")
            return "\n".join(lines)
        return "No memories found."

    elif action == "search":
        result = _request("POST", "/search", {
            "query": content,
            "limit": limit,
            "namespace": namespace,
        })
        if isinstance(result, list) and result:
            lines = []
            for m in result:
                score = m.get("score", 0)
                text = m.get("content", "?")
                lines.append(f"[{score:.2f}] {text}")
            return "\n".join(lines)
        return "No memories found."

    elif action == "list":
        result = _request("POST", "/list", {
            "limit": limit,
            "namespace": namespace,
        })
        if isinstance(result, list) and result:
            lines = []
            for m in result:
                mid = m.get("id", "?")[:8]
                text = m.get("content", "?")[:60]
                lines.append(f"[{mid}] {text}")
            return "\n".join(lines)
        return "No memories found."

    elif action == "forget":
        mid = kwargs.get("id", "")
        result = _request("DELETE", f"/forget?id={mid}")
        return f"\u2713 Deleted memory: {mid}" if "error" not in result else result

    elif action == "stats":
        # FIX: POST /stats with body (GET /stats?namespace= 404s — same as namespace_stats)
        result = _request("POST", "/stats", {"namespace": namespace} if namespace else {})
        return json.dumps(result, indent=2)

    # -- Room actions (#395) ----
    elif action == "room_create":
        room_id = kwargs.get("room_id", "") or kwargs.get("room", "")
        title = kwargs.get("title")
        result = _request("POST", "/room/create", {
            "room_id": room_id,
            "title": title,
            "namespace": namespace,
        })
        if "error" not in result:
            return f"\u2713 Room '{room_id}' created"
        return result

    elif action == "room_remember":
        # FIX: Use /room/remember (not /remember) with room_id (not room).
        # The /remember endpoint silently ignores room/author fields because
        # RememberRequest has no such fields — memories become orphaned.
        room_id = kwargs.get("room_id", "") or kwargs.get("room", "")
        author = kwargs.get("author", "agent")
        mem_type = kwargs.get("type", "")
        payload = {
            "room_id": room_id,
            "content": content,
            "tags": tags.split(",") if tags else [],
            "namespace": namespace,
            "author": author,
        }
        if mem_type:
            payload["type"] = mem_type
        result = _request("POST", "/room/remember", payload)
        if "error" not in result:
            return f"\u2713 Stored in room '{room_id}': {content[:80]}"
        return result

    elif action == "room_document":
        # FIX: Use /room/remember (not /remember) with room_id (not room).
        # FIX: Default type='reference' (not 'document' — 'document' is not a
        # valid memory type. Valid: fact, procedure, preference, decision,
        # context, note, insight, reference, event).
        room_id = kwargs.get("room_id", "") or kwargs.get("room", "")
        author = kwargs.get("author", "agent")
        mem_type = kwargs.get("type", "reference")
        result = _request("POST", "/room/remember", {
            "room_id": room_id,
            "content": content,
            "tags": tags.split(",") if tags else [],
            "namespace": namespace,
            "author": author,
            "type": mem_type,
        })
        if "error" not in result:
            return f"\u2713 Document stored in room '{room_id}': {content[:80]}"
        return result

    elif action == "room_recall":
        room_id = kwargs.get("room_id", "") or kwargs.get("room", "")
        query = kwargs.get("query", "") or kwargs.get("content", "")
        if not query:
            # No query — fall back to chronological listing
            result = _request("GET", f"/room/memories?room_id={room_id}&limit={limit}")
            if isinstance(result, list) and result:
                lines = []
                for m in result:
                    text = m.get("content", "?")
                    tags = m.get("tags", [])
                    lines.append(f"[{text[:80]}...] | tags: {tags}")
                return "\n".join(lines)
            return "No memories found in room."
        result = _request("POST", "/room/recall", {
            "room_id": room_id,
            "query": query,
            "limit": limit,
        })
        if isinstance(result, list) and result:
            lines = []
            for m in result:
                score = m.get("score", 0)
                text = m.get("memory", {}).get("content", "?")
                lines.append(f"[{score:.2f}] {text}")
            return "\n".join(lines)
        return "No memories found in room."

    elif action == "room_list":
        ns = kwargs.get("namespace", "")
        path = "/room/list" + (f"?namespace={ns}" if ns else "")
        result = _request("GET", path)
        if isinstance(result, list) and result:
            lines = []
            for r in result:
                rid = r.get("id", "?")
                title = r.get("title", "(untitled)")
                ns = r.get("namespace", "?")
                lines.append(f"  {rid}  {title}  [{ns}]")
            return "\n".join(lines)
        return "No rooms found."

    elif action == "room_summary":
        room_id = kwargs.get("room_id", "") or kwargs.get("room", "")
        result = _request("POST", "/room/summary", {"room_id": room_id})
        return json.dumps(result, indent=2) if result else "Room not found."

    elif action == "room_stats":
        room_id = kwargs.get("room_id", "") or kwargs.get("room", "")
        result = _request("POST", "/room/stats", {"room_id": room_id})
        return json.dumps(result, indent=2) if result else "Room not found."

    elif action == "room_delete":
        room_id = kwargs.get("room_id", "") or kwargs.get("room", "")
        result = _request("DELETE", f"/room/delete?room_id={room_id}")
        if "error" not in result:
            return f"\u2713 Room '{room_id}' deleted (memories preserved)"
        return result

    # -- Namespace actions ----
    # FIX: Server route is GET /namespaces (not /namespace/list).
    elif action == "namespace_list":
        result = _request("GET", "/namespaces")
        return json.dumps(result, indent=2, ensure_ascii=False) if result else "No namespaces found."

    # FIX: Server route is POST /stats with body (GET /stats?namespace= 404s due
    # to exact route match in handlers.rs line 465).
    elif action == "namespace_stats":
        ns = kwargs.get("namespace", "default")
        result = _request("POST", "/stats", {"namespace": ns})
        return json.dumps(result, indent=2, ensure_ascii=False) if result else "Namespace not found."

    # -- Tag actions ----
    # FIX: Server route is GET /tags (not /tags/list).
    elif action == "tags_list":
        ns = kwargs.get("namespace", "")
        path = "/tags" + (f"?namespace={ns}" if ns else "")
        result = _request("GET", path)
        return json.dumps(result, indent=2, ensure_ascii=False) if result else "No tags found."

    elif action == "tags_rename":
        old_tag = kwargs.get("old", "")
        new_tag = kwargs.get("new", "")
        result = _request("POST", "/tags/rename", {"old": old_tag, "new": new_tag, "namespace": namespace})
        if "error" not in result:
            return f"\u2713 Tag '{old_tag}' renamed to '{new_tag}'"
        return result

    # FIX: Server route is POST /tags/delete with body (not DELETE /tags/delete?tag=X).
    elif action == "tags_delete":
        tag_name = kwargs.get("tag", "")
        result = _request("POST", "/tags/delete", {"tag": tag_name, "namespace": namespace})
        if "error" not in result:
            return f"\u2713 Tag '{tag_name}' deleted"
        return result

    # -- Maintenance actions ----
    elif action == "pin":
        mem_id = kwargs.get("id", "")
        result = _request("POST", "/pin", {"id": mem_id})
        if "error" not in result:
            return f"\u2713 Memory pinned: {mem_id}"
        return result

    elif action == "unpin":
        mem_id = kwargs.get("id", "")
        result = _request("POST", "/unpin", {"id": mem_id})
        if "error" not in result:
            return f"\u2713 Memory unpinned: {mem_id}"
        return result

    # FIX: /importance is a global recompute — no id parameter needed.
    elif action == "importance":
        result = _request("POST", "/importance", {})
        return json.dumps(result, indent=2, ensure_ascii=False) if result else "Importance failed."

    # FIX: Server expects POST /consolidate with JSON body (not query params).
    elif action == "consolidate":
        threshold = kwargs.get("threshold", 0.6)
        dry_run = kwargs.get("dry_run", False)
        result = _request("POST", "/consolidate", {"threshold": threshold, "dry_run": dry_run, "namespace": namespace})
        # Empty list [] means no duplicates found — that's a success, not a failure.
        return json.dumps(result, indent=2, ensure_ascii=False) if result is not None else "Consolidate failed."

    # FIX: Server expects action/dry_run/older_than_days/max_access_count (not sub/days).
    elif action == "aging":
        action_type = kwargs.get("sub", kwargs.get("action", "status"))
        days = kwargs.get("days", kwargs.get("older_than_days", 90))
        dry_run = kwargs.get("dry_run", False)
        result = _request("POST", "/aging", {
            "action": action_type,
            "dry_run": dry_run,
            "older_than_days": int(days) if str(days).isdigit() else 90,
            "namespace": namespace,
        })
        return json.dumps(result, indent=2, ensure_ascii=False) if result else "Aging failed."

    elif action == "export":
        result = _request("GET", "/export")
        return json.dumps(result, indent=2, ensure_ascii=False) if isinstance(result, (dict, list)) else str(result)

    # FIX: Server expects {"content": ...} field (not {"data": ...}).
    elif action == "import":
        file_path = kwargs.get("path", "")
        if not file_path:
            return {"error": "Missing required parameter: path"}
        try:
            with open(file_path, "r") as f:
                data = f.read()
            result = _request("POST", "/import", {"content": data, "namespace": namespace})
            if "error" not in result:
                return f"\u2713 Imported from {file_path}"
            return result
        except FileNotFoundError:
            return {"error": f"File not found: {file_path}"}

    # FIX: No /doctor route on server — use GET /health for diagnostics.
    elif action == "doctor":
        result = _request("GET", "/health")
        return json.dumps(result, indent=2, ensure_ascii=False) if result else "Health check failed."

    # FIX: No /init route on server — namespaces are auto-created on first write.
    elif action == "init":
        result = _request("GET", "/health")
        if "error" not in result:
            return f"\u2713 Namespace '{namespace}' ready (auto-created on first write)"
        return result

    return f"Unknown action: {action}"
