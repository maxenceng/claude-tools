# Frontend

React 19, TypeScript, Vite. Server state through TanStack Query, copy through
react-i18next, styling through the design system in `src/design-system/`.

## Commands

Node is pinned in `.nvmrc` — run `nvm use` first.

- `make check` — typecheck and tests, the inner loop
- `make ci` — what CI runs: adds lint, the duplication scan, `design-check` and the bundle
- `make lint` — fail on code that breaks the conventions: copy outside i18n, comments in
  JSX, styling outside the design system, and Vercel's React and TypeScript rules
- `make design-check` — fail on the UI anti-patterns impeccable detects
- `make dev` — dev server, proxies `/api` to the backend on :8080
- `make openapi-client` — regenerate the typed API client

## Conventions

Conventions live in the `ddd-frontend` skill; `src/training/` is the worked example to copy.

These are non-negotiable; `make ci` fails on the first two:

- A screen composes primitives from `src/design-system/` — no `className`, `style` or
  stylesheet outside it. When nothing fits, extend or add a primitive.
- No user-facing literal: every word on screen comes from `t()`, in the context's namespace,
  with the key in both `en` and `fr`.
- Never edit `src/api/generated/` — it is produced from the backend's OpenAPI schema and
  overwritten.
- Never read backend source for an API answer. If the generated types do not answer it,
  the schema is incomplete and the backend annotation should be fixed instead.
