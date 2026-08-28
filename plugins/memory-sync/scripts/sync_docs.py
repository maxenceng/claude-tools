#!/usr/bin/env python3
"""Embed a project's durable docs into a dedicated Qdrant collection.

Usage: sync_docs.py <project-path>
Requires QDRANT_URL, QDRANT_API_KEY, EMBEDDINGS_URL in the environment. The
collection is named after the project directory, hyphens folded to
underscores (next-suggestions -> next_suggestions), separate from any other
project's collection and from claude_memory.

A doc is split into markdown-aware chunks (heading/paragraph/table/code-fence
boundaries) sized against the embedding model's real tokenizer via its
/tokenize endpoint, so a long ADR or backlog ticket is embedded as several
chunks that each fit the model's input window instead of one oversized
string the service would silently truncate. Each chunk is prefixed with its
nearest heading(s) so it stays legible on its own in a search result.

Each run drops and recreates the collection rather than trying to upsert in
place -- the script re-embeds every file unconditionally on every run
anyway, and a fixed chunk count per file would otherwise leave stale chunks
behind whenever a file shrinks. Point ids are still derived deterministically
from (path, chunk index) for traceability, not for upsert safety.
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
RESERVED_COLLECTIONS = {"claude_memory"}

DOC_GLOBS = [
    ("CLAUDE.md", "conventions"),
    ("docs/glossary.md", "glossary"),
    ("docs/context-map.md", "context-map"),
    ("docs/adr/*.md", "adr"),
    ("docs/backlog/*.md", "backlog"),
]
EXCLUDE_BASENAMES = {"_template.md"}

# Leaves headroom under the model's real cap (checked per assembled chunk
# below) for the [CLS]/[SEP] specials and the token-count approximation
# error from summing block counts instead of retokenizing every join.
CHUNK_TOKEN_BUDGET = 450
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
    if not text.strip():
        return 0
    req = urllib.request.Request(
        f"{EMBEDDINGS_URL}/tokenize",
        data=json.dumps({"inputs": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return len(json.load(resp)[0])


def qdrant(method, path, body=None):
    req = urllib.request.Request(
        f"{QDRANT_URL}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json", "api-key": QDRANT_API_KEY},
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def recreate_collection(collection, vector_size):
    try:
        qdrant("DELETE", f"/collections/{collection}")
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


def split_blocks(text):
    """Split on blank lines, keeping fenced code blocks intact.

    Markdown tables need no special case: their rows have no blank lines
    between them, so a table already survives as one block.
    """
    blocks = []
    current = []
    in_fence = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            current.append(line)
            in_fence = not in_fence
            continue
        if not in_fence and stripped == "":
            if current:
                blocks.append("\n".join(current))
                current = []
            continue
        current.append(line)
    if current:
        blocks.append("\n".join(current))
    return [b for b in blocks if b.strip()]


def is_heading(block):
    lines = block.strip("\n").splitlines()
    return len(lines) == 1 and lines[0].lstrip().startswith("#")


def heading_level(block):
    line = block.strip().lstrip()
    return len(line) - len(line.lstrip("#"))


def split_oversized(block, budget):
    lines = block.split("\n")
    pieces = []
    current_lines = []
    current_tokens = 0
    for line in lines:
        line_tokens = count_tokens(line)
        if current_lines and current_tokens + line_tokens > budget:
            pieces.append("\n".join(current_lines))
            current_lines, current_tokens = [line], line_tokens
        else:
            current_lines.append(line)
            current_tokens += line_tokens
    if current_lines:
        pieces.append("\n".join(current_lines))
    return pieces


def chunk_document(text, budget=CHUNK_TOKEN_BUDGET):
    blocks = split_blocks(text)
    chunks = []
    h1 = h2 = None
    current, current_tokens = [], 0

    def flush():
        if current:
            chunks.append("\n\n".join(current))

    def start_new(piece, piece_tokens):
        prefix = "\n\n".join(h for h in (h1, h2) if h)
        if prefix and piece not in (h1, h2):
            return [prefix, piece], count_tokens(prefix) + piece_tokens
        return [piece], piece_tokens

    for block in blocks:
        if is_heading(block):
            level = heading_level(block)
            if level <= 1:
                h1, h2 = block, None
            else:
                h2 = block

        block_tokens = count_tokens(block)
        pieces = [(block, block_tokens)]
        if block_tokens > budget:
            flush()
            current, current_tokens = [], 0
            pieces = [(p, count_tokens(p)) for p in split_oversized(block, budget)]

        for piece, piece_tokens in pieces:
            if not current:
                current, current_tokens = start_new(piece, piece_tokens)
            elif current_tokens + piece_tokens <= budget:
                current.append(piece)
                current_tokens += piece_tokens
            else:
                flush()
                current, current_tokens = start_new(piece, piece_tokens)

    flush()
    return [c for c in chunks if c.strip()]


def main():
    if len(sys.argv) != 2:
        print("usage: sync_docs.py <project-path>", file=sys.stderr)
        sys.exit(1)

    project_root = os.path.abspath(sys.argv[1])
    project = os.path.basename(project_root)
    collection = project.replace("-", "_")

    if collection in RESERVED_COLLECTIONS:
        print(
            f"refusing to sync '{project}' -- it folds to the reserved collection "
            f"name '{collection}', which sync.py owns and this script would drop",
            file=sys.stderr,
        )
        sys.exit(1)

    files = list(find_files(project_root))
    if not files:
        print(f"no docs found under {project_root}")
        return

    probe_vector = embed("dimension probe")
    recreate_collection(collection, len(probe_vector))

    points = []
    chunked_files = 0
    for path, doc_type in files:
        text = open(path, encoding="utf-8").read()
        rel_path = os.path.relpath(path, project_root)
        chunks = chunk_document(text)
        if len(chunks) > 1:
            chunked_files += 1

        for i, chunk in enumerate(chunks):
            tokens = count_tokens(chunk)
            if tokens > HARD_TOKEN_LIMIT:
                print(
                    f"warning: {rel_path} chunk {i} is {tokens} tokens, "
                    f"over the model's {HARD_TOKEN_LIMIT} cap -- it will be truncated",
                    file=sys.stderr,
                )
            vector = embed(chunk)
            points.append(
                {
                    "id": str(uuid.uuid5(NAMESPACE, f"{rel_path}#{i}")),
                    "vector": vector,
                    "payload": {
                        "path": rel_path,
                        "project": project,
                        "doc_type": doc_type,
                        "mtime": os.path.getmtime(path),
                        "chunk_index": i,
                        "chunk_count": len(chunks),
                        "content": chunk,
                    },
                }
            )

    qdrant("PUT", f"/collections/{collection}/points?wait=true", {"points": points})
    print(
        f"synced {len(points)} chunks from {len(files)} docs "
        f"({chunked_files} split into multiple chunks) from {project} "
        f"into collection '{collection}'"
    )


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
