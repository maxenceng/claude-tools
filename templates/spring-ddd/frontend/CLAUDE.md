# Frontend

React 19, TypeScript, Vite. Server state through TanStack Query.

## Commands

Node is pinned in `.nvmrc` — run `nvm use` first.

- `make check` — typecheck and tests, the inner loop
- `make ci` — what CI runs: adds the duplication scan, `design-check` and the bundle
- `make design-check` — fail on the UI anti-patterns impeccable detects
- `make dev` — dev server, proxies `/api` to the backend on :8080
- `make openapi-client` — regenerate the typed API client

## Conventions

Conventions live in the `ddd-frontend` skill; `src/training/` is the worked example to copy.

Two are non-negotiable:

- Never edit `src/api/generated/` — it is produced from the backend's OpenAPI schema and
  overwritten.
- Never read backend source for an API answer. If the generated types do not answer it,
  the schema is incomplete and the backend annotation should be fixed instead.
