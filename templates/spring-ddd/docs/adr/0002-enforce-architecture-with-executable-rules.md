# 2. Enforce architecture with executable rules, not prose

Date: 2026-08-01

## Status

Accepted

## Context

The architecture was previously described in a long instructions file read by coding
agents on every request. That approach has two costs. It is expensive, because the
rules are re-read constantly whether or not they are relevant. And it is unreliable,
because a described rule is advisory — nothing fails when it is broken.

## Decision

Express architecture rules as tests wherever they can be expressed that way.

- `ArchUnit` covers layering: inward dependencies, a framework-free domain, ports
  owned by the domain, no setters on aggregates.
- `Spring Modulith` covers bounded context boundaries, and generates the architecture
  diagrams from the same structure.

Prose is kept for what tests cannot express: which context a concept belongs to,
whether an aggregate boundary is well drawn, and the ubiquitous language. That prose
lives in `docs/` and in skills that load on demand, not in always-resident context.

## Consequences

Violations fail the build instead of surviving review. The always-loaded instruction
file shrinks to roughly thirty lines, which reduces token cost on every request.

Rules must now be written as code, which is more work up front than writing a sentence.
That cost is paid once; the sentence would have been paid on every request forever.

Rules that genuinely need to change are changed deliberately, in a commit, with an ADR —
rather than by an agent quietly deciding a guideline did not apply.
