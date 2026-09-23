---
description: Scan the codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick
argument-hint: "[module or subsystem to focus on] (no args: infer hot spots from recent history)"
---

Surface architectural friction and propose **deepening opportunities**: refactors that
turn shallow modules into deep ones. The aim is testability and AI-navigability.

Requires the `mattpocock-skills` plugin (`claude plugins install mattpocock-skills`)
installed alongside this one — step 3 below calls `mattpocock-skills:grilling` by name.

Call the Skill tool with `ddd-workflow:codebase-design` for the vocabulary (module, interface, depth,
seam, adapter, leverage, locality) and its principles (the deletion test, "the interface
is the test surface", "one adapter is hypothetical, two is real"). Use these terms
exactly, and don't drift into "component," "service," "API," or "boundary". The domain
language in `docs/glossary.md` names the good seams; ADRs in `docs/adr/` record
decisions this command should not re-litigate.

## 1. Explore

**Scope before you scan.** Deepening a module pays off by making future changes to it
easier, so weight the parts of the codebase that have recently changed:

- If `$ARGUMENTS` names a direction, take it and skip the inference below.
- Otherwise, walk back `git log --oneline` to find hot spots — files and areas that keep
  coming up — and let those paths pull attention first. If changes are scattered with no
  clear hot spot, widen the net.

Read `docs/glossary.md` and any ADRs in the area you're touching first. Then spawn a
sub-agent to walk the codebase and note friction organically:

- Where does understanding one concept require bouncing across many small modules?
- Where is a module shallow — interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, while the real bugs
  hide in how they're called (no locality)?
- Where do tightly-coupled modules leak across their seams?
- Which parts are untested, or hard to test through their current interface?

Apply the deletion test to anything suspected shallow: would deleting it concentrate
complexity, or just move it? "Concentrates" is the signal worth reporting.

## 2. Present candidates as an HTML report

Write a self-contained HTML file to the OS temp directory (`$TMPDIR`, falling back to
`/tmp`) at `<tmpdir>/architecture-review-<timestamp>.html`, so nothing lands in the repo
and each run gets a fresh file. Open it (`xdg-open`/`open`/`start`) and tell the user the
absolute path.

Use Tailwind via CDN for layout and Mermaid via CDN for graph-shaped diagrams
(dependencies, call flow, sequences); mix in hand-built divs/SVG for the more editorial
visuals (mass diagrams, cross-sections). Each candidate gets a before/after
visualisation — be visual, not prose-heavy.

Per candidate card: **files** involved, **problem** (why it's causing friction),
**solution** (plain-English description of the change), **wins** stated in `codebase-design`
terms ("locality: bugs concentrate in one module", never "easier to maintain"), a
**before/after diagram**, and a **recommendation strength** badge (`Strong` / `Worth
exploring` / `Speculative`). End with a **top recommendation** section naming which
candidate to tackle first and why.

Use `docs/glossary.md`'s vocabulary for the domain and `codebase-design`'s for the
architecture — "the Order intake module," never "the OrderHandler" or "the Order
service," if the glossary defines Order.

**ADR conflicts**: only surface a candidate that contradicts an existing ADR when the
friction is real enough to warrant reopening it, flagged clearly in the card (e.g. "this
contradicts ADR-0007, worth reopening because…"). Don't list every theoretical refactor
an ADR already forbids.

Do not propose interfaces yet. Once the file is written, ask which candidate to
explore.

## 3. Grilling loop

Once a candidate is picked, call the Skill tool with `mattpocock-skills:grilling` to walk the
decision tree: constraints, dependencies, the shape of the deepened module, what sits
behind the seam, which tests survive.

Handle side effects inline as decisions crystallise, using `ddd-workflow:domain-modeling`'s
discipline to keep `docs/glossary.md` and `docs/adr/` current:

- Naming the deepened module after a concept not yet in `docs/glossary.md`? Add it,
  same change.
- Sharpening a fuzzy term along the way? Update the glossary right there.
- User rejects the candidate for a load-bearing reason? Offer an ADR — only when a
  future explorer would actually need the reason to avoid re-suggesting the same thing;
  skip ephemeral or self-evident reasons.
- Want alternative interfaces for the deepened module? Call the Skill tool with
  `ddd-workflow:codebase-design` and use its design-it-twice pattern (`references/design-it-twice.md`).

Adapted from [mattpocock/skills](https://github.com/mattpocock/skills)'s
`improve-codebase-architecture` (MIT).
