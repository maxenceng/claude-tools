# Tests

Vitest, Testing Library and MSW, in jsdom. A component test renders the real component,
with the real hook and the real generated client, and intercepts only the HTTP request.

## Mock the network, nothing else

```ts
// src/test/server.ts
import { setupServer } from 'msw/node'

export const server = setupServer()
```

```tsx
// src/training/CoursePopularity.test.tsx
type Responder = (info: { request: Request }) => Response | Promise<Response>

function popularity(respond: Responder): void {
  server.use(http.get('*/api/courses/popularity', respond))
}

function problem(status: number, detail: string): () => Response {
  return () => HttpResponse.json({ status, detail }, { status })
}
```

Intercepting at the network is what makes the test cover what breaks: the path, the query
parameter, `unwrap`'s narrowing of the ProblemDetail, the retry policy, and the mapping of
status to state. A test that mocks `api.GET` or `useCoursePopularity` skips all of that and
proves only that the mock returns what it was told to.

Each test registers the handlers it needs with `server.use`; `resetHandlers` after each test
drops them. The server starts with no handlers at all, so a request nobody expected is an
error (below), not a silent pass.

## One test per state

`CoursePopularity.test.tsx` has one test per state the screen can be in, named for what the
user sees:

| State | Test |
|---|---|
| idle | *asks nothing until a title is submitted* |
| populated | *shows the popularity of a known course* |
| empty / not found | *says, neutrally, that a course has no popularity yet* |
| error | *offers a retry when the vendor is unavailable* |
| error, no answer | *says the server could not be reached when nothing answers, not what fetch threw* |
| rejected input | *ties a rejected title to the input, without an alert* |
| rejected input, announced | *announces a rejected title submitted with Enter from the input* |
| loading | *shows a busy indicator while the lookup is in flight* |
| loading again | *shows the busy indicator again, then the new value, on a second lookup* |
| translated | *speaks French when the language is French* |

A test name says the behaviour, not the mechanism: *says, neutrally, that…* records that a
404 must not raise an alert, and the test asserts `queryByRole('alert')` is null.

Assert what the name claims, or the test passes for the wrong reason. *asks nothing…* counts
the handler's calls and asserts `0` after typing a title and waiting — no `status` and no
`alert` would also be true of a component that asked and had not heard back yet. *shows the
popularity…* reads `new URL(request.url).searchParams.get('title')` in its handler, so a
request that dropped the title would fail it even though the handler still answered `73`.

The 400 test submits `'x'`, not a blank title. A blank title never reaches the server — the
query is disabled while the title is blank — so the test plays a server that rejects a value
the client let through, which is the case the UI must actually handle.

*announces a rejected title submitted with Enter…* focuses the input and fires `submit` on
its form, which is what Enter in a field does — jsdom does not turn a key press into a
submit. It collects the `aria-live="polite"` regions before submitting and asserts the
message lands inside one of them, so a slot mounted only with its message fails it.

A loading test needs a handler that waits (`await delay(50)`), or the answer can arrive
before the busy indicator is ever rendered.

*speaks French…* switches the language, renders, and finds the button by its French name
(`Rechercher`); it also asserts `<html lang>` followed. One such test per screen proves the
screen reads its copy through `t()` in its own namespace. The other tests stay in English
— the setup pins `en` — so a translation change does not break a behaviour test.

## Find things the way a user does

Query by role and accessible name: `getByRole('button', { name: 'Look up' })`,
`getByLabelText('Course title')`, `findByRole('alert')`, `findByRole('status')`. The names
are the English locale's text, written out in the test rather than read from the JSON: a
test that called `t()` would pass on a key that rendered the wrong message. A test that
finds the input by its label fails when the label is no longer tied to the input, which is
an accessibility bug a class selector would never notice. Use `findBy*` for anything that
appears after a request, and `queryBy*` to assert absence.

## A fresh `QueryClient` per test

```tsx
// src/training/CoursePopularity.test.tsx
function renderScreen(): void {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <CoursePopularity />
    </QueryClientProvider>,
  )
}
```

A client shared across tests carries its cache along: a test that expects a request would
get yesterday's answer from the previous test, and pass or fail by ordering. Building one in
the render helper is cheap and makes each test start empty. Do not configure it differently
from `main.tsx` — retry policy lives on the hook, so the test exercises the real one.

## The setup that looks wrong and is not

```ts
// src/test/setup.ts
const NodeRequest = globalThis.Request
globalThis.Request = class extends NodeRequest {
  constructor(input: RequestInfo | URL, init?: RequestInit) {
    super(typeof input === 'string' ? new URL(input, window.location.href).href : input, init)
  }
}
...
server.listen({ onUnhandledFrame: 'error' })
...
await i18n.changeLanguage(DEFAULT_LANGUAGE)

afterEach(async () => {
  server.resetHandlers()
  cleanup()
  await i18n.changeLanguage(DEFAULT_LANGUAGE)
})
afterAll(() => {
  server.close()
})
```

Each odd part is load-bearing. Do not "tidy" any of them:

- **`server.listen()` at module level, not in `beforeAll`.** `openapi-fetch` captures
  `globalThis.fetch` when `createClient` runs, and `src/api/client.ts` runs it at import —
  while the test file is being imported, before any `beforeAll`. Moved into a hook, MSW
  patches `fetch` too late, the client keeps the real one, and requests escape to the
  network.
- **The `Request` subclass.** The client's `baseUrl` is `'/'`, same-origin in the browser
  (the Vite dev server proxies `/api`). Node's `Request` rejects a relative URL; the
  subclass resolves it against the jsdom origin, which `vite.config.ts` sets to
  `http://localhost/`, as a browser would. Changing `baseUrl` to an absolute URL instead
  would break the same-origin setup in development.
- **`onUnhandledFrame: 'error'`.** This is MSW 3's option (2.x called it
  `onUnhandledRequest`). A request with no handler fails the test, so a wrong path or a
  forgotten `server.use` cannot pass by accident. MSW is pinned exactly (`msw` `3.0.2` in
  `package.json`) because these option names have changed across majors.
- **`cleanup()` in `afterEach`.** `globals: false` in `vite.config.ts` means Testing
  Library cannot register its own cleanup, so the setup does it.
- **English, at load and after each test.** `i18n.ts` picks the language from
  `navigator.language`, so without the first line the suite would assert English on one
  machine and French on another. The `afterEach` puts it back after a test that switched,
  so the French test cannot leak into the next one.

## What earns a test

Every state a component renders, and every status the endpoint documents. Not: the
`trainingKeys` arrays, a primitive's CSS, or TanStack Query's own behaviour.

- **Functions with branches of their own get plain unit tests.** `unwrap` and the failure
  predicates in `src/api/problem.test.ts`; `isAskable` and `retriesOnlyUnansweredRequests`
  in `src/training/queries.test.ts`. A hook does not get a test apart from the component
  that uses it, because its behaviour is what the component shows.
- **A primitive gets a test for what it promises, not how it looks.** `TextField.test.tsx`
  checks the label, the `onChange` value and the always-mounted live error slot;
  `Button.test.tsx` the explicit `type`; `primitives.test.tsx` the role or element each
  presentational one renders. A primitive's own tests are the place for fixture copy.
- **The locales get one parity test.** `src/i18n/locales.test.ts` covers every namespace
  without being told about it (`i18n.md`).
- **A local lint rule gets a RuleTester test beside it** in `eslint/rules/`, run by vitest
  with the rest (`lint.md`).
