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
- `docs/backlog/` — *Notes* is where a ticket records what it knowingly left

Read those two sections, not the whole file. The rest of an ADR is the decision; only its
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

One row per item, grouped by source:

```
<file>:<line> — <what is limited>. ceiling: <what it cannot do>. trigger: <what makes it worth closing>.
```

Tag `no-trigger` where nothing says when to revisit; those are the rows worth reading
twice. Close with `<N> deferrals, <M> with no trigger.` Finding none is a result — say so
rather than padding the ledger with things nobody deferred.

Read and report only. Write the ledger to a file if asked, and say plainly that a file
regenerated from three sources is a fourth place for the same fact to go stale.

The marker-and-ledger idea is [ponytail](https://github.com/dietrichgebert/ponytail)'s, MIT.
