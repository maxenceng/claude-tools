# Queries and server state

TanStack Query is the cache of what the server said. Everything below follows from treating
it as the only copy.

## One owner per piece of state

Server state is owned by TanStack Query; local state by `useState`. `CoursePopularity.tsx`
has both, and keeps them apart:

```tsx
// src/training/CoursePopularity.tsx
const [draft, setDraft] = useState('')
const [submitted, setSubmitted] = useState('')
const popularity = useCoursePopularity(submitted)
```

What the user typed (`draft`) and what they asked for (`submitted`) are local. The answer
is not: it is never put into `useState`, because then there are two copies, and the moment
the query refetches, retries or is invalidated, the local copy is the stale one and nothing
says so. Deriving
from the query result on each render costs nothing and cannot drift.

## The key factory

```ts
// src/training/queries.ts
export const trainingKeys = {
  all: ['training'] as const,
  popularity: (title: string) => [...trainingKeys.all, 'popularity', title] as const,
}
```

Every key in a context starts with `trainingKeys.all`, so one call can invalidate the whole
context — which is what a mutation needs (below). A key written inline as
`['training', 'popularity', title]` works until someone renames a segment in one place;
then invalidation silently misses it and the screen shows stale data with no error. The
factory makes the key a name the compiler checks.

**Why `as const`.** Without it, `['training']` is a `string[]`: mutable, any length, any
strings. With it, it is `readonly ['training']`, and `popularity(title)` is
`readonly ['training', 'popularity', string]`. That buys two things. A key cannot be
pushed to or reassigned after it is built, so the key a query was cached under is the key
a later invalidation names. And the tuple type carries each segment, so
`invalidateQueries({ queryKey: trainingKeys.all })` is checked against the same literal the
reads start with. It is TanStack Query's documented key-factory pattern, and the only
`as const` a context should need.

A new context adds its own `<context>Keys` with an `all` root. Never reuse another
context's factory — that is a cross-context import, and `architecture.test.ts` rejects it.

## One hook per read

```ts
// src/training/queries.ts
/** A network failure is retried once, silently, before the screen offers Retry. */
export const NETWORK_RETRIES = 1
...
/** Whether a title is worth asking about; a blank one is not sent at all. */
export function isAskable(title: string): boolean {
  return title.trim() !== ''
}

/**
 * Retries only a request nobody answered. When the server answered, the
 * answer stands and the screen offers Retry instead.
 */
export function retriesOnlyUnansweredRequests(failureCount: number, error: Error): boolean {
  return !isAnswered(error) && failureCount < NETWORK_RETRIES
}

export function useCoursePopularity(title: string): UseQueryResult<Schema<'CoursePopularityResponse'>> {
  return useQuery({
    queryKey: trainingKeys.popularity(title),
    queryFn: async () =>
      unwrap(await api.GET('/api/courses/popularity', { params: { query: { title } } })),
    enabled: isAskable(title),
    retry: retriesOnlyUnansweredRequests,
  })
}
```

Each choice here is a convention:

- **The hook owns the request.** A component never calls `api` itself, so the key, the
  `unwrap` and the retry policy are decided once, and a second component asking the same
  thing shares the cache entry rather than inventing a second key.
- **`unwrap` on every call.** `openapi-fetch` returns `{ data, error, response }`; left as
  is, every component would re-decide what a failure looks like. `unwrap` turns it into data
  or an `ApiError` (see `errors.md`), so `isError` means the same thing everywhere.
- **Conditions are named.** `enabled: title.trim() !== ''` says what it computes, not why;
  `enabled: isAskable(title)` says why, and the reason sits in its TSDoc. The same goes
  for `retry`: an inline `(failures, error) => …` lambda with a bare `1` in it becomes
  `retriesOnlyUnansweredRequests` and `NETWORK_RETRIES`. Both are exported so
  `queries.test.ts` can test them directly, on blank and padded titles and on an
  `ApiError` against a `TypeError` — cheaper and sharper than driving them through a
  rendered screen.
- **`enabled` for input the server would reject.** A blank title would only earn a 400, so
  the query does not run; the component renders the *idle* state instead. This is also why
  the template's 400 cannot come from a blank title in the UI — it is the server's last word
  on a value the client let through.
- **`retry` only for a network failure.** TanStack retries three times by default. An
  `ApiError` means the server answered, and asking again a few hundred milliseconds later
  rarely changes a 404 or a 400 — it only delays the message by seconds. Even a 503 is left
  to the user: the alert's Retry button is visible and they decide when. A network failure
  (no answer at all) gets `NETWORK_RETRIES` silent retries, because a dropped connection
  often is transient.
- **No `keepPreviousData`.** It keeps the last answer on screen while a new key loads, which
  hid the loading state on every lookup after the first: the user saw the old number and no
  sign anything was happening. Without it each new key starts at `isPending`, and the screen
  says "Looking up…" again.
- **An explicit return type.** `UseQueryResult<Schema<'CoursePopularityResponse'>>` states
  what the hook promises, so a schema change surfaces at the hook rather than in whichever
  component reads the field. `Schema<Name>` comes from `src/api/client.ts`, so the hook
  names a generated type without importing `generated/`, which only `src/api/` may do.

`CoursePopularity.tsx` names the hook's result as `ReturnType<typeof useCoursePopularity>`
for its `Outcome` child. If a context needs a schema type by name, use `Schema<'Name'>`;
never hand-write a copy of it.

## Mutations

> **Unverified by the template's build.** The template has no mutation yet — ADR 0010 gives
> `training` one read endpoint and nothing else, and a write needs persistence and its own
> ADR. This section describes the shape the first one should take; the first context to add
> a write should check it against reality and correct this file.

A write is a hook in the same `queries.ts`, beside the reads it affects:

```ts
// shape only — no such endpoint exists in the template
interface CourseRename {
  id: string
  title: string
}

export function useRenameCourse(): UseMutationResult<Schema<'CourseResponse'>, Error, CourseRename> {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, title }: CourseRename) =>
      unwrap(await api.PUT('/api/courses/{id}', { params: { path: { id } }, body: { title } })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: trainingKeys.all }),
  })
}
```

- **Invalidate a prefix on success.** `trainingKeys.all` marks every training query stale,
  and the ones on screen refetch. Narrowing to the one key that obviously changed is how a
  list somewhere else keeps showing the old title; widen first, narrow only when a refetch
  is measurably expensive. Do not hand-write the server's answer into the cache with
  `setQueryData` unless the response is exactly what the read would return.
- **No retry.** `useMutation` does not retry by default; keep it that way. A write the
  server answered must not be sent twice, and one that timed out may have landed.
- **Map a 400 onto the form.** The `ProblemDetail` carries a `detail` and no field name, so
  a one-field form passes `rejectionOf(mutation.error)` to that field's `TextField` `error`,
  exactly as `CoursePopularity.tsx` does for its title; a form with several fields shows it
  once at form level, tied to the form. Do not parse field names out of the message — that
  is the backend's wording, not its contract. If the UI needs per-field errors, the backend
  should add them to the schema.
- **409 is not a validation error.** The input was fine; the state was not. Explain it and
  offer the next step (reload, pick another) — see `errors.md`.
- **Keep the form's draft in `useState`** until success, so a rejected submit loses nothing
  the user typed.
