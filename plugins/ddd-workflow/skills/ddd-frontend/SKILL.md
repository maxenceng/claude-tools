---
name: ddd-frontend
description: Conventions for writing frontend code in a DDD project's React + TypeScript client — a context's folder, its queries, error states and tests against the generated OpenAPI client, screens composed from the in-house design system, copy through i18n, and the lint that enforces both. Load before writing or restructuring frontend code.
---

# DDD frontend conventions

The hard rules are enforced by `src/architecture.test.ts`, the type checker and ESLint
(`make lint`). This document covers the things they cannot check: where a piece of UI
belongs, who owns a piece of state, what a failure should look like on screen, when a
primitive needs a new variant, and how to test it.

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

Types reach a context by inference from `api`, or by name through `Schema<'Name'>` from
`src/api/client.ts` — never by redeclaration. A field that is `undefined` at runtime while
the types insist it exists is a stale schema, every time.

## Layout

```
src/
├── api/                 the boundary: client.ts, problem.ts, generated/
├── design-system/       tokens.css, global.css, one primitive per X.tsx + X.module.css, index.ts
├── i18n/                i18n.ts, i18next.d.ts, locales/<language>/<namespace>.json
├── test/                MSW server and test setup
├── <context>/           one per backend bounded context, named like it
│   ├── queries.ts       <context>Keys, the hook's predicates, one hook per server read
│   ├── <Feature>.tsx
│   └── <Feature>.test.tsx
├── App.tsx
└── main.tsx
eslint/                  the project's own lint rules, each with its RuleTester test
```

- One folder per backend bounded context, named exactly like it (`training` for
  `com.example.app.training`).
- A context never imports from another context. `architecture.test.ts` enforces it.
- `api`, `design-system`, `i18n` and `test` are shared folders, listed in the test's
  `sharedFolders`. The design system imports no context and never `api`; i18n imports no
  context.

Read `references/structure.md` before adding a context or extracting shared code.

## Server state

- TanStack Query owns server state; `useState` owns local state (a draft, a submitted
  value, an open panel). Never copy query data into `useState` — two copies drift.
- Query keys come only from the context's `<context>Keys` factory in `queries.ts`
  (`trainingKeys`), each key a tuple `as const` so it is readonly and prefix invalidation
  stays type-checked. An inline array is a key nothing else can invalidate.
- One hook per server read, in `<context>/queries.ts`, named `use<Thing>`, with an explicit
  `UseQueryResult<Schema<'…'>>` return type. Components call the hook; they never call
  `api` themselves.
- Every call goes through `unwrap` from `src/api/problem.ts`, so a failure arrives as an
  `ApiError` and a success as plain data.
- `enabled` and `retry` take named, exported, unit-tested functions — `isAskable`,
  `retriesOnlyUnansweredRequests` — never an inline condition or lambda.
- Never retry an answered request: retry only a network failure, `NETWORK_RETRIES` times,
  and let the UI offer Retry for the rest.

Read `references/queries.md` before writing a hook — it has the reasoning, the `enabled`
and `retry` choices, and mutations (which the template does not have yet).

## Errors

A failed call is an `ApiError` carrying the HTTP `status` and the ProblemDetail's `detail`.
Read it only through the predicates in `src/api/problem.ts` — `isAnswered`, `isRejected`,
`isNotFound`, `rejectionOf`, `detailOf` — and name any status in `HttpStatus`. A component
never writes `instanceof ApiError` or compares `status` to a number. Map each status to a
state, not to one generic error screen:

| Status | Means | Render |
|---|---|---|
| 400 | the input was rejected | `rejectionOf(error)` as the field's `TextField` `error` |
| 404 | nothing there yet | a neutral `Text tone="muted"`, no `Alert` |
| 409 | the request is fine, the state is not | explain why and offer what to do next |
| 5xx, network | something did not answer | an `Alert` with `detailOf(error)` (a translated fallback when nothing answered) and a Retry `Button` |

Never retry an answered request automatically — any `ApiError`, whatever the status.

Read `references/errors.md` before rendering a failure.

## The four states

Every screen that reads the server renders and tests four states: **loading**,
**empty / not found**, **error**, **populated**. Where the query waits on input
(`enabled: false`), add a fifth: **idle**, which renders nothing that claims a result.

The primitives carry the announcements: `Status` is the `role="status"` busy indicator,
`Alert` the `role="alert"` failure, and `TextField` keeps its error slot always mounted as
`aria-live="polite"`, so a 400 is heard whether the form was submitted by Enter or by the
button. Put results inside an always-mounted `aria-live="polite"` region in the screen.
Each later lookup shows its loading state again — no `keepPreviousData`.

