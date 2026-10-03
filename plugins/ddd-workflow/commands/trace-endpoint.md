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
with a `rect` around the messages inside it. `tickets` is the endpoint's history, not its
latest change: when a ticket id is given, append it to the ids already in the file (a new
file starts from an empty list); when none is given, keep `tickets` as it was.

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
