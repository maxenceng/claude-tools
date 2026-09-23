---
name: domain-modeling
description: Actively challenge and sharpen a bounded context's ubiquitous language as you design — catching drift, inventing edge-case scenarios, and writing resolved terms into docs/glossary.md and decisions into docs/adr/ the moment they crystallise, not in a batch afterward. Use when discussing terminology, modelling an aggregate, or a decision is hard to reverse and surprising without context.
---

# Domain modelling

The *active* discipline, distinct from the one-line habit of reading `docs/glossary.md`
for vocabulary that any skill already does. This is for when the model is being changed,
not merely consumed.

This project already has the file conventions — `docs/glossary.md` (one section per
bounded context, listed in `docs/context-map.md`'s table), `docs/adr/NNNN-kebab-title.md`
— match the shape of the lowest-numbered ADR already there, the same "read the neighbour
first" habit `ddd-backend` uses for code. This skill is the behaviour on top: when to
challenge a term, when a decision earns an ADR, and doing it inline instead of batching
it up.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with `docs/glossary.md`, say so immediately:
"the glossary defines cancellation as X, but you seem to mean Y — which is it?" Silence
here is how two names for one thing start coexisting, which the glossary itself calls out
as the failure mode to avoid.

### Sharpen fuzzy language

When a term is vague or overloaded, propose the precise one. "You're saying 'account' —
do you mean the Customer or the User? Those are different things, and the glossary
should say which."

### Discuss concrete scenarios

When a domain relationship is on the table, stress-test it with a specific edge case.
Invent scenarios that force precision about where one concept ends and another begins —
this is usually where a term everyone thought was settled turns out not to be.

### Cross-reference with code

When the user states how something works, check whether the code agrees. Surface the
gap plainly: "the code cancels entire Orders, but you just said partial cancellation is
possible — which is right?"

### Update the glossary inline, not in a batch

The moment a term resolves, add or correct its row in `docs/glossary.md`, in the section
for that bounded context — same change, not a follow-up pass. A glossary updated later
documents what survived the session, not what the words actually mean, which is the
failure the file's own header warns against.

`docs/glossary.md` is a glossary, never a spec, a scratchpad, or a place to park an
implementation decision. If what you're about to write is "why", it's an ADR, not a
glossary row.

### Offer an ADR sparingly

Offer one only when all three hold:

1. **Hard to reverse** — the cost of changing your mind later is real.
2. **Surprising without context** — a future reader, or agent, will wonder why it's this
   way.
3. **The result of a genuine trade-off** — there were real alternatives, and one was
   picked for specific reasons.

Missing any of the three, skip it — most decisions aren't ADRs, and an ADR ledger nobody
trusts is as useless as a glossary nobody trusts. When you do write one, follow the
existing shape (context, decision, consequences) and let `scripts/check-adr-numbers.py`
catch a collided number rather than hand-picking one under time pressure.

Adapted from [mattpocock/skills](https://github.com/mattpocock/skills)'s `domain-modeling`
(MIT), retargeted at this repo's existing glossary/ADR conventions instead of introducing
a competing `CONTEXT.md` format.
