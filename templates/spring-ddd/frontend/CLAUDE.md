# Frontend

React 19, TypeScript, Vite. Server state through TanStack Query.

## Commands

Node is pinned in `.nvmrc` — run `nvm use` first.

- `make check` — typecheck and tests, what CI runs
- `make dev` — dev server, proxies `/api` to the backend on :8080
- `make openapi-client` — regenerate the typed API client

## The API boundary

`src/api/generated/` is produced from the backend's OpenAPI schema and is the whole
truth about the API.

Never edit it by hand — it is overwritten. Never read backend source to answer a
question about the API: if the generated types do not answer it, the schema is
incomplete and the backend annotation should be fixed instead.

## Conventions

- Server state belongs to TanStack Query, local state to `useState`. Do not copy
  server data into local state.
- Import types from the generated client rather than redeclaring shapes.
- Handle every state that occurs: loading, error, empty, populated.
- Semantic HTML, keyboard reachable, labels tied to inputs.
- Avoid `any`; use `unknown` and narrow.
