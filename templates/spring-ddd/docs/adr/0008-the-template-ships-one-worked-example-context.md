# 8. The template ships one worked example context

Date: 2026-09-05

## Status

Accepted

## Context

`CLAUDE.md`, `docs/context-map.md` and the top-level `README.md` all said the same thing:
this template holds no business context, only the two kernels. That was deliberate — a
generated project should start from a shape its own domain has not touched yet, not from
someone else's example it has to unlearn.

It had a cost nothing here caught. `ddd-backend`'s advice on outbound clients — how to build
a vendor's API client, where its wire shapes live, what `ArchitectureTest` enforces about
either — described a shape with nothing behind it anywhere in this repository: not in the
template, which had no context to hang a client off, and not in the archetype, generated
from the template. The skill went stale exactly the way `HOWTO.md` already warns prose does
("a skill recommending a method that does not exist"), and nothing failed, because nothing
built against it. A real project (`next-suggestions`) had to correct the advice after
building the same pattern for itself, on its own timeline, unrelated to this repo's own CI.

The two designs available were: keep the template context-free and accept that its
outbound-client advice is unverifiable here, or give it one context real enough to build,
test and fail against. The first is what this repo already had, and is what let the advice
go stale silently for as long as it did.

## Decision

The template ships one example bounded context, `training`, whose only job is to give the
outbound-client pattern (see [ADR 9](0009-outbound-clients-are-built-with-feign.md))
something real to be built and tested against. It is deliberately thin: `Course`, `CourseId`
and `Title` exist only so `Course` has an identity and a name to look up a vendor by;
`Popularity`, the one field an external "training catalogue" supplies, is the whole reason
the context exists. There is no controller, no persistence adapter, and no use case beyond
filling that one field — anything more would be a second example (persistence, HTTP) this
template already demonstrates having zero contexts to attach it to before now, and would
cost more to keep building against than the one gap this closes.

`CLAUDE.md`, `docs/context-map.md` and `README.md` no longer say a business context does not
exist; they say this one does, and that it is an example to delete or rename, not a
domain to build on. A project generated from the archetype starts with `training` present,
the same way it starts with the four placeholder prompts `CLAUDE.md` already ships and
`make doctor` reports as unwritten until replaced.

## Consequences

`docs/glossary.md` gets a `## training` section — the same convention any other context
would need, proving the convention still holds with a real context to check it against.

`archunit.properties`'s tolerance for a project with no bounded context is still needed: a
generated project that deletes `training` before writing its own first context passes back
through the state that file exists for. Nothing about that mechanism changes.

The archetype copies `training` like any other package, unrenamed by this decision — the
Maven archetype's own package substitution handles it the same way it already handles
`shared` and `error`. `scripts/verify-archetype.sh` is what proves that rather than this ADR
asserting it.

The next context this template is asked to demonstrate — persistence, an HTTP endpoint, a
Temporal workflow — reopens this same trade-off: real enough to build against, or the
prose stays unverified until a project finds the gap for us again. This one closes the
outbound-client gap specifically and does not pre-empt that question for the others.
