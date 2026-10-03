# Design Iteration and Endpoint Atlas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an impeccable-driven design loop to frontend tickets, an impeccable detector gate to the template's CI, and an archify/Mermaid endpoint call-flow atlas written at `/ticket done`.

**Architecture:** Almost everything is prose in `plugins/ddd-workflow/` (commands and ticket steps), checked by `scripts/verify-plugin.sh`. The template gains one Make target, one devDependency and one config file, checked by `make -C frontend ci` and `scripts/verify-archetype.sh`. Archify is a skill rather than a plugin, so `verify-plugin.sh` learns an explicit allow-list for non-plugin skills.

**Tech Stack:** Markdown commands/steps, Python (inside `verify-plugin.sh`), Bash, GNU Make, npm (`impeccable@4.1.0`), Maven archetype.

**Spec:** `docs/superpowers/specs/2026-10-03-impeccable-archify-design.md`

## Global Constraints

- Impeccable is referenced as `impeccable:impeccable` (a declared plugin dependency; install: `/plugin marketplace add pbakaus/impeccable`).
- Archify is referenced as the `archify` skill (not a plugin; install: `npx skills add tt-a1i/archify -g`); a command using it checks for it and stops with that install line when absent.
- `impeccable` npm package pinned exactly: `"impeccable": "4.1.0"` (no caret).
- Atlas lives in `docs/endpoints/` of the generated project: `<context>/<METHOD>-<slug>.md` + `.html`, plus `README.md` index.
- Slug rule: path without leading `/`, `/` → `-`, `{` and `}` removed. `POST /api/orders/{id}/lines` → `POST-api-orders-id-lines`.
- Endpoint `.md` frontmatter: `endpoint`, `context`, `traced_at` (full commit sha), `tickets` (list of ids).
- Edit the template, never `templates/spring-ddd-archetype/` directly; rebuild with `./scripts/build-archetype.sh`.
- `ddd-workflow` version bumps once, in the last task, `1.6.5` → `1.7.0`.
- Write prose in the repository's existing voice: second person imperative, reasons given inline, no emoji, no bullet soup where a sentence works.

---

### Task 1: `/trace-endpoint` command and the non-plugin skill allowance

**Files:**
- Create: `plugins/ddd-workflow/commands/trace-endpoint.md`
- Modify: `scripts/verify-plugin.sh:199-226` (the cross-reference check) and the summary print block below it

**Interfaces:**
- Produces: the `/trace-endpoint <METHOD> <path>` command, which Tasks 2 and 3 invoke by name; the file layout and frontmatter listed in Global Constraints.
- Produces: `NON_PLUGIN_SKILLS` in `verify-plugin.sh` — a dict `{name: install_command}`.

- [ ] **Step 1: Write the command (this is the failing case for the checker)**

Create `plugins/ddd-workflow/commands/trace-endpoint.md`:

`````markdown
---
description: Trace one endpoint's call path and write its sequence diagram into docs/endpoints/
argument-hint: "<METHOD> <path>, e.g. POST /api/orders/{id}/lines"
---

Requested: `$ARGUMENTS`

## Before anything

This command renders through the `archify` skill, which is not a plugin and so cannot be
declared as one. If the `archify` skill is not in this session's skill list, stop and say:

```
npx skills add tt-a1i/archify -g
```

Do not fall back to Mermaid alone. A command that quietly does half its job is how the
atlas ends up with two kinds of file nobody can tell apart.

## Trace

Dispatch the `codebase-explorer` agent. Give it the method and path and ask for exactly
this shape back, nothing else:

- **Participants** in call order, each tagged with one layer: `adapter-in`, `application`,
  `domain`, `port`, `adapter-out`, `external`.
- **Messages** in call order: `from → to : what`, each with the `file:line` it happens on.
- **Error branches**: every domain error the call can raise, the participant that raises
  it, and the HTTP status the error kernel maps it to. Read the mapping; do not infer it
  from the exception's name.
- **Transaction boundary**: which participant opens it and which closes it.
- **Events and other contexts**: events published, and any other context reached through
  its published, query or command package.

Tell it the call ends where the code leaves this process — the database, a Feign client,
a broker. What happens inside those is not this endpoint's flow.

## Write

The file name is the method and the path with its leading `/` dropped, each `/` turned
into `-` and braces removed: `POST /api/orders/{id}/lines` → `POST-api-orders-id-lines`.
The folder is the context that owns the controller.

**`docs/endpoints/<context>/<name>.md`** — the primary file, because GitHub and Obsidian
both render Mermaid and neither renders the HTML:

````
---
endpoint: POST /api/orders/{id}/lines
context: ordering
traced_at: <output of git rev-parse HEAD>
tickets: [ORDERING-12]
---

# POST /api/orders/{id}/lines

```mermaid
sequenceDiagram
    participant C as OrderController
    ...
    alt OrderClosed
        D-->>C: OrderClosed → 409
    end
