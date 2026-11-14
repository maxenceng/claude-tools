---
name: ddd-frontend
description: Conventions for writing frontend code in a DDD project's React + TypeScript client — a context's folder, its queries, error states and tests against the generated OpenAPI client, screens composed from the in-house design system, copy through i18n, and the lint that enforces both. Load before writing or restructuring frontend code.
---

# DDD frontend conventions

The hard rules are enforced by `src/architecture.test.ts`, the type checker and ESLint
(`make fe-lint`). This document covers the things they cannot check: where a piece of UI
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
`src/api/client.ts` — never by redeclaration, and never through a hand-kept list of aliases
that renames them (`type Ticket = BoardTicketView`). A rename list has to be updated with
every schema change and tells the reader nothing the generated name does not. Use the name
the generator gives. A field that is `undefined` at runtime while
the types insist it exists is a stale schema, every time.

The client never re-derives a rule the domain owns. If a screen needs a value the backend
computes — whether a thing is overdue, which of several states wins — the response carries
it as a field. Working it out again from the raw fields writes the rule twice, and the two
copies drift the first time the domain changes. Missing a field is a backend change, not
a helper in the context.

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
- A folder that only composes contexts — app-wide key handling, a connection screen — is
  the composition side, listed in the test's `compositionFolders`. No context and no shared
  folder imports it; only the files directly in `src/` do. It is the frontend's twin of
  "nothing depends on the shell".
- The files directly in `src/` (`App.tsx`, `main.tsx`, any `app.ts` wiring them) compose
  too, so no context and no shared folder imports one either. A type or helper a context
  wants from there belongs in that context or a shared folder.

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
- A refetch replaces what is shown, never where the user is. Scroll and selection move
  only on the user's own open or select; a default selection is settled on the first read
  and kept, not re-derived ("the first row") from every later one.
- A failed refetch keeps the last answer shown, the failure beside it. A failed read is not
  an empty one: an item whose ask failed never reads as "none" or drops from the list.
- A read per row (one request for each item, to join something onto it) runs over the rows
  drawn — after the cut, the page or the window — never over the whole list they came from.

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

A Retry `Button` re-sends a read. After a failed write, offer it only when the write is
known not to have landed (the server refused it before writing). A write whose call failed
may have landed, so read the state again and show what is there; a Retry there writes twice.

Read `references/errors.md` before rendering a failure.

## The four states

Every screen that reads the server renders and tests four states: **loading**,
**empty / not found**, **error**, **populated**. Where the query waits on input
(`enabled: false`), add a fifth: **idle**, which renders nothing that claims a result.

The primitives carry the announcements: `Status` is the `role="status"` busy indicator,
`Alert` the `role="alert"` failure, and `TextField` keeps its error slot always mounted as
`aria-live="polite"`. Put results inside an always-mounted `aria-live="polite"` region in
the screen.
Each later lookup shows its loading state again — no `keepPreviousData`.

What each state looks like on screen:

- **Loading** holds the populated layout. Where the result has a shape (rows, figures), the
  placeholders sit at their real size with labels and headers already shown, so nothing
  shifts when the data lands; no shimmer. A single lookup's `Status` line is enough.
- **Empty** keeps the region's frame and heading and adds one sentence saying what belongs
  there and, where there is one, the action that fills it.
- **Error** renders inside the region that failed, never as a whole-screen replacement: what
  failed, and the Retry `Button` for a 5xx.
- **Zero is data, absence is not**: a real zero prints as `0`; a value that is missing or
  does not apply is a muted dash.
- **Counts follow the view**: a count shown beside a filter or tab is computed from the rows
  in that view and recomputed when it changes.

Read `references/data-display.md` before laying out figures, deltas, tables or a dashboard.

## State shapes

A state the project writes by hand — a screen's four states, a connection's phases — is a
set of classes discriminated by an enum `kind`, not a union of object literals. The union
of the classes keeps `switch` narrowing; each class answers the questions its callers ask
(`isReady()`, `shown()`), so no caller compares a kind to reach a field. Behaviour is a
prototype method, not an arrow field, so two equal states compare equal.

- A closed set of names that means something (an action, a cause, a panel, a kind of
  comment) is an enum, compared and passed by its members, never a union of string
  literals. Lint refuses the union outside `src/design-system/`. A design token prop stays a
  literal union: it names a token, not a meaning.
- Generated types stay plain objects. A store turns a response into a state class at the
  boundary.

## Stateful pieces

