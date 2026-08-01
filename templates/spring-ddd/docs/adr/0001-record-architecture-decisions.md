# 1. Record architecture decisions

Date: 2026-08-01

## Status

Accepted

## Context

Decisions that shaped the architecture get forgotten, and are then either re-litigated
or silently reversed. This is worse when a coding agent is involved: without the
reasoning it will reasonably propose the option that was already rejected.

## Decision

Record every architecturally significant decision as a numbered file in `docs/adr/`.
Significant means it constrains future work: layering, module boundaries, persistence,
transaction scope, choice of framework.

Keep the format to context, decision, consequences. Never edit an accepted ADR — write
a new one that supersedes it, so the history of reasoning stays readable.

## Consequences

Reviewers and agents can answer "why is it like this" without archaeology through git
history. The cost is one short file per significant decision.
