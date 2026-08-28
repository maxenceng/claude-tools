#!/usr/bin/env python3
"""Embed a project's durable docs into a dedicated Qdrant collection.

Usage: sync_docs.py <project-path>
Requires QDRANT_URL, QDRANT_API_KEY, EMBEDDINGS_URL in the environment. The
collection is named after the project directory, hyphens folded to
underscores (next-suggestions -> next_suggestions), separate from any other
project's collection and from claude_memory. Re-running is safe: point ids
are derived from the file path, so an unchanged file re-embeds to the same
id and a changed one updates it in place. A file removed from disk since the
last sync is left in Qdrant -- this script only ever upserts.
"""
import glob
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

QDRANT_URL = os.environ["QDRANT_URL"].rstrip("/")
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
EMBEDDINGS_URL = os.environ["EMBEDDINGS_URL"].rstrip("/")
NAMESPACE = uuid.UUID("641ec3d1-3e8a-4ee2-86d6-03ae5bf27e64")

DOC_GLOBS = [
    ("CLAUDE.md", "conventions"),
    ("docs/glossary.md", "glossary"),
    ("docs/context-map.md", "context-map"),
    ("docs/adr/*.md", "adr"),
    ("docs/backlog/*.md", "backlog"),
]
EXCLUDE_BASENAMES = {"_template.md"}


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


def ensure_collection(collection, vector_size):
    try:
        qdrant("GET", f"/collections/{collection}")
        return
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    qdrant(
        "PUT",
        f"/collections/{collection}",
        {"vectors": {"size": vector_size, "distance": "Cosine"}},
    )


def find_files(project_root):
    for pattern, doc_type in DOC_GLOBS:
        for path in sorted(glob.glob(os.path.join(project_root, pattern))):
            if os.path.basename(path) in EXCLUDE_BASENAMES:
                continue
            yield path, doc_type


def main():
    if len(sys.argv) != 2:
        print("usage: sync_docs.py <project-path>", file=sys.stderr)
        sys.exit(1)

    project_root = os.path.abspath(sys.argv[1])
    project = os.path.basename(project_root)
    collection = project.replace("-", "_")

    files = list(find_files(project_root))
    if not files:
        print(f"no docs found under {project_root}")
        return

    probe_vector = embed("dimension probe")
    ensure_collection(collection, len(probe_vector))

    points = []
    for path, doc_type in files:
        text = open(path, encoding="utf-8").read()
        rel_path = os.path.relpath(path, project_root)
        vector = embed(text)
        points.append(
            {
                "id": str(uuid.uuid5(NAMESPACE, rel_path)),
                "vector": vector,
                "payload": {
                    "path": rel_path,
                    "project": project,
                    "doc_type": doc_type,
                    "mtime": os.path.getmtime(path),
                    "content": text,
                },
            }
        )

    qdrant("PUT", f"/collections/{collection}/points?wait=true", {"points": points})
    print(f"synced {len(points)} docs from {project} into collection '{collection}'")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