## Design system

- Screens compose primitives from `src/design-system/` (`Page`, `Stack`, `Heading`, `Text`,
  `Button`, `TextField`, `Alert`, `Status`). Outside it, no `className` or `style` on an
  HTML element and no stylesheet import — lint fails the build.
- Tokens in `tokens.css` are the only raw values. A primitive's CSS Module reads
  `var(--…)`; a value with no token gets a token first.
- A primitive takes one prop per visual axis, typed as a string literal union of token
  names (`gap="md"`, `tone="muted"`) — never a boolean mode, never `string`, never a
  `className` pass-through.
- A primitive owns its accessibility: labels, roles, live regions, `aria-invalid`.
- When nothing fits, extend a primitive (a new value on an axis) or add one — in the same
  change, never by restyling in the screen.

Read `references/design-system.md` before adding or extending a primitive. For component API
design, invoke the `vercel-composition-patterns` skill and the `vercel-react-best-practices`
skill when they are installed.

## i18n

- No user-facing literal in a component: copy comes from `t()`, with
  `useTranslation('<context>')` — one namespace per bounded context, `common` for the shell.
- Keys say what the text is for (`popularity.notFound`), not what it says. They are typed:
  an unknown key fails `tsc`.
- `en` and `fr` stay in parity: `locales.test.ts` fails on a key missing from either, or an
  empty message. A new key goes into both in the same change.
- Values are interpolated (`t('popularity.popularityOf', { title })`), never concatenated.
- The ProblemDetail's `detail` is shown as the server sent it; only the client's own words
  are translated.

Read `references/i18n.md` before adding a namespace, a language or a key with a value in it.

## Lint

- `make lint` runs `eslint .`; `make ci` (and `make fe-ci` from the root) runs it. Every
  rule is at `error`, so any finding fails the build.
- It enforces: Vercel's archived style-guide rules rebuilt on maintained plugins,
  typescript-eslint `strictTypeChecked`, react-hooks with the React Compiler rules,
  jsx-a11y, and the review rules — `local/no-literal-copy` (copy through i18n),
  `local/no-jsx-comments`, and styling only inside `src/design-system/`.
- Fix the code, not the rule. An inline disable is the last resort and states its reason:
  `// eslint-disable-next-line <rule> -- <why>`. One without a reason fails, and so does
  one that no longer suppresses anything.

Read `references/lint.md` before disabling a rule or adding one — it lists what the rules
do not catch.

## Tests

- MSW intercepts at the network boundary (`src/test/server.ts`). Never mock `api`, the
  client module, or a hook — then the test proves the mock.
- One test per state, named for the behaviour a user sees.
- Query by role and label (`getByRole`, `getByLabelText`), the way a user and a screen
  reader find things; not by class or test id.
- A fresh `QueryClient` per test, so no cached answer leaks between tests.
- Assert the English copy; the setup pins `en`. One test switches language to prove the
  screen is translated.
- Named predicates get plain unit tests (`problem.test.ts`, `queries.test.ts`); a local
  lint rule gets a RuleTester test beside it.

Read `references/tests.md` before writing one — it also explains the MSW setup in
`src/test/setup.ts`, which looks wrong and is not.

## Appearance

Appearance follows the ticket's *Design direction* and is iterated with `/ticket design`.
`make fe-ci` runs impeccable's detector (`make design-check` in `frontend/`), so its
findings fail CI, not review. Do not restyle anything outside the ticket. A change of look
lands in a token or a primitive, so it changes every screen that uses it.

Semantic HTML from the start: a button is a `<button>`, every input has a `<label>`, and
everything interactive is reachable by keyboard. The primitives do this for what they
render; the screen's own structure (`<section aria-labelledby>`, `<form>`) stays semantic.

## General React advice

For React advice this document does not cover, invoke the `vercel-react-best-practices`
skill and the `vercel-composition-patterns` skill when they are installed; if they are
not, say so once and continue. Their Next.js, React Server Component and server-side
fetching rules do not apply: this is a Vite single-page app, and data is fetched in the
browser through TanStack Query.

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
- A comment inside JSX — the explanation goes in the component's TSDoc, above it.
- A string literal shown to a user, including a fallback (`detail ?? 'Something went
  wrong'`) — it is copy, so it is a key.
- A `className` on a raw element in a screen — compose primitives, and extend one when
  none fits.
- An inline condition or a magic status number in a component (`title.trim() !== ''`,
  `error.status === 404`) — name it as a predicate in `queries.ts` or `problem.ts`.
- A new token prop typed `string` instead of a literal union — the compiler accepts any
  value, and the copy rule reads every literal passed to it as copy.
