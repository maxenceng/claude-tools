---
description: Work a ticket end to end — capture it, refine it, start it, review it, close it
argument-hint: "[new <description> | refine <number> | start <number> | design <number> | review <number> | respond <number> | done <number>] (no args: show the board)"
---

A ticket is a GitHub issue, named by its number. Its status, context and type are labels
(`status:todo`, `context:<name>`, `type:feature`), its body is the ticket's `##` sections, and the
merged pull request's `Closes #<n>` closes it. A ticket is not a file in the repository.

Every step reaches GitHub through one script and no other way:
`${CLAUDE_PLUGIN_ROOT}/scripts/ticket-tracker <verb>`, called `ticket-tracker` below. It prints JSON,
reads a ticket by one set of readability rules, and refuses with a reason when it cannot. Do not
write a `gh` call in its place, and do not work around a refusal: when it says a ticket is
unreadable, say why and stop. Without the network every verb refuses with that reason and writes
nothing; say so and stop rather than working from memory.

Requested: `$ARGUMENTS`

If no arguments were given, run `ticket-tracker board` and list every open ticket, grouped by status,
with number, title and context. Say which one is in progress, say plainly that anything in `draft`
cannot be started until it has been through `refine`, and list any ticket under `unreadable` with its
reason. Stop there.

Otherwise dispatch on the first word — one of `new`, `refine`, `start`, `design`, `review`,
`respond`, `done` — by reading `${CLAUDE_PLUGIN_ROOT}/ticket-steps/<word>.md` and following
it. Read that one file and no others: the steps do not share instructions at runtime, and
loading the six that are not running is most of what this command used to cost.

A ticket is captured cheaply and analysed later. `new` writes down what someone said and
asks almost nothing; `refine` is where the questions, the modelling and the acceptance
criteria happen. Keeping them apart is what lets a whole backlog be written in one sitting
without deciding six designs at the same time.

Where a step names an agent or a skill, invoking it *is* the step — it is not done until
that agent has reported back.

## Throughout

Each verb is a session boundary, and starting one in a fresh session is the cheaper default.
The issue carries the criteria and the model decision, the ADRs carry the reasoning, the
PR carries the review — so a new session begins this command knowing everything it needs,
while a continuing one drags every earlier verb's transcript into every tool call it makes.
Stay in the same session while a verb is unfinished, and while a dispatched agent still has to
report back: its result arrives in the session that dispatched it and nowhere else.

Write only the section the step owns. `ticket-tracker write-sections` replaces the named `##`
sections and nothing else, and refuses if the issue changed since you read it
(`--expect-updated-at` is the `updatedAt` that `show` returned). A refusal there means a human
edited the issue meanwhile: read it again and reconcile, never retry blindly. The human's words
are the part worth keeping.

A commit subject says the change in words and carries no ticket id; the pull request body carries
`Closes #<n>`. Outside the record (`docs/adr/`, `docs/research/`, `docs/endpoints/`, `scripts/`)
no file names an issue, so code and living documents say what the behaviour is instead.

**Asking.** Put a question to the human through the `AskUserQuestion` tool, not as prose,
whenever its answers can be named in advance: two to four options, your recommendation first
with `(Recommended)` at the end of its label, each option's trade-off in its description. The
dialog may hide everything written before it, so each question carries the context it depends
on. Up to four independent questions go in one call; a round with more takes several calls.
The human can always answer in their own words, so never add an "Other" option. A question
with no options worth naming — describe the destination, what is wrong with it — stays prose.

## The verbs of `ticket-tracker`

`board`, `show <n>`, `create`, `label <n>`, `move <n> <status>`, `write-sections <n>`,
`ready <n> <refine|start|design>`, `develop <n>`, `pr-create`, `pr-feedback <n>`,
`pr-reply <n> <id>`, `pr-write-sections <n>`, `done <n>`, `close <n>`, `frontier <map>`, `add-sub-issue`, `add-blocker`,
`notes`. Each step names the ones it uses; `ticket-tracker --help` and `<verb> --help` list the
rest.
