# design

Iterate on a frontend ticket's UI with the human until they call it done. This is the one
verb that never decides for itself when it is finished: taste is the judgement nothing
else in this workflow can make, and a loop that stops on its own is making it.

Run `${CLAUDE_PLUGIN_ROOT}/scripts/ticket-tracker ready <n> design` first: it refuses a ticket that is
not `in-progress`, or that does not touch `frontend/**`, with the reason. Status does not change here;
this sits between `start` and `review`.

The commands below are the template's (`npm`, `make fe-check`, Vite on 5173). Where the
project's `CLAUDE.md` or `Makefile` names others, its package manager, its frontend
targets, its port, use those. The project's commands win.

## Setup

Start `make run` and `make -C frontend dev` in the background. Work out the route the
ticket changes from its criteria and the diff; ask only if neither says.

A desktop shell (Tauri, Electron) is the exception: never launch its window from a tool
call, background or not. Some shells freeze the terminal the session runs in. Ask the
human to launch it in their own terminal, capture it with the desktop's screenshot tool
(`grim`, `screencapture`), and ask them to click where a state needs a gesture. Where the
shell's web view exposes no DevTools protocol (WebKitGTK), the detector and the critique
read the source and the screenshot only. Say so in the PR.

## One round

1. `npm --prefix frontend exec -- impeccable detect --json http://localhost:5173/<route>`,
   run through the frontend so the pinned version and `frontend/.impeccable/config.json`
   apply. Fix every finding
   straight away and say what you fixed. A detector hit is a rule, not an opinion, so it
   is not put to the human. The one exception is a hit the human already kept on purpose.
   Those are recorded in *Design direction*, and the fix is to silence it in the config,
   not to change the look.
2. Screenshot the route through `claude-in-chrome`, or as *Setup* says for a desktop
   shell. If neither is possible, say so and stop: a critique without a screenshot is
   guessing.
3. Invoke the `impeccable:impeccable` skill with `critique`.
4. Show the human the screenshot and the critique together, then ask through
   `AskUserQuestion` which move to make: the two to four named moves the critique points
   at — from `quieter`, `bolder`, `polish`, `distill`, `typeset`, `layout`, `colorize`,
   `animate` — your recommendation first, each description saying what it would change on
   this screen. They pick one, or answer in their own words.
5. Apply it: a named move through the `impeccable:impeccable` skill, free-form feedback
   by hand. Either way the change lands in `frontend/src/design-system/` — a token in
   `tokens.css`, or a primitive's variant or module — never in the screen, which may not
   style itself. Run `make fe-check` and `make fe-lint` before the next round; a design
   change that breaks a test or the lint is not a design change yet.

Repeat until the human says it is done. Show one round at a time; a batch of changes
nobody saw separately is a design nobody chose.

## Before handing over

If the direction itself moved — not a tweak, a different answer to what the screen is
for — update *Design direction* and add one line to *Notes* saying what changed and why (both through
`ticket-tracker write-sections`). That section is what `review` and the next ticket read.

Stop the background `make run` and `dev` servers once the loop ends.

Commit the work. Critique reports under `.impeccable/critique/` are not committed; the
ticket's *Design direction* and *Notes* are the record. Then `/ticket review`.