Anything that keeps state and acts on it — a store, a controller, the client, a key
handler, a test fake — is a class with private fields and methods. It is never a factory
that returns an object of closures over its local variables. A factory hides its state
where neither a type nor a test can name it, and it keeps growing: the first one becomes
the 300-line closure every feature is added to. A named helper sits at module level, never
inside another function. A callback passed inline (a listener, a `map`, a JSX handler)
stays an inline arrow.

A method passed as a value loses its `this`, so wrap it in an arrow where it is handed over
(`useSyncExternalStore((l) => store.subscribe(l), () => store.snapshot())`).

ESLint enforces it in source and tests alike, through two more `no-restricted-syntax`
entries:

```js
const NO_NESTED_FUNCTIONS = [
  {
    selector: ':function VariableDeclarator > :matches(ArrowFunctionExpression, FunctionExpression)',
    message: 'Declare the helper at module level, or make this a class with a private method.',
  },
  {
    selector: ':matches(:function ReturnStatement, ArrowFunctionExpression) > ObjectExpression > Property > :function',
    message: 'An object of closures is a class: give it private state and methods.',
  },
]
```

## Design system

- Screens compose primitives from `src/design-system/` (`Page`, `Stack`, `Heading`, `Text`,
  `Button`, `TextField`, `Alert`, `Status`). Outside it, no `className` or `style` on an
  HTML element and no stylesheet import — lint fails the build.
- Tokens in `tokens.css` are the only raw values. A primitive's CSS Module reads
  `var(--…)`; a value with no token gets a token first.
- A new or changed token pair — text or a mark on its ground — meets WCAG AA before review:
  4.5:1 for text, 3:1 for large text and for marks. Dimmed text is still text. A new fill or
  tint (a selected card, a status tint) is checked against every ink drawn on it, the
  dimmest first. A token test that measures each pair keeps the next fill honest.
- A primitive takes one prop per visual axis, typed as a string literal union of token
  names (`gap="md"`, `tone="muted"`) — never a boolean mode, never `string`, never a
  `className` pass-through.
- A primitive owns its accessibility: labels, roles, live regions, `aria-invalid`.
- A primitive is named for what it renders, never for the screen it was written for. One
  that began as `TicketList` is renamed `Rows` in the change that gives it a second caller.
- When nothing fits, extend a primitive (a new value on an axis) or add one — in the same
  change, never by restyling in the screen.
- A class in a primitive's CSS Module is named for its role there, never for another
  primitive: `.pane` inside `Detail`, when `Pane` is a primitive, reads as that primitive.
  Call it `.frame`.
- A primitive that only works inside another's frame — a container query reading `cqi`, a
  context it expects — is not exported from the design system. The frames that supply it
  are, and `architecture.test.ts` refuses any other importer of it.

- Stacking is a token scale (`--layer-sticky`, `--layer-overlay`), never a bare `z-index`
  per stylesheet. A sticky header sits below every dialog and popup, or it covers the
  field a dialog opened to edit. A row the cursor can reach carries a `scroll-margin-top`
  of the sticky header's height, so scrolling it into view never parks it under the header.

Read `references/design-system.md` before adding or extending a primitive. For component API
design, invoke the `vercel-composition-patterns` skill and the `vercel-react-best-practices`
skill when they are installed.

## i18n

- i18n stays even when the product ships one language. A single-language project drops
  the second locale and the parity test, never the catalogue: copy written inline is
  scattered across screens, and every screen added later makes the move dearer.
- No user-facing literal in a component: copy comes from `t()`, with
  `useTranslation('<context>')` — one namespace per bounded context, `common` for the shell.
- Keys say what the text is for (`popularity.notFound`), not what it says. They are typed:
  an unknown key fails `tsc`.
- `en` and `fr` stay in parity: `locales.test.ts` fails on a key missing from either, an
  empty message, or a plural without exactly its language's forms (French has `_many`).
  A new key goes into both in the same change.
- Values are interpolated (`t('popularity.popularityOf', { title })`), never concatenated.
- The ProblemDetail's `detail` is shown as the server sent it; only the client's own words
  are translated.

Read `references/i18n.md` before adding a namespace, a language or a key with a value in it.

## Lint

- From the project root, `make fe-lint` runs ESLint and `make fe-ci` runs it with
  everything else; inside `frontend/` they are `make lint` and `make ci`. The root's own
  `make lint` is the backend's formatting check, not ESLint. Every rule is at `error`, so
  any finding fails the build.
