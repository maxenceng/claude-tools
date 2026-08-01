# Backlog

Features to do and their status, as markdown in the repo.

It lives here rather than in a separate tool so that a status change rides along in the
branch and the PR that caused it. "What state was this in when we merged" is then a
question history answers, not one anybody has to remember.

Open this folder — or the repo root — as an Obsidian vault to get a board over it. Nothing
here depends on Obsidian: the files are plain markdown with YAML frontmatter, and
`/ticket` reads and writes them directly.

## Naming

`<CONTEXT>-<n>-<short-slug>.md`, where `<CONTEXT>` is the bounded context the work sits
in — `CONTEXT-1-short-slug.md`. A ticket that cannot be given a context prefix is
usually two tickets, or a sign the context does not exist yet. Both are worth knowing
before any code is written.

## Frontmatter

| Field | Values | Why it is there |
|---|---|---|
| `id` | `CONTEXT-1` | Matches the filename and the branch name. |
| `status` | `todo`, `in-progress`, `in-review`, `done` | Advanced by `/ticket`, not by hand. |
| `context` | a bounded context, or `cross-context` | The first question any backend work asks. |
| `type` | `feature`, `fix`, `chore`, `spike` | |
| `created` | `YYYY-MM-DD` | Absolute dates only — "last week" ages badly. |

`cross-context` is deliberately awkward to write. A ticket that genuinely spans contexts
is a modelling event and deserves a second look before it becomes code.

## Board

With the Dataview community plugin installed, this renders as a live table:

````
```dataview
TABLE status, context, type, created
FROM "docs/backlog"
WHERE id
SORT status ASC, id ASC
```
````

Obsidian's built-in Bases can do the same over the properties above if you prefer not to
install a plugin. The frontmatter is the interface either way.

## Status, and what moves it

| Status | Means | Set when |
|---|---|---|
| `todo` | Understood well enough to start. | `/ticket new` |
| `in-progress` | Branch exists, work underway. | `/ticket start` |
| `in-review` | Pushed, under review. | `/ticket review` |
| `done` | Merged. | `/ticket done` |

A ticket in `todo` with an empty **Model decision** is not ready to start. That section is
the point of the whole file — the acceptance criteria come from whoever wrote the ticket,
but where the behaviour belongs is a decision this project makes, and it is the one most
expensive to get wrong.
