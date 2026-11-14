# Prototypes

How a frontend ticket's look is decided at `refine`: by variants the human sees, not by
options described in prose. "A thin seam or a lit title row?" cannot be judged from words.
The same two side by side are judged in seconds.

## When

Prototype when `refine` has a visual question: focus, type, colour, layout, density, where
an action sits. Skip it for a ticket that only adds a field to a screen whose look is
already settled. Write *Design direction* from the existing screen instead.

Audit first. Screenshot the screen as it is today, in each state the ticket touches, and
show it before any variant. Keep these shots as variant 0 (`proto-R0-list.png`), so the
variants are judged against today and not against nothing. Some states cannot be shown
live, like a review screen with no open pull request. Give those canned data in the
prototype, or open a throwaway scratch pull request if the project allows one. Say which.

## The branch

A prototype lives on a throwaway branch, `prototype/<topic>`, pushed to origin. It is
never merged. It sits in the frontend's own tree, so it reads the real `tokens.css`,
fonts and primitives:

```
frontend/prototype-<topic>.html          entry page
frontend/prototype/<topic>/
  main.tsx                               picks the variant from ?variant=, ←/→ cycles, Tab moves focus
  Variant<A..>.tsx, variant<A..>.css     one file per variant; a later variant may import an earlier one
  data.ts                                canned data, including the empty and failing cases
  shots/proto-<variant>[-<state>].png    one screenshot per variant and state
```

Add a `prototype` script to `package.json` that serves the entry page on a port of its
own (`vite --port 1421 --open /prototype-<topic>.html`), so it never clashes with the dev
server. Let each state be a search param (`&board=empty`, `&prs=empty`, `&pr=review`),
so a screenshot and a reviewer can reach it from its URL alone.

Use canned data, never the live backend. A variant is judged on its look, and a variant
that needs the app running cannot be screenshotted headless.

## Screenshots

Take them headless, in a plain browser (Chromium through Playwright or `claude-in-chrome`),
at the window size the app runs at. Commit them to `shots/` on the prototype branch. The
human may never run the prototype; the shots are what they compare.

A desktop shell (Tauri, Electron) is the one case where the browser is not the app. Never
launch the shell's window from a session. Some shells freeze the terminal the session runs
in, and WebKitGTK has no DevTools protocol to drive. The prototype stays a plain browser
page for that reason.

## Asking

Show the shots together, then ask through `AskUserQuestion` with each variant as an option.
The human will often answer with a mix: "D: B's look, A's focus". Build that mix as a new
variant, shoot it, and show it again. Never write a mix into the ticket unseen. Iterate
until one variant is chosen. Each round's variants stay on the branch, so a rejected one
can be revisited.

An `impeccable detect` hit on something a variant draws on purpose is put to the human
here, with the variant: "the detector calls the type edge a side-tab accent; keep it?".
Write the answer into *Design direction*. Every later step honours it, and silencing it in
`.impeccable/config.json` is part of the build.

## The pointer block

Pin the chosen variant at a commit and open *Design direction* with a pointer block. Each
ticket built from the same branch repeats it, so `start` finds the reference without a
search:

```markdown
**Prototype, the reference for this ticket's look.** Throwaway branch `prototype/<topic>` on
origin, pinned at commit `<sha>` (`git fetch origin prototype/<topic>`; read with
`git show <sha>:<path>`, never merge it). Variant **<X>**: source `<files>`, on <base
variant>'s `<files>`. Screenshots: `<shots/...png>` (one per state, the empty one
included). To run it: `git worktree add ../<topic>-proto <sha> && cd ../<topic>-proto/frontend
&& <install> && <run prototype>`, then `http://localhost:<port>/prototype-<topic>.html?variant=<X>`
(<state params>).

What it decides: <the variant, and what it takes from which earlier variant>. <Anything
it draws that is not built, and why.> <Detector hits kept on purpose.>
```

Then the three lines `refine` asks for (the question, the finding, the job). Rejected
variants go in *Notes* in one line each, with what was kept from them. That stops the next
ticket from proposing them again.

## Once approved, it is the spec

From `start` onwards the chosen variant is what gets built. Where it is silent, build the
nearest thing it shows. Do not raise a layout question it does not draw, and do not add a
feature it does not show. Two exceptions, both checked before building:

- A field the prototype shows but an ADR keeps off stays off. Re-read the ADRs that touch
  the screen.
- A state the prototype tells apart by colour alone keeps a non-colour marker too (a glyph,
  a word).

Anything else the build cannot draw as the prototype draws it is an `Open` item for the
human, never a quiet departure.

## A broad ticket splits

"Improve the UX" is several tickets. Split it at `refine` into:

1. **The system ticket.** Tokens, primitives, focus treatment, one rule for where actions
   sit. Its ADR records the system.
2. **One ticket per screen**, built on the system. Each answers its screen's question,
   finding and job.

The screen tickets are drafts blocked by the system ticket (`ticket-tracker add-blocker`).
Each is refined only once the system has landed, with the same audit and variants and on
the same prototype branch, because a screen prototyped on a system still in flux is redone
when the system moves.
