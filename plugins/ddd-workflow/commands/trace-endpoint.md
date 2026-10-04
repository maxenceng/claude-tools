---
description: Trace one endpoint's call path and write its sequence diagram into docs/endpoints/
argument-hint: "<METHOD> <path> [ticket-id], e.g. POST /api/orders/{id}/lines ORDERING-12"
---

Requested: `$ARGUMENTS`

## Before anything

This command renders through the `archify` skill, which is not a plugin and so cannot be
declared as one. If the `archify` skill is not in this session's skill list, stop and say:

```
npx skills add tt-a1i/archify -g
bash ${CLAUDE_PLUGIN_ROOT}/scripts/archify-chrome.sh
```

The second line installs the Chromium that archify's browser gate runs in.

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
traced_at: <output of git rev-parse origin/main>
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
| OrderController → AddLine | `src/main/java/com/acme/ordering/adapter/in/web/OrderController.java:41` |
````

`traced_at` is `git rev-parse origin/main` after a `git fetch origin`, falling back to
`HEAD` only when there is no `origin`: a branch commit can vanish on squash-merge, and
`onboard` needs a sha that still resolves. Write every path in the table as a full
repo-relative path, never abbreviated with `...`, since `onboard` feeds them to `git log`.

Each error branch is an `alt` block naming the error and its status. Mark the transaction
with a `rect` around the messages inside it. `tickets` is the endpoint's history, not its
latest change: when a ticket id is given, append it to the ids already in the file (a new
file starts from an empty list); when none is given, keep `tickets` as it was.

**`docs/endpoints/<context>/<name>.html`** — invoke the `archify` skill with the same
trace as a sequence diagram, and write its output here. The skill owns its own IR; hand
it the trace and let it validate. If it cannot express an error branch as a branch,
it goes in as a note — the Markdown file keeps the real `alt`.

Run every archify command with `ARCHIFY_CHROME` set to the output of
`bash ${CLAUDE_PLUGIN_ROOT}/scripts/archify-chrome.sh --path`. Without a Chrome, archify's
last gate reports `skipped` and exits 2, which is not a pass. If `--path` fails, nothing is
installed yet, so stop the same way as above.

The HTML has less room than the Markdown. archify keeps a sequence readable on a desktop
only up to about 1085px wide, and 696px tall at that width. It also needs 28px between
messages that overlap, and it has no self-messages. That fits about six participants and
twenty arrows. When the trace is bigger, shrink the HTML and leave the Markdown alone, in
this order:

1. Merge a participant into its neighbour along the call. A repository with its database
   or vendor, an application service with the manager it only delegates to, a chain inside
   another context with the adapter that calls into it. Name the merge in the sublabel, for
   example `application + domain` or `adapter-out → PostgreSQL`.
2. A call that now starts and ends on the same merged participant can't be drawn. Put it in
   the `note` of the next arrow.
3. If it still doesn't fit, error branches leave the drawing. Each becomes a note on the
   arrow that raises it, and goes in an error card.

Never widen the canvas or space the messages more tightly to get past a gate: the
readability and spacing checks fail either way. The `.md` is the full trace. The `.html` is
a view of it, and a merge is not a finding.

**`docs/endpoints/README.md`** — one heading per context, one line per endpoint linking
its `.md`. Create it if it is missing; keep it sorted by context, then path.

Re-tracing overwrites both files. They are derived; the history is in git.

## Report

The file paths written, and anything the trace could not settle — a branch the explorer
could not follow, a status it could not find in the mapping. Those are worth a look before
the diagram is believed.
