---
name: ddd-frontend
description: Conventions for writing frontend code in a DDD project's React + TypeScript client — a context's folder, its queries, error states and tests, against the generated OpenAPI client. Load before writing or restructuring frontend code.
---

# DDD frontend conventions

The hard rules are enforced by `src/architecture.test.ts` and the type checker. This
document covers the things a test cannot check: where a piece of UI belongs, who owns a
piece of state, what a failure should look like on screen, and how to test it.

## Read the neighbour first

Before writing a query, a component or a test, open its counterpart in `src/training/` and
copy its shape. That folder is the worked example, and where this document and the code
differ, the code wins — this document is general and the code is specific. Name the file
you matched when you report back, because that is what makes the check visible rather than
assumed.

The question is not "what is a reasonable way to write this" but "how did this project
already write it". A new hook copies `useCoursePopularity`, including what it does not do:
it never retries an answered request, so the new one does not either.

## The API boundary

The generated client in `src/api/generated/` is the whole truth about the API.

- Never edit `src/api/generated/`. It is overwritten on the next generation.
- Never read backend source to answer an API question. If the generated types do not
  answer it, the schema is incomplete — say so, so the backend fixes its annotation.
- Regenerate in two steps, with the backend running (`make run`): `make openapi` writes
  `docs/openapi.json`, then `make openapi-client` writes the types. Running only the second
  rewrites the types from a stale schema, which is how the client drifts.
- Only `src/api/` imports from `generated/`; everything else goes through `api` in
  `src/api/client.ts`. `architecture.test.ts` fails the build otherwise.

Types reach a context by inference from `api`, not by redeclaration. A field that is
`undefined` at runtime while the types insist it exists is a stale schema, every time.

## Layout

```
src/
├── api/                 the boundary: client.ts, problem.ts, generated/
├── test/                MSW server and test setup
├── <context>/           one per backend bounded context, named like it
│   ├── queries.ts       <context>Keys and one hook per server read
│   ├── <Feature>.tsx
│   └── <Feature>.test.tsx
├── App.tsx
└── main.tsx
```

- One folder per backend bounded context, named exactly like it (`training` for
  `com.example.app.training`).
- A context never imports from another context. `architecture.test.ts` enforces it.
- Shared code lives in `src/api/` or in a deliberately named shared folder added to the
  test's `sharedFolders` — never in another context that happens to have it already.

Read `references/structure.md` before adding a context or extracting shared code.

## Server state

- TanStack Query owns server state; `useState` owns local state (a draft, a submitted
  value, an open panel). Never copy query data into `useState` — two copies drift.
- Query keys come only from the context's `<context>Keys` factory in `queries.ts`
  (`trainingKeys`). An inline array is a key nothing else can invalidate.
- One hook per server read, in `<context>/queries.ts`, named `use<Thing>`. Components call
  the hook; they never call `api` themselves.
- Every call goes through `unwrap` from `src/api/problem.ts`, so a failure arrives as an
  `ApiError` and a success as plain data.
- Never retry an answered request: retry only a network failure, once, and let the UI offer
  Retry for the rest.

Read `references/queries.md` before writing a hook — it has the reasoning, the `enabled`
and `retry` choices, and mutations (which the template does not have yet).

## Errors

A failed call is an `ApiError` carrying the HTTP `status` and the ProblemDetail's `detail`.
Map the status to a state, not to one generic error screen:

| Status | Means | Render |
|---|---|---|
| 400 | the input was rejected | the `detail` on the field, `aria-invalid` + `aria-describedby` |
| 404 | nothing there yet | a normal, neutral empty-like state, no `role="alert"` |
| 409 | the request is fine, the state is not | explain why and offer what to do next |
| 5xx, network | something did not answer | `role="alert"` with the message and a Retry button |

Never retry an answered request automatically — any `ApiError`, whatever the status.

Read `references/errors.md` before rendering a failure.

## The four states

Every screen that reads the server renders and tests four states: **loading**,
**empty / not found**, **error**, **populated**. Where the query waits on input
(`enabled: false`), add a fifth: **idle**, which renders nothing that claims a result.

Put results inside an always-mounted `aria-live="polite"` region, so a screen reader hears
each new outcome; keep `role="alert"` for errors and `role="status"` for the busy
indicator. Each later lookup shows its loading state again — no `keepPreviousData`.

## Tests

- MSW intercepts at the network boundary (`src/test/server.ts`). Never mock `api`, the
  client module, or a hook — then the test proves the mock.
- One test per state, named for the behaviour a user sees.
- Query by role and label (`getByRole`, `getByLabelText`), the way a user and a screen
  reader find things; not by class or test id.
- A fresh `QueryClient` per test, so no cached answer leaks between tests.

Read `references/tests.md` before writing one — it also explains the MSW setup in
`src/test/setup.ts`, which looks wrong and is not.

## Design

Appearance follows the ticket's *Design direction* and is iterated with `/ticket design`.
`make fe-ci` runs impeccable's detector (`make design-check` in `frontend/`), so its
findings fail CI, not review. Do not restyle anything outside the ticket.

Semantic HTML from the start: a button is a `<button>`, every input has a `<label>`, and
everything interactive is reachable by keyboard.

## General React advice

For React advice this document does not cover, invoke
the `vercel-react-best-practices` skill and the `vercel-composition-patterns` skill
when they are installed; if they are not, say so once and continue. Their Next.js, React Server Component and server-side fetching
rules do not apply: this is a Vite single-page app, and data is fetched in the browser
through TanStack Query.

## Frequent mistakes

- An inline query key array instead of the `<context>Keys` factory.
- `any` instead of `unknown` and narrowing — the compiler stops helping exactly where the
  shape is in doubt.
- A redeclared API type — a hand-written copy of what the generated client already says,
  which drifts silently.
- An error screen for a 404 — "not there yet" is a normal state, not a failure.
- A test that mocks `api.GET` — it proves the mock, not the request or the error mapping.
- A component that fetches and renders in one function past one screen — split the hook
  (or an `Outcome`-style child) from the presentation, as `CoursePopularity.tsx` does.
