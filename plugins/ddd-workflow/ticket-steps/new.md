# new

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

Invoke the `superpowers:brainstorming` skill unless the request already answers both
questions above.
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
