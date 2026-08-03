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

## Delegation

Steps below name an agent or a skill. Where one is named, invoking it *is* the step: a
step that says dispatch is not done until that agent has reported back.

Choose the implementation agent from what the change touches, not from what it is about:

| The change touches | Agent |
|---|---|
| `src/**` inside a bounded context | `backend-ddd` |
| `frontend/**` | `frontend` |
| `Makefile`, `compose.yaml`, `Dockerfile`, `.github/**`, `scripts/**`, or the build itself | `devops` |

A ticket touching two of those rows is two dispatches in dependency order, not one agent
working outside its brief.

Stay inline when the step edits the ticket's own frontmatter, or when the whole change is
a file already read this session. Dispatching costs a cold start and a re-read of context
the session already holds. Agents are named here because fresh eyes at review and
role-specific judgement at implementation are worth that cost — not because delegation is
better by default.

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

Invoke the `brainstorming` skill unless the request already answers both questions above.
A ticket written from an ambiguous sentence looks precise and misleads everyone who reads
it afterwards.

Use it for the questioning only. Brainstorming's own checklist ends by writing a spec to
`docs/superpowers/specs/` and going on to `writing-plans`; here it stops once the two
questions are answered and the ticket is written. The ticket is this project's design
record, and a spec beside it is a second description of the same decision that nothing
keeps in step.

Dispatch `codebase-explorer` first when the work touches code not already read this
session. Its written summary is what keeps forty files out of this conversation.

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
3. Dispatch the agent for what the ticket touches, from the Delegation table above, and
   tell it to work test-first, domain outwards, running `make test` as it goes — the
   architecture rules fail on a misplaced class immediately, which is cheaper than
   finding it in review. `backend-ddd` loads the `ddd-backend` skill itself; invoke that
   skill directly only when the work is small enough to stay inline.
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
   ticket said it would, and does the language hold? Hand it the ticket's *Model
   decision* and the diff, so it reviews against what was decided rather than against
   taste.
4. Then run a general code review for correctness — `/code-review`, or the
   `pr-review-toolkit` reviewers. This plugin ships no general reviewer on purpose. They
   are separate reviewers with separate jobs; collapsing them buries the modelling
   findings in style noise.
5. Push and open a PR whose body links the ticket file and lists the acceptance criteria
   with their outcomes.

Invoke the `verification-before-completion` skill before ticking anything or reporting
that a step passed.

Tick an acceptance criterion only once something demonstrates it. An unticked box is
information; a ticked one that nothing verifies is a lie the next reader will act on.

## done

1. Confirm the work is merged. If it is not, say so and stop.
2. Set `status: done`.
3. Fill in *Notes* with anything the code will not show — an approach rejected, a
   constraint found. Skip it if there is genuinely nothing; padding trains people to stop
   reading the section.
4. Invoke the `project-retro` skill if anything during the ticket was done by hand more
   than twice, or if the same correction came up repeatedly.
5. Raise an ADR if a decision was made that someone could reasonably reverse later
   without knowing why it was taken.

## Throughout

Edit only the frontmatter field that the step owns. Rewriting a whole ticket file to
change one status loses whatever a human wrote in it, and the human's words are the part
worth keeping.
