# Design iteration and endpoint call-flow atlas

Two additions to `ddd-workflow` and the `spring-ddd` template, borrowing from
[impeccable](https://github.com/pbakaus/impeccable) (UI design quality) and
[archify](https://github.com/tt-a1i/archify) (diagram rendering).

## Part 1 — impeccable in the ticket flow

### Goal

A UI ticket gets a design direction before code, an interactive design loop with the
human between `start` and `review`, and a deterministic anti-pattern gate in CI.

### Dependency

Impeccable ships a Claude Code plugin: `/plugin marketplace add pbakaus/impeccable`, skill
`impeccable`. Every reference in this plugin is qualified `impeccable:impeccable`, so
`verify-plugin.sh` lists it as a declared dependency. README documents the install.

### Plugin changes (`plugins/ddd-workflow/`)

**`ticket-steps/new.md`** — the written ticket gains a `## Design direction` section with
the `_Not analysed yet — /ticket refine CONTEXT-7._` marker, between *Model decision* and
*Glossary impact*.

**`ticket-steps/refine.md`** — when the ticket touches `frontend/**`:
- If `PRODUCT.md` is missing at the project root, stop and ask for `/impeccable init`
  first. A direction without product context is a guess.
- Invoke `impeccable:impeccable` with `shape` and fill *Design direction* from its result.
- For a ticket that does not touch the frontend, write `n/a` so a reader can tell it was
  considered.

**`ticket-steps/start.md`** — refuse a frontend ticket whose *Design direction* is still
the unanalysed marker, with the same reasoning as an empty *Model decision*.

**`ticket-steps/design.md`** (new verb, `/ticket design <ID>`):
- Precondition: `status: in-progress` and the ticket touches `frontend/**`. Status is not
  changed by this verb.
- Setup: `make run` (backend) and `make -C frontend dev`, both in the background.
- Loop, one round at a time:
  1. `npx impeccable detect http://localhost:5173/<route>`; fix any finding immediately,
     with no question asked — detector hits are not taste.
  2. Screenshot the route through `claude-in-chrome`.
  3. Invoke `impeccable:impeccable` with `critique`; show the human the screenshot and
     the critique together.
  4. The human picks a named move (`quieter`, `bolder`, `polish`, `distill`, …) or gives
     free-form feedback; apply it.
- The loop ends only when the human says it is done. This verb exists because taste is
  where the human's judgement is actually needed; it never self-terminates.
- If the direction itself moved, update *Design direction* and log the change in
  *Notes*. Critique reports land in `.impeccable/critique/` by impeccable's own default.

**`ticket-steps/review.md`** — for a diff touching `frontend/**`, invoke
`impeccable:impeccable` with `audit` as a third reviewer, beside `architecture-reviewer`
and the correctness review, scoped to the changed frontend files.

**`commands/ticket.md`** — add `design` to `argument-hint` and the dispatch list.

### Template changes (`templates/spring-ddd/`)

- `frontend/package.json`: `impeccable` as a pinned devDependency, so CI does not resolve
  whatever `npx` finds that day.
- `frontend/Makefile`: `design-check` target running `impeccable detect`, added to `ci`
  (and therefore `fe-ci` and `verify`). Non-zero exit (2 = findings, 1 = scan failure)
  fails the build.
- `.impeccable/config.json`: committed, with only the ignores the template itself needs.
- `docs/backlog/_template.md`: the `## Design direction` section.
- Rebuild the archetype with `scripts/build-archetype.sh`.

**Validation first:** run `impeccable detect src/` on the template before wiring the
target. If the static scan reads TSX + Tailwind poorly, the gate scans the built `dist/`
instead (so `design-check` runs after `build`), and the URL scan stays in the `design`
loop only.

## Part 2 — endpoint call-flow atlas

### Goal

Every endpoint that has been through a ticket has a committed sequence diagram, so the
project's call flows can be found and browsed in GitHub and in the Obsidian vault.

### Dependency

Archify is not a Claude Code plugin; it installs as a skill with
`npx skills add tt-a1i/archify -g`. It cannot be a declared `plugin:` dependency, so the
command checks for the skill at startup and stops with the install line when it is
absent. `verify-plugin.sh` gets an explicit allowance for the `archify` reference.

### Output

```
docs/endpoints/
  README.md                       index: context → endpoints, linked
  <context>/POST-api-orders.md    primary: Mermaid sequenceDiagram + evidence
  <context>/POST-api-orders.html  archify interactive render
```

Each `.md` carries:
- frontmatter: `endpoint`, `context`, `traced_at: <commit sha>`, `tickets: [...]`;
- a Mermaid `sequenceDiagram` (renders natively in GitHub and Obsidian);
- an evidence table: step → `file:line`;
- error branches as `alt` blocks, each with the HTTP status the error kernel maps it to.

### The trace

`codebase-explorer` follows one endpoint and returns a fixed shape:
- participants, each tagged with its layer: `adapter-in`, `application`, `domain`,
  `port`, `adapter-out`, `external`;
- messages in call order, each with `file:line`;
- error branches with their HTTP status;
- the transaction boundary;
- events published, and other contexts reached through their published, query or
  command packages.

The main session renders that shape twice — Mermaid into the `.md`, archify sequence IR
into the `.html` (`archify validate` must pass before the file is written). If archify's
sequence IR cannot express `alt` branches, they become notes in the HTML; the Mermaid
version keeps them as `alt`.

### Plugin changes

**`commands/trace-endpoint.md`** (new) — `/trace-endpoint <METHOD> <path>`: check for
archify, trace, render both files, update the index. On demand; also how endpoints that
predate this feature get into the atlas.

**`ticket-steps/done.md`** — a new step after the ADR step: find the endpoints the ticket
added or changed (controllers in the merged diff, plus controllers whose call path reaches
a changed class), re-trace each through `/trace-endpoint`, delete files for removed
endpoints, update the index. All of it lands in the same PR that sets `status: done`.
Tracing at `done` means it is traced from merged code.

**`commands/onboard.md`** — report stale diagrams: for each `.md`, compare `traced_at`
against `git log` on its evidence files; list those with later changes and offer to
re-trace. Report only, never a gate.

## Shared

- README: both features, both dependencies and how to install them.
- HOWTO.md: the `design` verb in the ticket loop; where the atlas lives.
- Bump `ddd-workflow` version in `plugin.json`.
- CI must stay green: `verify-plugin.sh`, `check-plugin-version-bump.sh`,
  `verify-archetype.sh`.

## Out of scope

- Review-time call-flow diagrams in the PR body (dropped: one trigger, at `done`).
- An autonomous design loop inside `start`.
- Generating the whole atlas in `make docs`.
- Copying impeccable's prose guidance into this plugin (`frontend-design` already
  overlaps it).