```

| Step | Where |
|---|---|
| OrderController → AddLine | `src/main/java/.../OrderController.java:41` |
````

Each error branch is an `alt` block naming the error and its status. Mark the transaction
with a `rect` around the messages inside it. `tickets` keeps the ids already in the file
when re-tracing and appends the current one — it is the endpoint's history, not its
latest change.

**`docs/endpoints/<context>/<name>.html`** — invoke the `archify` skill with the same
trace as a sequence diagram, and write its output here. The skill owns its own IR; hand
it the trace and let it validate. If it cannot express an error branch as a branch,
it goes in as a note — the Markdown file keeps the real `alt`.

**`docs/endpoints/README.md`** — one heading per context, one line per endpoint linking
its `.md`. Create it if it is missing; keep it sorted by context, then path.

Re-tracing overwrites both files. They are derived; the history is in git.

## Report

The file paths written, and anything the trace could not settle — a branch the explorer
could not follow, a status it could not find in the mapping. Those are worth a look before
the diagram is believed.
`````

- [ ] **Step 2: Run the checker and watch it fail**

Run: `./scripts/verify-plugin.sh`
Expected: `FAIL` with a line containing ``refers to `archify` skill/agent, which this plugin does not define``.

- [ ] **Step 3: Add the allowance**

In `scripts/verify-plugin.sh`, directly above `known = skills | agents`, add:

```python
    # A few dependencies are skills installed with `npx skills`, not plugins, so they
    # have no `plugin:` prefix to qualify them with. Each is named here with its install
    # line rather than accepted as any bare name, so a typo still fails.
    NON_PLUGIN_SKILLS = {
        "archify": "npx skills add tt-a1i/archify -g",
    }
```

Change the bare-name branch from:

```python
                elif ref not in known:
```

to:

```python
                elif ref in NON_PLUGIN_SKILLS:
                    external.add(f"{ref} ({NON_PLUGIN_SKILLS[ref]})")
                elif ref not in known:
```

- [ ] **Step 4: Run the checker and watch it pass**

Run: `./scripts/verify-plugin.sh`
Expected: ends `all plugins are well formed`; the `ddd-workflow` block lists `commands: … trace-endpoint …` and `external:` includes `archify (npx skills add tt-a1i/archify -g)`.

- [ ] **Step 5: Prove a typo still fails**

Temporarily change one `` `archify` skill `` in `trace-endpoint.md` to `` `archfy` skill ``, run `./scripts/verify-plugin.sh`, expect `FAIL` naming `archfy`, then revert.

- [ ] **Step 6: Commit**

```bash
git add plugins/ddd-workflow/commands/trace-endpoint.md scripts/verify-plugin.sh
git commit -m "ddd-workflow: /trace-endpoint writes an endpoint's call flow into docs/endpoints"
```

---

### Task 2: The atlas is written at `done` and checked for staleness at `onboard`

**Files:**
- Modify: `plugins/ddd-workflow/ticket-steps/done.md` (new step 6 after the ADR step; renumber the current 6 to 7)
- Modify: `plugins/ddd-workflow/commands/onboard.md` (`## Refresh what has drifted` list)

**Interfaces:**
- Consumes: `/trace-endpoint` and the `docs/endpoints/` layout from Task 1.

- [ ] **Step 1: Add the step to `done.md`**

Insert after step 5 (the ADR step), and renumber the "Ask whether this ticket taught…" step to 7:

```markdown
6. Bring the endpoint atlas up to date. This runs here rather than at `review` because
   only merged code is worth a diagram — a branch's call flow can still change under
   review, and a diagram of a flow that never landed misleads everyone who finds it.

   Find the endpoints the ticket touched: controllers changed in the merged diff, plus
   controllers in the same context whose call path reaches a class the diff changed.
   Run `/trace-endpoint` on each, passing this ticket's id so it lands in `tickets`.
   For an endpoint the ticket removed, delete its `.md` and `.html` and its line in
   `docs/endpoints/README.md`.

   A frontend-only ticket usually touches no endpoint. Say so and move on rather than
   tracing something to show the step ran.

   All of it goes in the same branch and PR as `status: done`.
```

- [ ] **Step 2: Add the staleness check to `onboard.md`**

Append to the bullet list under `## Refresh what has drifted`:

