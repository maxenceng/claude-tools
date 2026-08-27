---
description: Work a backlog ticket end to end — capture it, refine it, start it, review it, close it
argument-hint: "[new <description> | refine <ID> | start <ID> | review <ID> | respond <ID> | done <ID>] (no args: show the board)"
---

Tickets live in `docs/backlog/` as markdown with YAML frontmatter. Read that folder's
`README.md` for the naming and field conventions before writing to it.

Requested: `$ARGUMENTS`

If no arguments were given, list every ticket that is not `done`, grouped by status, with
id, title and context. Say which one is in progress, and say plainly that anything in
`draft` cannot be started until it has been through `refine`. Stop there.

Otherwise dispatch on the first word — one of `new`, `refine`, `start`, `review`,
`respond`, `done` — by reading `${CLAUDE_PLUGIN_ROOT}/ticket-steps/<word>.md` and following
it. Read that one file and no others: the steps do not share instructions at runtime, and
loading the five that are not running is most of what this command used to cost.

A ticket is captured cheaply and analysed later. `new` writes down what someone said and
asks almost nothing; `refine` is where the questions, the modelling and the acceptance
criteria happen. Keeping them apart is what lets a whole backlog be written in one sitting
without deciding six designs at the same time.

Where a step names an agent or a skill, invoking it *is* the step — it is not done until
that agent has reported back.

## Throughout

Each verb is a session boundary, and starting one in a fresh session is the cheaper default.
The ticket file carries the criteria and the model decision, the ADRs carry the reasoning, the
PR carries the review — so a new session begins this command knowing everything it needs,
while a continuing one drags every earlier verb's transcript into every tool call it makes.
Stay in the same session while a verb is unfinished, and while a dispatched agent still has to
report back: its result arrives in the session that dispatched it and nowhere else.

Edit only the frontmatter field that the step owns. Rewriting a whole ticket file to
change one status loses whatever a human wrote in it, and the human's words are the part
worth keeping.

## Vikunja

Frontmatter may carry `tracker_id:` once a ticket has been pushed to Vikunja — set by
whichever step first pushes it, read by every step after. `VIKUNJA_URL`, `VIKUNJA_TOKEN`
and `VIKUNJA_PROJECT_ID` come from the invoking shell's environment, never from a file in
this repo; where any of them is unset, every step that mentions Vikunja below proceeds on
the markdown alone and says so once, rather than failing over a tracker nobody opted into.

Moving a task to a bucket takes two lookups first, both by name rather than a hardcoded
id — the view and the bucket ids are Vikunja's to assign, not this command's to remember:

```bash
VIEW_ID=$(curl -sf "$VIKUNJA_URL/api/v1/projects/$VIKUNJA_PROJECT_ID/views" \
  -H "Authorization: Bearer $VIKUNJA_TOKEN" | jq '.[] | select(.view_kind=="kanban") | .id')

BUCKET_ID=$(curl -sf "$VIKUNJA_URL/api/v1/projects/$VIKUNJA_PROJECT_ID/views/$VIEW_ID/buckets" \
  -H "Authorization: Bearer $VIKUNJA_TOKEN" | jq --arg t "<bucket title>" '.[] | select(.title==$t) | .id')

curl -sf -X POST "$VIKUNJA_URL/api/v1/projects/$VIKUNJA_PROJECT_ID/views/$VIEW_ID/buckets/$BUCKET_ID/tasks" \
  -H "Authorization: Bearer $VIKUNJA_TOKEN" -H "Content-Type: application/json" \
  -d "{\"task_id\": $TRACKER_ID}"
```

This is the shape of it, not a script to run unread — substitute `jq` for whatever JSON
handling is available, and re-check the paths against `$VIKUNJA_URL/api/v1/docs` if this
instance's version has moved on from what these were written against.

Five buckets must exist on the project's Kanban view ahead of time, titled exactly
`draft`, `todo`, `in-progress`, `in-review`, `done`, with `done` set as that view's
done-bucket — moving a task in also marks it done. Set this up once, by hand, when the
Vikunja project is created; this command does not create buckets.

The no-argument board listing above never calls Vikunja: it reads `docs/backlog/`
directly, exactly as before this section existed.
