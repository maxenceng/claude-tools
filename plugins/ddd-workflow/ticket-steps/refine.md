# refine

Turn a captured draft into a ticket someone can start. This is where the questions live.

Refuse anything whose status is not `draft`, and say what it is instead. A ticket already
in `todo` has been analysed and possibly argued over; re-running this would quietly
overwrite that with a fresh opinion. If it genuinely needs rethinking, that is a human
saying so, not a status this step infers.

Two things must be settled before the file is worth saving, and both are modelling
questions rather than clerical ones:

**Which context.** `new` guessed it from the words available, or left it `unassigned`.
Confirm it or correct it now — this is the last cheap moment to move a ticket, because the
id is in the filename and the branch name after this.

**Where the behaviour belongs.** Fill in *Model decision*: new behaviour on an existing
aggregate, a new aggregate, or a new context. If it is a new context, stop and raise it;
that is larger than a ticket.

Invoke the `superpowers:brainstorming` skill unless the captured line already answers both
questions above. A ticket written from an ambiguous sentence looks precise and misleads
everyone who reads it afterwards.

Use it for the questioning only. Brainstorming's own checklist ends by writing a spec to
`docs/superpowers/specs/` and going on to `writing-plans`; here it stops once the two
questions are answered and the ticket is filled in. The ticket is this project's design
record, and a spec beside it is a second description of the same decision that nothing
keeps in step.

Dispatch `codebase-explorer` first when the work touches code not already read this
session. Its written summary is what keeps forty files out of this conversation.

## What to write

Fill *Acceptance criteria*, *Model decision* and *Glossary impact*, replacing the
_not analysed yet_ markers. Then set `status: todo`.

Do not invent detail the request does not contain — an acceptance criterion nobody asked
for is a requirement nobody agreed to. What a draft says is the whole of what was asked;
everything else in the ticket has to come from an answer someone actually gave during the
questioning.

Write the criterion that fails, not only the one that passes. Every rule has a case that
breaks it and that is the one that gets forgotten.

Leave the title alone unless the questioning changed what the ticket is about. It is the
sentence someone actually said, and quietly improving it loses the only unmediated record
of the request.

Refine one ticket per invocation. A batch of drafts is exactly the situation where
answering six sets of questions at once produces six designs nobody separately agreed to.
