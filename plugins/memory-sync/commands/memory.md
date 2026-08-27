---
description: Mirror project memory into Qdrant, or search it semantically
argument-hint: "[sync | search <query>]"
---

Memory lives at `~/.claude/projects/*/memory/*.md` — one directory per project, each
with a `MEMORY.md` index and individual files carrying frontmatter (`name`,
`description`, `metadata.type`) and free-text content. Those files stay authoritative;
this command mirrors them into a Qdrant collection so they're searchable by meaning
across every project at once, the same way `/ticket` mirrors backlog status to Vikunja
without the markdown stopping being the source of truth.

Requires `QDRANT_URL`, `QDRANT_API_KEY` and `EMBEDDINGS_URL` in the shell environment.
Where any is unset, say so and stop — there is nothing useful to fall back to for this
command, unlike `/ticket`'s sync, since mirroring is the entire point.

Dispatch on the first word:

- **`sync`** — run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync.py`. It walks every memory
  file, skips `MEMORY.md` (an index, not content), embeds each one whole via the
  embeddings service, and upserts it into the `claude_memory` collection keyed by a
  hash of the file's path — so re-running after a memory file changes updates that
  point in place rather than duplicating it. The collection is created on first run
  with whatever vector size the embedding model actually returns, never a hardcoded
  guess. Report what it printed; do not re-describe it.

- **`search <query>`** — run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/search.py <query>`.
  Embeds the query, returns the five nearest memory files by cosine similarity with
  their project, name, description and path. Read the file at the path before acting
  on what a result implies — the payload carries the content too, but a search result
  is a pointer, not a substitute for reading the memory the way any other memory access
  would.

No arguments: report that `sync` and `search <query>` are the two things this command
does, and stop. It does not run a sync automatically — memory changes at the pace of a
conversation, and syncing on every invocation would mean re-embedding files that have
not changed most of the time.
