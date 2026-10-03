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
const popularity = (respond: (info: { request: Request }) => Response | Promise<Response>) =>
  server.use(http.get('*/api/courses/popularity', respond))

const problem = (status: number, detail: string) => () => HttpResponse.json({ status, detail }, { status })
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
| rejected input, announced | *announces a rejected title by moving focus to the input* |
| loading | *shows a busy indicator while the lookup is in flight* |
| loading again | *shows the busy indicator again, then the new value, on a second lookup* |

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

A loading test needs a handler that waits (`await delay(50)`), or the answer can arrive
before the busy indicator is ever rendered.

## Find things the way a user does

Query by role and accessible name: `getByRole('button', { name: 'Look up' })`,
`getByLabelText('Course title')`, `findByRole('alert')`, `findByRole('status')`. A test that
finds the input by its label fails when the label is no longer tied to the input, which is
an accessibility bug a class selector would never notice. Use `findBy*` for anything that
appears after a request, and `queryBy*` to assert absence.

## A fresh `QueryClient` per test

```tsx
function ask(title: string) {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <CoursePopularity />
    </QueryClientProvider>,
  )
  ...
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

server.listen({ onUnhandledFrame: 'error' })
afterEach(() => {
  server.resetHandlers()
  cleanup()
})
afterAll(() => server.close())
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

## What earns a test

Every state a component renders, and every status the endpoint documents. Not: the
`trainingKeys` arrays, a component's class names, or TanStack Query's own behaviour. `unwrap`
gets plain unit tests (`src/api/problem.test.ts`) because it has branches of its own;
a hook does not get a test apart from the component that uses it, because its behaviour is
what the component shows.
