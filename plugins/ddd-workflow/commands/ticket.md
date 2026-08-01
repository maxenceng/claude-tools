---
description: Work a backlog ticket end to end — create it, start it, review it, close it
argument-hint: "[new <description> | start <ID> | review <ID> | done <ID>] (no args: show the board)"
---

Tickets live in `docs/backlog/` as markdown with YAML frontmatter. Read that folder's
`README.md` for the naming and field conventions before writing to it.

Requested: `$ARGUMENTS`

If no arguments were given, list every ticket that is not `done`, grouped by status, with
id, title and context. Say which one is in progress. Stop there.

Otherwise dispatch on the first word.

## new

Write a ticket from `_template.md`. Do not invent detail the request does not contain —
an acceptance criterion nobody asked for is a requirement nobody agreed to.

Two things must be settled before the file is worth saving, and both are modelling
questions rather than clerical ones:

**Which context.** The `context:` field is the first thing backend work needs. If the
work does not fit one, say so — that is usually two tickets, or a context that does not
exist yet.

**Where the behaviour belongs.** Fill in *Model decision*: new behaviour on an existing
aggregate, a new aggregate, or a new context. If it is a new context, stop and raise it;
that is larger than a ticket.

Use the brainstorming skill if the request is vague. A ticket written from an ambiguous
sentence looks precise and misleads everyone who reads it afterwards.

Number it by taking the highest existing `<CONTEXT>-<n>` and adding one. Set `status:
todo` and `created:` to today's absolute date.

## start

Refuse to start a ticket whose *Model decision* is empty, and say why. That section is
what separates a ticket from a wish, and filling it in afterwards means it was really
decided at the keyboard.

Then:

1. Set `status: in-progress`.
2. Create a branch named `<id>-<slug>`, matching the filename. Use a worktree if the
   current one has uncommitted work worth keeping.
3. Invoke the `ddd-backend` skill and implement test-first, domain outwards. Run
   `make test` as you go — the architecture rules fail on a misplaced class immediately,
   which is cheaper than finding it in review.
4. Write the boundary case first where the ticket has one. A rule tested only in the
   middle of its range passes with an off-by-one in it.
5. If the API surface changed, recapture the schema: `make run`, `make openapi`,
   `make openapi-client`. Running only the last regenerates types from a stale schema.
6. Apply the *Glossary impact* to `docs/glossary.md` in this change, not later.

## review

1. Set `status: in-review`.
2. Run `make ci`, and `make fe-check` if the frontend changed. Report what actually
   passed — not what should pass.
3. Dispatch `architecture-reviewer` for the modelling: does the behaviour sit where the
   ticket said it would, and does the language hold?
4. Then run a general code review for correctness. These are deliberately separate
   reviewers with separate jobs; do not collapse them.
5. Push and open a PR whose body links the ticket file and lists the acceptance criteria
   with their outcomes.

Tick an acceptance criterion only once something demonstrates it. An unticked box is
information; a ticked one that nothing verifies is a lie the next reader will act on.

## done

1. Confirm the work is merged. If it is not, say so and stop.
2. Set `status: done`.
3. Fill in *Notes* with anything the code will not show — an approach rejected, a
   constraint found. Skip it if there is genuinely nothing; padding trains people to stop
   reading the section.
4. Run the `project-retro` skill if anything during the ticket was done by hand more than
   twice, or if the same correction came up repeatedly.
5. Raise an ADR if a decision was made that someone could reasonably reverse later
   without knowing why it was taken.

## Throughout

Edit only the frontmatter field that the step owns. Rewriting a whole ticket file to
change one status loses whatever a human wrote in it, and the human's words are the part
worth keeping.
