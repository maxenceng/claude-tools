#!/usr/bin/env python3
"""Semantic search over a project's docs, synced by sync_docs.py.

Usage: search_docs.py <project> <query text>
<project> is folded the same way sync_docs.py names the collection: the
final path component, hyphens replaced with underscores. A bare project
name and a full project path both resolve to the same collection.
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
SNIPPET_LENGTH = 200
HARD_TOKEN_LIMIT = 512


def embed(text):
    req = urllib.request.Request(
        f"{EMBEDDINGS_URL}/embed",
        data=json.dumps({"inputs": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)[0]


def count_tokens(text):
    req = urllib.request.Request(
        f"{EMBEDDINGS_URL}/tokenize",
        data=json.dumps({"inputs": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return len(json.load(resp)[0])


def snippet(text):
    text = " ".join(text.split())
    if len(text) <= SNIPPET_LENGTH:
        return text
    return text[:SNIPPET_LENGTH].rsplit(" ", 1)[0] + "…"


def main():
    if len(sys.argv) < 3:
        print("usage: search_docs.py <project> <query text>", file=sys.stderr)
        sys.exit(1)

    collection = os.path.basename(os.path.normpath(sys.argv[1])).replace("-", "_")
    query = " ".join(sys.argv[2:]).strip()

    query_tokens = count_tokens(query)
    if query_tokens > HARD_TOKEN_LIMIT:
        print(
            f"warning: query is {query_tokens} tokens, over the model's "
            f"{HARD_TOKEN_LIMIT} cap -- it will be truncated before matching",
            file=sys.stderr,
        )

    vector = embed(query)
    req = urllib.request.Request(
        f"{QDRANT_URL}/collections/{collection}/points/query",
        data=json.dumps({"query": vector, "limit": 5, "with_payload": True}).encode(),
        headers={"Content-Type": "application/json", "api-key": QDRANT_API_KEY},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            points = json.load(resp)["result"]["points"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"no collection '{collection}' -- run sync-docs for this project first", file=sys.stderr)
            sys.exit(1)
        raise

    if not points:
        print("no results")
        return

    for p in points:
        payload = p["payload"]
        chunk = f" (chunk {payload['chunk_index'] + 1}/{payload['chunk_count']})" if payload.get("chunk_count", 1) > 1 else ""
        print(f"{p['score']:.3f}  [{payload['doc_type']}] {payload['path']}{chunk}")
        print(f"    {snippet(payload['content'])}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
