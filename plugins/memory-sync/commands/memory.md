---
description: Mirror project memory or project docs into Qdrant, or search either semantically
argument-hint: "[sync | search <query> | sync-docs <project-path> | search-docs <project> <query>]"
---

Memory lives at `~/.claude/projects/*/memory/*.md` — one directory per project, each
with a `MEMORY.md` index and individual files carrying frontmatter (`name`,
`description`, `metadata.type`) and free-text content. Those files stay authoritative;
this command mirrors them into a Qdrant collection so they're searchable by meaning
across every project at once, the same way `/ticket` mirrors backlog status to Vikunja
without the markdown stopping being the source of truth.

A project's own knowledge — glossary, ADRs, context map, CLAUDE.md, backlog — is a
different kind of thing (domain/architecture knowledge, not "how Claude should
behave") and lives in the project's own repo, not under `~/.claude/projects/`.
`sync-docs` mirrors that into a Qdrant collection dedicated to the one project, kept
separate from `claude_memory` and from every other project's docs.

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
  Searches `claude_memory` only, not any project's docs collection — use `search-docs`
  for that. Embeds the query, returns the five nearest memory files by cosine
  similarity with their project, name, description and path. Read the file at the path
  before acting on what a result implies — the payload carries the content too, but a
  search result is a pointer, not a substitute for reading the memory the way any other
  memory access would.

- **`sync-docs <project-path>`** — run
  `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_docs.py <project-path>`. It globs
  `CLAUDE.md`, `docs/glossary.md`, `docs/context-map.md`, `docs/adr/*.md` and
  `docs/backlog/*.md` under the given project path (skipping `_template.md`), splits
  each into markdown-aware chunks (heading/paragraph/table/code-fence boundaries) sized
  against the embedding model's real tokenizer so no chunk exceeds its input window,
  and upserts into a collection named after the project directory with hyphens folded
  to underscores (`next-suggestions` → `next_suggestions`) — created on first run with
  whatever vector size the embedding model returns. Each chunk carries the nearest
  heading(s) it fell under, so it reads on its own in a search result. The collection
  is dropped and rebuilt from scratch on every run rather than upserted in place, since
  every file is re-embedded unconditionally each time anyway and a fixed chunk count
  would otherwise leave stale chunks behind whenever a file shrinks. Report what it
  printed; do not re-describe it.

- **`search-docs <project> <query>`** — run
  `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/search_docs.py <project> <query>`. `<project>`
  is folded the same way `sync-docs` names the collection (final path component,
  hyphens to underscores), so either a bare name like `next-suggestions` or a full
  project path works. Embeds the query, returns the five nearest chunks by cosine
  similarity with their doc type, path and a snippet. If the collection doesn't exist
  yet it says so and stops rather than raising a raw HTTP error — run `sync-docs` for
  that project first. As with `search`, the snippet is a pointer: read the file before
  acting on what a result implies, and expect several hits from the same file at
  different chunks rather than one hit per file.

No arguments: report that `sync`, `search <query>`, `sync-docs <project-path>` and
`search-docs <project> <query>` are the four things this command does, and stop. It
does not run a sync automatically — docs and memory change at the pace of a
conversation, and syncing on every invocation would mean re-embedding files that have
not changed most of the time.
