---
description: Report copy-pasted code and propose extractions worth making
---

Find duplication using the detectors, not by reading the codebase — the scan is free
and reading source to hunt for repetition is not.

```bash
make dup
```

If a frontend is present, also run its detector:

```bash
make -C frontend dup
```

Work from the reports. Read only the specific files the detectors flag.

## Judging each finding

Duplication is only a defect when the copies must change together. Two blocks that
look alike but serve different reasons for change should stay apart — extracting them
creates a shared abstraction pulled in two directions, which is harder to unpick later
than the duplication was to tolerate.

For each cluster, decide: would a change to one copy require the same change to the
other? If yes, extract. If no, leave it, and say why.

## Proposing extractions

Put the extraction where the architecture says it belongs. Shared domain behaviour
becomes a method on the domain type or a new value object — not a `Utils` class, which
is where concepts go to hide. Shared adapter plumbing stays in the adapter layer.

Never extract across a bounded context boundary to remove duplication. Two contexts
containing similar code is normal and usually correct; coupling them to save a few
lines trades a small cost for a large one.

## Report

List each cluster with its locations, whether you recommend extracting, and the reason.
Rank by how much the duplication actually costs — a repeated eight-line business rule
matters, near-identical test setup usually does not.

Apply the extractions that are clearly right and run `make test` afterwards. Raise the
judgement calls rather than deciding them silently.
