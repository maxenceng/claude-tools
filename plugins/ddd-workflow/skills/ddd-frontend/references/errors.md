# Errors

The backend answers every failure in one shape, from one place: a `ProblemDetail` produced
by the single `GlobalExceptionHandler`, which maps the domain's `DomainErrorStatus` to an
HTTP status. The frontend mirrors that: one error type, and one mapping from status to what
the user sees.

## One error type

```ts
// src/api/problem.ts
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) { ... }
}

/** The data of a successful call; a failed one becomes an ApiError carrying the ProblemDetail. */
export function unwrap<T>({ data, error, response }: Result<T>): T {
  if (!response.ok) {
    const detail =
      typeof error === 'object' && error !== null && 'detail' in error && typeof error.detail === 'string'
        ? error.detail
        : response.statusText
    throw new ApiError(response.status, detail)
  }
  // A success with no body (204) has no data, so a no-content route's caller gets undefined.
  return data as T
}
```

Three things to keep:

- Success is `response.ok`, not "there is data". `openapi-fetch` leaves `data` undefined for
  a 204 or an empty body, and a no-content route (a `DELETE`, a `PUT` that returns nothing)
  is still a success; `problem.test.ts` pins it.
- The error body is typed `unknown` and narrowed, not cast. A proxy or a crashed server can
  answer with HTML or an empty body; narrowing falls back to `statusText`
  (`problem.test.ts` pins both paths) instead of rendering `undefined`.
- Only an answered request becomes an `ApiError`. A network failure stays whatever `fetch`
  threw (a `TypeError`), so `error instanceof ApiError` is the test for "the server
  answered" — which is what the retry policy keys on (`queries.md`).

## Status to state

Each status means something different to the user, because each `DomainErrorStatus` means
something different to the domain:

| Status | Domain status | Means for the user | Render |
|---|---|---|---|
| 400 | `INVALID`, or an `Assert` failure | what they sent is wrong | the `detail` on the field |
| 404 | `NOT_FOUND` | nothing there (yet) | a neutral empty-like state |
| 409 | `CONFLICT` | the request is fine, the state is not | explain, and offer the next step |
| 503 | `UNAVAILABLE` | something did not answer | an alert with Retry |
| other 5xx, network | — | something broke | an alert with Retry |

The template's endpoint, `GET /api/courses/popularity`, documents 200, 400, 404 and 503
(ADR 0010). `CoursePopularity.tsx` renders each:

```tsx
// src/training/CoursePopularity.tsx — the Outcome child
if (popularity.isError) {
  const answered = popularity.error instanceof ApiError ? popularity.error : null
  if (answered?.status === 400) return null       // shown on the field instead
  if (answered?.status === 404) {
    return <p className="mt-4 text-sm text-neutral-600">No popularity yet for this course.</p>
  }
  return (
    <div role="alert" className="mt-4 text-sm text-red-700">
      <p>{answered?.detail ?? 'The server could not be reached; try again.'}</p>
      <button type="button" onClick={() => popularity.refetch()} className="mt-2 underline">
        Retry
      </button>
    </div>
  )
}
```

**400 on the field.** The message belongs where the user will fix it. The input gets
`aria-invalid` and `aria-describedby` pointing at the message, so a screen reader reads the
reason with the field. The message sits outside the `aria-live` region, so nothing would
announce it on its own: when a 400 arrives, an effect moves focus to the input, and the
screen reader reads the field, its invalid state and the message together. The
ProblemDetail names no field; see `queries.md` for forms with more than one.

**404 is not an error screen.** "This course has no popularity yet" is a fact about the
world, not a failure. Red text and `role="alert"` would tell the user something went wrong
when nothing did. Render it the way an empty list is rendered.

**409 explains and offers a way on.** The user did nothing wrong in form; the state moved
under them (a full course, a stale edit). Say what is in the way using the `detail`, and
offer the action that resolves it — reload, choose another — rather than a bare Retry that
will conflict again. The template has no 409 route yet, so no example exists in its code.

**5xx and network: alert with Retry.** The user cannot fix it and may want to try again. The
alert carries `role="alert"` so it is announced, shows the `detail` of an answered request
(the backend writes it for a person and keeps diagnostics in its logs), and offers a Retry
that calls `refetch()`. A network failure has no `detail` — only whatever `fetch` threw,
written for a developer — so the alert says, in fixed words, that the server could not be
reached. Never render `error.message` of an error that is not an `ApiError`.

## Never retry an answered request

The query retries a network failure once and an `ApiError` never — any status, 5xx
included. An automatic retry of a 503 hides the outage behind seconds of "Looking up…",
and a 4xx will answer the same way however many times it is asked. The visible Retry hands
the decision to the user, who knows whether it is worth waiting. The test
*offers a retry when the vendor is unavailable* asserts the server was called exactly once
before the alert appeared, so a reintroduced default retry fails it.

## What not to do

- Do not render `JSON.stringify(error)` or a status code. The `detail` is written for a
  person; a number is not.
- Do not catch inside `queryFn` to return a fallback value. The query then reports success,
  the four states collapse into one, and the failure is invisible.
- Do not map an error to a state by matching on the `detail` text. Status is the contract;
  wording is not.