```markdown
- `docs/endpoints/` — a diagram is traced at `done`, so a change made outside a ticket
  leaves it describing code that has moved. For each `.md`, run
  `git log --oneline <traced_at>..HEAD -- <files in its evidence table>`. List every
  diagram with output, and offer to run `/trace-endpoint` on them. Report; do not
  re-trace unasked — a dozen re-traces is a cost the human should choose.
```

- [ ] **Step 3: Run the checker**

Run: `./scripts/verify-plugin.sh`
Expected: `all plugins are well formed`.

- [ ] **Step 4: Commit**

```bash
git add plugins/ddd-workflow/ticket-steps/done.md plugins/ddd-workflow/commands/onboard.md
git commit -m "ddd-workflow: done traces touched endpoints; onboard reports stale diagrams"
```

---

### Task 3: Impeccable detector gate in the template

**Files:**
- Modify: `templates/spring-ddd/frontend/package.json` (devDependencies, scripts)
- Modify: `templates/spring-ddd/frontend/package-lock.json` (via npm)
- Modify: `templates/spring-ddd/frontend/Makefile` (new `design-check`, `ci` prerequisites)
- Create: `templates/spring-ddd/frontend/.impeccable/config.json`
- Modify: `templates/spring-ddd/docs/backlog/_template.md`
- Modify: `scripts/verify-archetype.sh:49-54` (assert the config survives the archetype)

**Interfaces:**
- Produces: `make -C frontend design-check`, which Task 4's `design` step and `review` rely on running inside `make verify`.

- [ ] **Step 1: Decide what the gate scans**

```bash
cd templates/spring-ddd/frontend
npm install --save-dev --save-exact impeccable@4.1.0
npx impeccable detect --json src/ ; echo "exit=$?"
npm run build && npx impeccable detect --json dist/ ; echo "exit=$?"
```

Read both JSON outputs. Pick `src/` if it reports per-rule results for `.tsx` files (non-empty `files` or equivalent, exit 0 or 2). Pick `dist/` if `src/` scanned nothing or exited 1. Write the choice and the reason in the commit message. The steps below say `<TARGET>`: substitute `src` or `dist`.

- [ ] **Step 2: Write the failing archetype assertion**

In `scripts/verify-archetype.sh`, after the `frontend/.gitignore` line, add:

```bash
[[ -f frontend/.impeccable/config.json ]] || { echo "FAIL: frontend/.impeccable/config.json missing — the archetype dropped a dot-directory" >&2; exit 1; }
```

and change the following `echo "ok: …"` to `echo "ok: both .gitignore files, impeccable config, mvnw +x, no git-ignored file leaked"`.

Run: `./scripts/verify-archetype.sh`
Expected: FAIL on the new line (the file does not exist yet).

- [ ] **Step 3: Add the config, the script and the target**

`templates/spring-ddd/frontend/.impeccable/config.json`:

```json
{
  "detector": {
    "ignoreFiles": ["src/api/generated/**"]
  }
}
```

Generated files are overwritten on every regeneration; a finding there cannot be fixed.

In `package.json` `scripts`, add `"design-check": "impeccable detect <TARGET>"`.

In `frontend/Makefile`, add after `dup:`:

```make
design-check: ## Fail on the UI anti-patterns impeccable detects without a model
	npm run design-check
```

and change `ci:` to — for `src`: `ci: typecheck test dup design-check build ## …` (cheapest first, keep the existing comment); for `dist`: `ci: typecheck test dup build design-check ## …`.

- [ ] **Step 4: Run the gate on the template**

Run: `make -C templates/spring-ddd/frontend ci`
Expected: PASS. If `design-check` reports a finding in the worked example, fix the component — the template is the example projects copy. Add an ignore to `config.json` only for a rule that is wrong for the template, with `npx impeccable ignores add-value <rule> <value> --reason "<why>"`.

- [ ] **Step 5: Add *Design direction* to the backlog template**

In `templates/spring-ddd/docs/backlog/_template.md`, between `## Model decision`'s body and `## Glossary impact`, insert:

```markdown
## Design direction

<Frontend tickets: the UI direction from `/impeccable shape`, settled before coding
starts. Anything else: "n/a", so a reader knows it was considered.>

```

- [ ] **Step 6: Rebuild the archetype and verify**

```bash
./scripts/build-archetype.sh
./scripts/verify-archetype.sh
```

Expected: `ok: both .gitignore files, impeccable config, mvnw +x, …` and the script's remaining checks pass. If the config is missing, the archetype packaging dropped the dot-directory: handle `.impeccable` in `build-archetype.sh` the way `.gitignore` is handled (travel without the dot, rename in the post-generate script), and rerun.

