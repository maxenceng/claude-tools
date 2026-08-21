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
