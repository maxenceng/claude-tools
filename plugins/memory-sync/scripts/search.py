#!/usr/bin/env python3
"""Semantic search over memory files synced by sync.py.

Usage: search.py <query text>
Requires QDRANT_URL, QDRANT_API_KEY, EMBEDDINGS_URL in the environment.
"""
import json
import os
import sys
import urllib.error
import urllib.request

QDRANT_URL = os.environ["QDRANT_URL"].rstrip("/")
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
EMBEDDINGS_URL = os.environ["EMBEDDINGS_URL"].rstrip("/")
COLLECTION = "claude_memory"


def embed(text):
    req = urllib.request.Request(
        f"{EMBEDDINGS_URL}/embed",
        data=json.dumps({"inputs": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)[0]


def main():
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        print("usage: search.py <query text>", file=sys.stderr)
        sys.exit(1)

    vector = embed(query)
    req = urllib.request.Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/query",
        data=json.dumps({"query": vector, "limit": 5, "with_payload": True}).encode(),
        headers={"Content-Type": "application/json", "api-key": QDRANT_API_KEY},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        points = json.load(resp)["result"]["points"]

    if not points:
        print("no results")
        return

    for p in points:
        payload = p["payload"]
        print(f"{p['score']:.3f}  [{payload['project']}] {payload['name']}")
        print(f"    {payload['description']}")
        print(f"    {payload['path']}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