- [ ] **Step 7: Commit**

```bash
git add templates/spring-ddd scripts/verify-archetype.sh scripts/build-archetype.sh
git commit -m "spring-ddd: impeccable detector gates fe-ci; tickets carry a design direction"
```

---

### Task 4: Impeccable in the ticket verbs

**Files:**
- Modify: `plugins/ddd-workflow/ticket-steps/new.md` (the ticket body block)
- Modify: `plugins/ddd-workflow/ticket-steps/refine.md` (`## What to write` and a new section)
- Modify: `plugins/ddd-workflow/ticket-steps/start.md` (refusals)
- Create: `plugins/ddd-workflow/ticket-steps/design.md`
- Modify: `plugins/ddd-workflow/ticket-steps/review.md` (step 4)
- Modify: `plugins/ddd-workflow/ticket-steps/respond.md` (new section)
- Modify: `plugins/ddd-workflow/commands/ticket.md` (argument-hint, dispatch list)

**Interfaces:**
- Consumes: `make -C frontend design-check` and the `## Design direction` section from Task 3.
- Produces: `/ticket design <ID>`.

- [ ] **Step 1: `new.md`**

In the ticket body block, between the `## Model decision` stanza and `## Glossary impact`, insert:

```markdown
## Design direction

_Not analysed yet — `/ticket refine CONTEXT-7`._

```

- [ ] **Step 2: `refine.md`**

Add a section before `## What to write`:

