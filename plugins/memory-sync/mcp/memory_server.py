#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp", "pyyaml"]
# ///
"""MCP server exposing the same claude_memory Qdrant collection scripts/search.py
and scripts/sync.py already read and write, as direct tool calls instead of shelled-out
scripts. Kept as its own self-contained file, duplicating embed()/qdrant() rather than
importing the scripts - the same "no shared module" shape every script in this plugin
already uses.

Requires QDRANT_URL, QDRANT_API_KEY, EMBEDDINGS_URL in the environment the MCP client
launches this process with.
"""
import glob
import json
import os
import urllib.error
import urllib.request
import uuid

import yaml
from mcp.server.mcpserver import MCPServer

QDRANT_URL = os.environ["QDRANT_URL"].rstrip("/")
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
EMBEDDINGS_URL = os.environ["EMBEDDINGS_URL"].rstrip("/")
COLLECTION = "claude_memory"
NAMESPACE = uuid.UUID("6c7e6b1a-6b0b-4c9a-9f3e-6a2f8c1d9b4e")

mcp = MCPServer("memory")


def embed(text):
    req = urllib.request.Request(
        f"{EMBEDDINGS_URL}/embed",
        data=json.dumps({"inputs": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)[0]


def qdrant(method, path, body=None):
    req = urllib.request.Request(
        f"{QDRANT_URL}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json", "api-key": QDRANT_API_KEY},
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


@mcp.tool()
def memory_search(query: str, limit: int = 5) -> str:
    """Semantically search every synced memory file across every project and user.

    Use to check whether something similar to a correction or convention was already
    recorded - by you in an earlier session, or by a teammate syncing to the same
    collection - before writing a new memory file or repeating a question already
    answered elsewhere.
    """
    vector = embed(query)
    result = qdrant(
        "POST",
        f"/collections/{COLLECTION}/points/query",
        {"query": vector, "limit": limit, "with_payload": True},
    )
    points = result["result"]["points"]
    if not points:
        return "no results"

    lines = []
    for p in points:
        payload = p["payload"]
        lines.append(f"{p['score']:.3f}  [{payload['project']}] {payload['name']}")
        lines.append(f"    {payload['description']}")
        lines.append(f"    {payload['path']}")
    return "\n".join(lines)


def _parse_frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text
    _, raw_fm, body = text.split("---\n", 2)
    return (yaml.safe_load(raw_fm) or {}), body


@mcp.tool()
def memory_sync() -> str:
    """Push every local ~/.claude/projects/*/memory/*.md file into the shared claude_memory
    collection, same as running `/memory sync`. Call after writing new memory files if they
    should be searchable (by you or a teammate) before this session ends - a SessionEnd hook
    already does this automatically, so this is only needed for making memory searchable
    mid-session.
    """
    files = [
        f
        for f in glob.glob(os.path.expanduser("~/.claude/projects/*/memory/*.md"))
        if os.path.basename(f) != "MEMORY.md"
    ]
    if not files:
        return "no memory files found"

    probe_vector = embed("dimension probe")
    try:
        qdrant("GET", f"/collections/{COLLECTION}")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        qdrant("PUT", f"/collections/{COLLECTION}", {"vectors": {"size": len(probe_vector), "distance": "Cosine"}})

    points = []
    for path in files:
        text = open(path, encoding="utf-8").read()
        frontmatter, _ = _parse_frontmatter(text)
        metadata = frontmatter.get("metadata") or {}
        project = path.split("/.claude/projects/", 1)[1].split("/memory/", 1)[0]
        vector = embed(text)
        points.append(
            {
                "id": str(uuid.uuid5(NAMESPACE, path)),
                "vector": vector,
                "payload": {
                    "path": path,
                    "project": project,
                    "name": frontmatter.get("name"),
                    "description": frontmatter.get("description"),
                    "type": metadata.get("type"),
                    "mtime": os.path.getmtime(path),
                    "content": text,
                },
            }
        )

    qdrant("PUT", f"/collections/{COLLECTION}/points?wait=true", {"points": points})
    projects = len({p["payload"]["project"] for p in points})
    return f"synced {len(points)} memory files across {projects} projects"


if __name__ == "__main__":
    mcp.run()
