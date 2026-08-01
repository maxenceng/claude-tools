# 3. Pin TypeScript 5 for the generated API client

Date: 2026-08-01

## Status

Accepted

## Context

The frontend consumes the backend through a TypeScript client generated from the
OpenAPI schema. That generation is what allows frontend work to proceed without ever
reading backend source, so the generator is load-bearing rather than incidental.

TypeScript 7.0.2 is current, but `openapi-typescript@7.13.0` — its latest release —
declares a peer dependency on TypeScript `^5.x`. Installing TypeScript 7 leaves npm
reporting an invalid tree, and the generator is not tested against it.

## Decision

Pin the frontend to TypeScript `^5.9.3`.

Prefer the generator over the newer compiler. Losing generation would mean either
hand-maintaining API types, which drift silently, or letting frontend work read
backend source, which is exactly the coupling the schema boundary removes.

## Consequences

The frontend runs one major version behind on TypeScript. Nothing in the current code
needs TypeScript 7, so the practical cost today is zero.

This should be revisited when `openapi-typescript` supports TypeScript 7. Until then,
an upgrade attempt will produce an invalid dependency tree rather than a clear error,
so this file is the explanation.
