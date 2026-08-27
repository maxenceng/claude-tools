#!/usr/bin/env python3
"""Embed every ~/.claude/projects/*/memory/*.md file into Qdrant.

Requires QDRANT_URL, QDRANT_API_KEY, EMBEDDINGS_URL in the environment. MEMORY.md
files are skipped -- they're an index over the other files, not memory content
themselves. Re-running is safe: point ids are derived from the file path, so an
unchanged file re-embeds to the same id and a changed one updates it in place.
"""
import glob
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

import yaml

QDRANT_URL = os.environ["QDRANT_URL"].rstrip("/")
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
EMBEDDINGS_URL = os.environ["EMBEDDINGS_URL"].rstrip("/")
COLLECTION = "claude_memory"
NAMESPACE = uuid.UUID("6c7e6b1a-6b0b-4c9a-9f3e-6a2f8c1d9b4e")


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


def ensure_collection(vector_size):
    try:
        qdrant("GET", f"/collections/{COLLECTION}")
        return
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    qdrant(
        "PUT",
        f"/collections/{COLLECTION}",
        {"vectors": {"size": vector_size, "distance": "Cosine"}},
    )


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text
    _, raw_fm, body = text.split("---\n", 2)
    return (yaml.safe_load(raw_fm) or {}), body


def main():
    files = [
        f
        for f in glob.glob(os.path.expanduser("~/.claude/projects/*/memory/*.md"))
        if os.path.basename(f) != "MEMORY.md"
    ]
    if not files:
        print("no memory files found")
        return

    probe_vector = embed("dimension probe")
    ensure_collection(len(probe_vector))

    points = []
    for path in files:
        text = open(path, encoding="utf-8").read()
        frontmatter, _ = parse_frontmatter(text)
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
    print(f"synced {len(points)} memory files across {len({p['payload']['project'] for p in points})} projects")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