```markdown
## Frontend tickets

A ticket that touches `frontend/**` has a third question: what it should look like.
Settle it here for the same reason as the model — decided at the keyboard, it is decided
by whoever happens to be typing.

If `PRODUCT.md` is missing at the project root, stop and ask for `/impeccable init`
first. A design direction with no audience and no voice behind it is a guess dressed as
a decision.

Otherwise invoke the `impeccable:impeccable` skill with `shape` and write what it settles
into *Design direction*. For a ticket that does not touch the frontend, write `n/a`.
```

and in `## What to write`, change `Fill *Acceptance criteria*, *Model decision* and *Glossary impact*` to `Fill *Acceptance criteria*, *Model decision*, *Design direction* and *Glossary impact*`.

- [ ] **Step 3: `start.md`**

After the paragraph refusing an empty *Model decision*, add:

```markdown
Refuse a ticket touching `frontend/**` whose *Design direction* is still the unanalysed
marker, for the same reason.
```

In step 3's sentence after the Delegation table reference, add for the frontend row: tell the `frontend` agent to build against *Design direction*. Concretely, append to step 3:

```markdown
   Hand the `frontend` agent the ticket's *Design direction* along with its criteria.
```

- [ ] **Step 4: Create `design.md`**

```markdown
# design

Iterate on a frontend ticket's UI with the human until they call it done. This is the one
verb that never decides for itself when it is finished: taste is the judgement nothing
else in this workflow can make, and a loop that stops on its own is making it.

Refuse a ticket that is not `in-progress`, or that does not touch `frontend/**`. Status
does not change here; this sits between `start` and `review`.

## Setup

Start `make run` and `make -C frontend dev` in the background. Work out the route the
ticket changes from its criteria and the diff; ask only if neither says.

## One round

1. `npx impeccable detect --json http://localhost:5173/<route>`. Fix every finding
   straight away and say what you fixed. A detector hit is a rule, not an opinion, so it
   is not put to the human.
2. Screenshot the route through `claude-in-chrome`.
3. Invoke the `impeccable:impeccable` skill with `critique`.
4. Show the human the screenshot and the critique together, and offer the named moves the
   critique points at — `quieter`, `bolder`, `polish`, `distill`, `typeset`, `layout`,
   `colorize`, `animate` — with a recommendation. They pick one, or say something in
   their own words.
5. Apply it: a named move through the `impeccable:impeccable` skill, free-form feedback
   by hand. Run `make fe-check` before the next round; a design change that breaks a test
   is not a design change yet.

Repeat until the human says it is done. Show one round at a time; a batch of changes
nobody saw separately is a design nobody chose.

## Before handing over

If the direction itself moved — not a tweak, a different answer to what the screen is
for — update *Design direction* and add one line to *Notes* saying what changed and why.
That section is what `review` and the next ticket read.

Commit the work. Then `/ticket review`.
```

- [ ] **Step 5: `review.md`**

After step 4's first paragraph (the one ending "collapsing them buries the modelling findings in style noise."), add:

```markdown
   For a diff touching `frontend/**`, add a third: invoke the `impeccable:impeccable`
   skill with `audit`, scoped to the changed frontend files. Design quality is its own
   axis and neither of the other two reads for it.
```

- [ ] **Step 6: `respond.md`**

Add a section at the end, before any `## Vikunja` section if one exists:

```markdown
## Design feedback

On a frontend ticket, translate a design comment into one of impeccable's named moves
before acting on it — "too loud" is `quieter`, "feels generic" is `bolder`, "cluttered" is
`distill` — and apply it through the `impeccable:impeccable` skill. Name the move in the
reply. A named move is something the reviewer can ask for again and recognise when they
see it; a one-off tweak is neither. Feedback no move fits is applied as written.
```

- [ ] **Step 7: `ticket.md`**

Change the `argument-hint` to:

```
argument-hint: "[new <description> | refine <ID> | start <ID> | design <ID> | review <ID> | respond <ID> | done <ID>] (no args: show the board)"
```

and the dispatch sentence to `one of \`new\`, \`refine\`, \`start\`, \`design\`, \`review\`, \`respond\`, \`done\``.

- [ ] **Step 8: Run the checker**

Run: `./scripts/verify-plugin.sh`
Expected: `all plugins are well formed`; `ticket steps:` lists `design`; `external:` lists `impeccable:impeccable`.

- [ ] **Step 9: Commit**

```bash
git add plugins/ddd-workflow
git commit -m "ddd-workflow: frontend tickets get a design direction and a /ticket design loop"
```

---

### Task 5: Docs and version

**Files:**
- Modify: `README.md` (`### Commands`, a new dependencies note)
- Modify: `HOWTO.md` (`## 2. One-time, per machine`, `## 5. The daily loop`)
- Modify: `plugins/ddd-workflow/.claude-plugin/plugin.json` (`version`)

- [ ] **Step 1: README**

Under `### Commands`, add:

```markdown
- `/trace-endpoint` — trace one endpoint from controller to adapter and write its sequence
  diagram to `docs/endpoints/`: Mermaid in Markdown for GitHub and Obsidian, and an
  interactive archify HTML beside it. `/ticket done` runs it on every endpoint the ticket
  touched, so the atlas grows with the work; `/onboard` reports diagrams whose code has
  moved since.
```

and extend the `/ticket` bullet's verb list with `design`, adding one sentence: `` `design` is the frontend loop between `start` and `review`: screenshot, impeccable critique, a named move you pick, repeat until you call it done. ``

After the "Depending on one is fine; depending silently is not." paragraph, add:

```markdown
Two dependencies are new with the design loop and the atlas. Impeccable is a plugin and
is declared like the others: `/plugin marketplace add pbakaus/impeccable`. Archify is a
skill, not a plugin — `npx skills add tt-a1i/archify -g` — so `verify-plugin.sh` names it
in an explicit allow-list, and `/trace-endpoint` checks for it and stops with the install
line when it is missing.
```

- [ ] **Step 2: HOWTO**

In `## 2. One-time, per machine`, add the two install lines above. In `## 5. The daily loop`'s command block, add after `start`:

```
/ticket design BILLING-14   # frontend only: critique, pick a move, repeat until done
```

and after `/onboard`:

```
/trace-endpoint POST /api/orders   # one endpoint's call flow into docs/endpoints/
```

Add a paragraph after the `respond` paragraphs:

```markdown
`design` is the frontend's loop and the only verb that never decides it is finished. Each
round fixes what impeccable's detector flags, then shows you a screenshot with a critique
and asks you to pick a move. The direction it builds toward was settled at `refine`, from
`PRODUCT.md` — run `/impeccable init` once per project to write that.

`done` also writes the endpoint atlas: every endpoint the ticket touched gets its sequence
diagram re-traced into `docs/endpoints/`, from the merged code. Open that folder in the
same vault as the backlog.
```

- [ ] **Step 3: Version bump**

In `plugins/ddd-workflow/.claude-plugin/plugin.json`, change `"version": "1.6.5"` to `"version": "1.7.0"`.

- [ ] **Step 4: Run every check**

```bash
./scripts/verify-plugin.sh
./scripts/check-plugin-version-bump.sh main
./scripts/verify-archetype.sh
make -C templates/spring-ddd verify
```

Expected: all pass. `make verify` boots the application for the schema capture; if it fails there and `make ci` did not, read `.github/workflows/ci.yml` before assuming a defect.

- [ ] **Step 5: Commit**

```bash
git add README.md HOWTO.md plugins/ddd-workflow/.claude-plugin/plugin.json
git commit -m "ddd-workflow 1.7.0: document the design loop and the endpoint atlas"
```
