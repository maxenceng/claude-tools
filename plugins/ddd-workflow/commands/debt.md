---
description: Collect the deliberate shortcuts this project chose, from code markers, ADRs and ticket notes
---

A limit somebody chose is not a defect. It becomes one the day nobody remembers choosing
it, and a deferral written down in three different places is written down nowhere. This
collects them into one ledger.

## The marker

A deliberate simplification in `src/main` carries a `deferred:` comment naming what it
cannot do, and what would make it worth closing:

```java
// deferred: the condition names the hashed password only, so a write that moves the floor
// alone is unguarded — name the floor too once "log out everywhere" exists
```

Ceiling first, trigger second. A marker with no trigger is the kind that rots, because
nothing will ever say it is time.

## Sweep

Three sources, because a deferral gets written wherever the decision was made:

```bash
grep -rn 'deferred:' src/main
```

- `docs/adr/` — *Consequences* is where a decision records what it did not close
- the tickets — *Notes* is where a ticket records what it knowingly left. Every issue, open and
  closed, comes from `${CLAUDE_PLUGIN_ROOT}/scripts/ticket-tracker notes`: a JSON list of number,
  title, state and the *Notes* text, with empty and unanalysed ones already dropped.

`notes` needs GitHub. When it refuses (exit code 3 means GitHub is unreachable, anything else says
why in its message), sweep the other two sources anyway and report the ticket source as
**skipped**, with the reason, instead of passing it off as empty: a ledger that silently lacks a
source reads as a clean one. Nothing is cached, so there is no older answer to fall back on.

Read the *Consequences* section of an ADR, not the whole file. The rest of an ADR is the decision; only its
consequences are the price.

Read them rather than grepping them for phrases. "Deliberately not" matches an ADR
explaining the ADR format and a ticket naming its own scope, and misses the deferral three
lines further down that happened to be phrased differently. The code marker is greppable
because it was written to be; prose was not.

## What counts

A limit that was chosen, with a reason: a one-second window left open, a guard covering
one column of two, a query proved only where Docker runs. Not a bug — that is a ticket.
Not work merely unstarted — that is the backlog. The test is whether somebody decided to
live with it. If nobody decided, it is not debt, it is an oversight, and it should be
raised as one instead.

## Report

One row per item, grouped by source (a ticket is named by its number, `#<n>`):

```
<file>:<line> — <what is limited>. ceiling: <what it cannot do>. trigger: <what makes it worth closing>.
```

Tag `no-trigger` where nothing says when to revisit; those are the rows worth reading
twice. Name any skipped source. Close with `<N> deferrals, <M> with no trigger.` Finding none is a result — say so
rather than padding the ledger with things nobody deferred.

Read and report only. Write the ledger to a file if asked, and say plainly that a file
regenerated from three sources is a fourth place for the same fact to go stale.

The marker-and-ledger idea is [ponytail](https://github.com/dietrichgebert/ponytail)'s, MIT.
