# Errors

The backend answers every failure in one shape, from one place: a `ProblemDetail` produced
by the single `GlobalExceptionHandler`, which maps the domain's `DomainErrorStatus` to an
HTTP status. The frontend mirrors that: one error type, one file that reads it, and one
mapping from status to what the user sees.

## One error type

```ts
// src/api/problem.ts
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}
...
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
  threw (a `TypeError`), so "is it an `ApiError`" is the test for "the server answered" —
  which is what the retry policy keys on (`queries.md`).

## Reading a failure

Everything that asks a question of a failure lives beside `ApiError`, named for the
question:

```ts
// src/api/problem.ts
/** The statuses the client answers differently from any other failure. */
export const HttpStatus = {
  BAD_REQUEST: 400,
  NOT_FOUND: 404,
} as const

/** Whether the server answered, as opposed to the request never reaching it. */
export function isAnswered(error: unknown): error is ApiError {
  return error instanceof ApiError
}

/** Whether the server refused the request's input (400). */
export function isRejected(error: unknown): error is ApiError {
  return isAnswered(error) && error.status === HttpStatus.BAD_REQUEST
}

/** Whether the server has nothing at that address (404) — an answer, not a failure. */
export function isNotFound(error: unknown): boolean {
  return isAnswered(error) && error.status === HttpStatus.NOT_FOUND
}

/** Why the server refused the request's input, or undefined when it did not refuse it. */
export function rejectionOf(error: unknown): string | undefined {
  return isRejected(error) ? error.detail : undefined
}

/** What the server said went wrong, or undefined when nothing answered. */
export function detailOf(error: unknown): string | undefined {
  return isAnswered(error) ? error.detail : undefined
}
```

Why predicates rather than `error instanceof ApiError && error.status === 404` at the call
site:

- **A status is written once.** `404` appears in `HttpStatus` and nowhere else, so a reader
  of a component sees `isNotFound`, a word, not a number they must look up. A new status the
  client treats differently (a `409`) gets a name here and a predicate beside it.
- **The question is asked the same way everywhere.** Two components that each spell out the
  `instanceof` and the comparison will, sooner or later, spell them differently. One
  predicate is one answer.
- **They take `unknown`.** TanStack's `error` is `Error | null`; every predicate is false for
  `null` and for a non-`ApiError`, so a caller never narrows first. `isAnswered` and
  `isRejected` are type guards, so `error.detail` is typed after them.
- **They are tested on their own.** `problem.test.ts` has a *reading a failure* block that
  checks each predicate against a 400, a 404, a 503, a `TypeError` and `null`.

Add a predicate when a component would otherwise compare a status. Do not add one that only
re-wraps something the library already names — `popularity.isLoading` is TanStack's own
"pending and fetching", and wrapping it would add a name, not a meaning.

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
function Outcome({ popularity }: OutcomeProps): JSX.Element | null {
  const { t } = useTranslation('training')

  if (popularity.isLoading) return <Status>{t('popularity.lookingUp')}</Status>
  if (popularity.isPending) return null
  if (popularity.isError) {
    if (isRejected(popularity.error)) return null
    if (isNotFound(popularity.error)) {
      return (
        <Text tone="muted" size="sm">
          {t('popularity.notFound')}
        </Text>
      )
    }
    return (
      <Alert>
        <Text>{detailOf(popularity.error) ?? t('popularity.unreachable')}</Text>
        <Button type="button" variant="link" onClick={() => void popularity.refetch()}>
          {t('popularity.retry')}
        </Button>
      </Alert>
    )
  }
```

**400 on the field.** The message belongs where the user will fix it. The screen hands
`rejectionOf` to the field, and `TextField` does the rest:

```tsx
// src/training/CoursePopularity.tsx
const rejected = rejectionOf(popularity.error)
...
<TextField label={t('popularity.titleLabel')} value={draft} onChange={setDraft} error={rejected} />
```

```tsx
// src/design-system/TextField.tsx
<input
  id={inputId}
  className={styles.input}
  value={value}
  onChange={change}
  aria-invalid={invalid ? true : undefined}
  aria-describedby={invalid ? errorId : undefined}
/>
<p id={errorId} className={styles.error} aria-live="polite">
  {error}
</p>
```

The input gets `aria-invalid` and `aria-describedby` pointing at the message, so a screen
reader reads the reason with the field. The message goes in a slot that is always mounted
as `aria-live="polite"`, so it is announced when it appears, wherever focus is. Moving
focus to the input instead does not work: a title submitted with Enter already has focus
there, so nothing changes and nothing is announced. The slot is not `role="status"` — that
role belongs to the busy indicator, and the tests find it by role. The slot must exist
before the message does; a live region mounted together with its text is often not
announced. The ProblemDetail names no field; see `queries.md` for forms with more than
one.

**404 is not an error screen.** "This course has no popularity yet" is a fact about the
world, not a failure. The danger tone and `role="alert"` would tell the user something went
wrong when nothing did. Render it the way an empty list is rendered: muted `Text`.

**409 explains and offers a way on.** The user did nothing wrong in form; the state moved
under them (a full course, a stale edit). Say what is in the way using the `detail`, and
offer the action that resolves it — reload, choose another — rather than a bare Retry that
will conflict again. The template has no 409 route yet, so no example exists in its code;
the first one adds `CONFLICT: 409` to `HttpStatus` and an `isConflict` beside `isNotFound`.

**5xx and network: alert with Retry.** The user cannot fix it and may want to try again.
`Alert` carries `role="alert"` so it is announced, shows `detailOf` an answered request
(the backend writes it for a person and keeps diagnostics in its logs), and offers a Retry
that calls `refetch()`. A network failure has no `detail` — only whatever `fetch` threw,
written for a developer — so `detailOf` is `undefined` and the alert falls back to the
translated `popularity.unreachable`. Never render `error.message` of an error that is not
an `ApiError`.

The `detail` is rendered as the server wrote it, in the server's language. It is not a key
and is not looked up in the locales; only the client's own words — the fallback included —
go through `t()` (`i18n.md`).

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
- Do not compare `error.status` in a component. Name the status in `HttpStatus` and ask
  through a predicate.
