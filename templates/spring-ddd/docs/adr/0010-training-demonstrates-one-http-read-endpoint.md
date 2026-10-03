# 10. Training demonstrates one HTTP read endpoint

Date: 2026-10-03

## Status

Accepted

## Context

[ADR 8](0008-the-template-ships-one-worked-example-context.md) gave `training` no controller,
because the outbound-client advice was the only gap it set out to close. A frontend now needs
something to be built against, and the template has no neighbour for it to copy: no route, no
failure body, no generated client path.

A controller that waits on the catalogue vendor also changes what a vendor failure means.
`CourseCatalogueUnreachableException` was a plain `RuntimeException` precisely because nothing
decided what a caller should do about it ([ADR 9](0009-outbound-clients-are-built-with-feign.md)).
With a controller calling it, that failure would leave as a 500, which tells the caller nothing
about whether to retry.

## Decision

`training` gains one read endpoint, `GET /api/courses/popularity?title=`, and nothing else. It
stays without persistence and without any mutation; a write needs persistence and its own ADR.
This reopens and extends ADR 8 for HTTP only.

`DomainErrorStatus` gains `UNAVAILABLE`, mapped to `503`, for something the request depends on
that did not answer. `CourseCatalogueUnreachableException` now extends `DomainException` with
that status, keeping its cause, so the global handler covers it without importing `training`.

## Consequences

The generated client and `docs/openapi.json` gain `/api/courses/popularity` with `200`, `400`,
`404` and `503`, which is the contract the frontend worked example is written against.

Every context's outbound client that a controller can reach should now raise a
`DomainException` with `UNAVAILABLE` rather than a bare runtime exception.

Anything beyond this one read (a list, a write, persistence) is still a separate decision.
