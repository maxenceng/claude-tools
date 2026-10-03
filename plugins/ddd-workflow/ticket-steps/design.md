# design

Iterate on a frontend ticket's UI with the human until they call it done. This is the one
verb that never decides for itself when it is finished: taste is the judgement nothing
else in this workflow can make, and a loop that stops on its own is making it.

Refuse a ticket that is not `in-progress`, or that does not touch `frontend/**`. Status
does not change here; this sits between `start` and `review`.

## Setup

Start `make run` and `make -C frontend dev` in the background. Work out the route the
ticket changes from its criteria and the diff; ask only if neither says.

## One round

1. `npm --prefix frontend exec -- impeccable detect --json http://localhost:5173/<route>`,
   run through the frontend so the pinned version and `frontend/.impeccable/config.json`
   apply. Fix every finding
   straight away and say what you fixed. A detector hit is a rule, not an opinion, so it
   is not put to the human.
2. Screenshot the route through `claude-in-chrome`. If it (or a local Chrome) is
   unavailable, say so and stop: a critique without a screenshot is guessing.
3. Invoke the `impeccable:impeccable` skill with `critique`.
4. Show the human the screenshot and the critique together, and offer the named moves the
   critique points at — `quieter`, `bolder`, `polish`, `distill`, `typeset`, `layout`,
   `colorize`, `animate` — with a recommendation. They pick one, or say something in
   their own words.
5. Apply it: a named move through the `impeccable:impeccable` skill, free-form feedback
   by hand. Run `make fe-check` before the next round; a design change that breaks a test
   is not a design change yet.

Repeat until the human says it is done. Show one round at a time; a batch of changes
nobody saw separately is a design nobody chose.

## Before handing over

If the direction itself moved — not a tweak, a different answer to what the screen is
for — update *Design direction* and add one line to *Notes* saying what changed and why.
That section is what `review` and the next ticket read.

Stop the background `make run` and `dev` servers once the loop ends.

Commit the work. Critique reports under `.impeccable/critique/` are not committed; the
ticket's *Design direction* and *Notes* are the record. Then `/ticket review`.
