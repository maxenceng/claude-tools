# refine

Turn a captured draft into a ticket someone can start. This is where the questions live.

`ticket-tracker` below is `${CLAUDE_PLUGIN_ROOT}/scripts/ticket-tracker`; it is the only way to
reach GitHub.

Run `ticket-tracker ready <n> refine` first. It refuses anything whose status is not `draft`, and
says what it is instead. A ticket already in `todo` has been analysed and possibly argued over;
re-running this would quietly overwrite that with a fresh opinion. If it genuinely needs rethinking,
that is a human saying so, not a status this step infers. Then `ticket-tracker show <n>`: its
`updatedAt` is what the write below must quote.

Two things must be settled before the file is worth saving, and both are modelling
questions rather than clerical ones:

**Which context.** `new` guessed it from the words available, or left it off. Confirm it or
correct it now. The ticket's id is its issue number and does not depend on the context, so a wrong
guess is cheap to fix here and later alike; `ticket-tracker label <n> --context <name>` sets it, and
refuses a context `docs/context-map.md` does not name (`cross-context` excepted, which is deliberately
awkward to write: a ticket that spans contexts is a modelling event).

**Where the behaviour belongs.** Fill in *Model decision*: new behaviour on an existing
aggregate, a new aggregate, or a new context. If it is a new context, stop and raise it;
that is larger than a ticket.

Question the human unless the captured line already answers both questions above. A
ticket written from an ambiguous sentence looks precise and misleads everyone who reads it
afterwards.

Ask in rounds. A round is every question you can ask now without guessing at an answer
not yet given, asked through `AskUserQuestion` (see *Asking* in `/ticket`), each with the
options and your recommendation. List the whole option space, including the conventional
middle a competent engineer would reach for first; where you exclude one, or it does not
fit in the tool's four, say why in the question text rather than leave it off. A question
that depends on another one still open belongs to the next round, not this one: answered
together, the first answer would have changed the second question. Wait for the answers,
then ask whatever they unblocked.

Facts are yours to find, not the human's to supply. Look them up in the glossary and the
ADRs, or dispatch `codebase-explorer` for the code — and do not hold the round for it:
ask the questions that do not depend on what it will find while it runs.

Stop when nothing the sections below need is still assumed rather than answered. Play
back the context, the model decision and the criteria in a few lines and get a yes
before writing them; a ticket the human has not seen summarised is one they will
discover they disagree with at `review`.

The ticket is this project's design record. Write no spec or plan beside it — a second
description of the same decision is one that nothing keeps in step.

Dispatch `codebase-explorer` first when the work touches code not already read this
session. Its written summary is what keeps forty files out of this conversation.

## Frontend tickets

A ticket that touches `frontend/**` has a third question: what it should look like.
Settle it here for the same reason as the model — decided at the keyboard, it is decided
by whoever happens to be typing.

If `PRODUCT.md` is missing at the project root, stop and ask for `/impeccable init`
first. A design direction with no audience and no voice behind it is a guess dressed as
a decision.

Otherwise invoke the `impeccable:impeccable` skill with `shape` and write what it settles
into *Design direction*. For a ticket that does not touch the frontend, write `n/a`.

A screen someone works in — a list, a table, a form, a dashboard — also gets three lines
there, because `shape` leaves them implicit and the build then falls back on the stock
order of figures, chart, table:

- **The question** the screen answers first, in one line ("which deploy broke?"). Its
  biggest block answers it; a block that answers no question is left out.
- **The finding**: the fact in the data that most needs attention, and where it is read
  first — the line under the title, or beside the action it drives.
- **The job** done most often on it, and the control one click away that does it.

## What to write

Fill *Acceptance criteria*, *Model decision*, *Design direction* and *Glossary impact*, replacing the
_not analysed yet_ markers, in one call: a JSON object of section name to text on stdin of
`ticket-tracker write-sections <n> --expect-updated-at <updatedAt>`. It replaces those sections and
nothing else, and refuses, changing nothing, if the issue moved since you read it. Make sure the
ticket has its `type:` label (`ticket-tracker label <n> --type <type>`; `new` defaulted it to
`feature`) and its `context:` label, then `ticket-tracker move <n> todo`. A `todo` without both is
unreadable, so the move refuses it.

Do not invent detail the request does not contain — an acceptance criterion nobody asked
for is a requirement nobody agreed to. What a draft says is the whole of what was asked;
everything else in the ticket has to come from an answer someone actually gave during the
questioning.

Write the criterion that fails, not only the one that passes. Every rule has a case that
breaks it and that is the one that gets forgotten.

That is not licence to invent one. A criterion guarding against malformed or out-of-range
*external* data — a vendor field outside its documented scale, a response shape nobody has
seen — needs the same evidence a bug report would: has this integration actually been
observed to send it? Check this project's git history and ADRs before writing the
criterion, not after a review round questions it. Where a domain type already refuses the
value on its own (a bounded value object's constructor), failing loud through that refusal
is itself a valid answer, and does not need a silent-skip guard invented in front of it —
an unobserved case is not the same finding as an observed one, even when a genuinely
observed sibling case nearby makes the invented one look like it belongs beside it.

The same evidence question runs the other way on an audit ticket — one whose criteria
decide the fate of guards that already exist, rather than proposing new ones. "No evidence
this happens" is the trigger for asking whether each one earns its keep, not a rule that
every unevidenced guard found gets a "removed" criterion: one whose own effect already
fails loud, or one guarding data the domain already treats as optional, can be evidence-free
and still correct to keep. `ddd-backend`'s *Frequent mistakes* has the carve-outs; write the
criterion — remove, or keep with the reasoning going to an ADR — per guard, not by template.

Leave the title alone unless the questioning changed what the ticket is about. It is the
sentence someone actually said, and quietly improving it loses the only unmediated record
of the request.

Refine one ticket per invocation. A batch of drafts is exactly the situation where
answering six sets of questions at once produces six designs nobody separately agreed to.