- Beyond Vercel's rules, five enforce the review: `local/no-literal-copy`,
  `local/no-jsx-comments`, styling only inside `src/design-system/`, a regular
  expression only as the value of a module-level `const` whose name says what it matches,
  and no union of string literal types outside the design system (an enum instead).
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
- jsdom lays nothing out, so a criterion about how a screen looks — a line clamp, an
  overflow, a wrap — is not proved by a test. What a test can pin is the stylesheet: read
  the CSS Module and assert the rule and tokens that produce the look (`clamp(…)`,
  `grid-column`, `overflow-x`). Say in the pull request which criteria rest on that, and
  tick them only once a screenshot of the rendered screen shows the look.
- A test helper that imports a Node built-in (`node:fs` to read a stylesheet) is refused
  outside tests by `architecture.test.ts`, so it never reaches the bundle.

Read `references/tests.md` before writing one — it also explains the MSW setup in
`src/test/setup.ts`, which looks wrong and is not.

## Appearance

Appearance follows the ticket's *Design direction* and is iterated with `/ticket design`.
When that direction names an approved prototype, the prototype is the spec. Read
`references/prototypes.md` for how prototypes are made at `refine` and what "build what it
draws" excludes.
`make fe-ci` runs impeccable's detector (`make design-check` in `frontend/`), so its
findings fail CI, not review. Do not restyle anything outside the ticket. A change of look
lands in a token or a primitive, so it changes every screen that uses it.

State a user would share or come back to — a filter, the selected tab, the page — lives in
the URL's search params, not in `useState`, so a reload or a pasted link lands on the same
view. Navigation starts as a top bar; a sidebar is earned by more than
about seven destinations.

Semantic HTML from the start: a button is a `<button>`, every input has a `<label>`, and
everything interactive is reachable by keyboard. The primitives do this for what they
render; the screen's own structure (`<section aria-labelledby>`, `<form>`) stays semantic.

A shortcut on a digit or a punctuation key matches `KeyboardEvent.code` (`Digit1`), never
`key`: on AZERTY a bare digit key's `key` is `&`. A letter stays on `key`, which follows the
layout the user reads.

An app driven from the keyboard (a tool, a board, an IDE-like window) keeps these too:

- Every action has a visible control and a key. A key-only action is undiscoverable, and a
  button-only one is slow. Both call the same function. The control's tooltip and
  accessible label name the key.
- A key hint (a key bar, a chip beside a control) shows only keys that act in the current
  state. A hint for a key that does nothing teaches the user to ignore hints.
- Focus is unmistakable: the focused pane is lit and the others recede. A selection is
  solid only in the focused pane. Elsewhere it stays visible but quieter, never cleared,
  so moving back finds it.
- A click never moves the focus out of where the keys go. A button, and a popup's scrim,
  prevent the default of their `mousedown` and act on `click`, so a press on either leaves
  a popup's input focused. A window-level click guard that lets the scrim through is no
  help here: the scrim's own press is the one that blurs the input.
- A state is never told by colour alone. A lamp, a status or a tab's state also carries a
  word or a glyph.

## General React advice

For React advice this document does not cover, invoke the `vercel-react-best-practices`
skill and the `vercel-composition-patterns` skill when they are installed; if they are
not, say so once and continue. Their Next.js, React Server Component and server-side
fetching rules do not apply: this is a Vite single-page app, and data is fetched in the
browser through TanStack Query.

A long list with a cursor (a diff, a table, a board) re-renders only the rows a change
reaches. Each row is a memoised component whose props are what it draws (its line, whether
the cursor is on it), never the whole list or a callback rebuilt each render. A cursor move
then redraws two rows, and a keystroke in a box redraws one. A test counts the renders a
move causes, so a later prop that defeats the memo fails the build rather than lagging.

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
- A shared primitive still named for its first caller (`TicketList` rendering documents
  too) — rename it for what it renders when the second caller arrives.
- A new token prop typed `string` instead of a literal union — the compiler accepts any
  value, and the copy rule reads every literal passed to it as copy.
- A set of values with a meaning written as a string union outside the design system
  (`'diff' | 'comments' | 'files'`) — it is an enum.
- A CSS Module class named after another primitive (`.pane` when `Pane` exists) — name it
  for its role in this one.
- A frame-dependent primitive exported from the design system — any screen can render it
  outside the frame that makes it work.
- A hand-kept list of aliases renaming generated types — import the generated name.
- A bare `z-index` in a primitive's stylesheet — a sticky header then covers a dialog;
  take a layer token.
- A long list whose rows take the list, or a callback rebuilt every render, as a prop —
  every cursor move re-renders every row.
