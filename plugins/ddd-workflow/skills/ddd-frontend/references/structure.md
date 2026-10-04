# Structure

## Context folders mirror backend contexts

`src/training/` exists because the backend has a `training` bounded context, and it is
named exactly like it. Every screen, hook and key in it speaks that context's language —
the words in `docs/glossary.md` for `training` — and talks to that context's routes.

The mirror buys three things:

- **The language stays one language.** A frontend folder named `courses` for a backend
  context named `training` is two names for one thing, and the glossary only knows one.
- **A ticket has one place to land.** A ticket is scoped to a bounded context; its
  frontend half goes in the folder of the same name, without anyone deciding.
- **The boundaries carry over.** Backend contexts reach each other only through what they
  publish. If two frontend folders imported each other freely, the UI would couple what
  the domain deliberately keeps apart, and the coupling would surface the first time one
  context's API changes.

So `architecture.test.ts` enforces it:

```ts
// src/architecture.test.ts
const sharedFolders = new Set(['api', 'design-system', 'i18n', 'test']) // not bounded contexts
...
  it('scans source files, so the rules below cannot pass on an empty list', () => {
...
  it('a bounded context never imports from another bounded context', () => {
...
  it('only src/api imports from the generated client', () => {
...
  it('the design system imports no bounded context', () => {
...
  it('the design system does not talk to the API', () => {
...
  it('i18n imports no bounded context', () => {
```

Every top-level folder of `src/` that is not in `sharedFolders` is a context. A context may
import from itself and from a shared folder, never from another context. Files directly in
`src/` (`App.tsx`, `main.tsx`) are composition: they may import any context, because
putting contexts side by side on a page is their job.

## Adding a context

1. Create `src/<context>/`, named like the backend context.
2. Add `queries.ts` with `<context>Keys` (an `all` root) and one hook per read — copy
   `src/training/queries.ts`.
3. Add the context's namespace: `src/i18n/locales/<language>/<context>.json` for every
   language, registered in `resources` in `src/i18n/i18n.ts` (`i18n.md`).
4. Add the component and its test beside it — copy `CoursePopularity.tsx` and
   `CoursePopularity.test.tsx`, composed from the design system's primitives.
5. Mount it from `App.tsx`.
6. Run `make fe-check`, then `make lint`. The architecture test, the locale parity test and
   the lint rules apply to the new folder without being told about it.

## A page that needs two contexts

Compose them in `App.tsx` (or a page component directly in `src/`), each context rendering
its own part. If one context's screen seems to need another context's data, that is the
same question the backend asks: is it one concept or two? Usually the screen belongs to a
page, not to either context. If the backend already joins the data in one route, the hook
for that route belongs to the context that owns the route.

## When to extract shared code

Shared code has these homes, and only these:

- **`src/api/`** — anything about talking to the backend: the client, `ApiError`, `unwrap`
  and the failure predicates, and `Schema<Name>` for a generated type a context needs by
  name.
- **`src/design-system/`** — every piece of UI that has a look: a button, a form field, a
  layout. It already exists, so a context never starts its own `src/ui/`; a primitive
  missing from it is added there (`design-system.md`).
- **`src/i18n/`** — the i18next setup and the locale files. It holds every context's
  namespace, but imports no context: the JSON is data, not code.
- **A deliberate shared folder** — for anything else genuinely used by more than one
  context that is neither API nor UI (a date formatter, say). Name it for what it is, and
  add it to `sharedFolders` in the same change, so the decision is visible in the diff
  rather than implied by an import.

Extract when a second context needs the same thing, not before. One use is a guess at the
abstraction; two uses show what actually varies. A look is the exception: it lands in the
design system on its first use, because a screen may not style itself — but as a variant
of an existing primitive where one fits, which keeps the guess small.

Never "share" by importing from the context that wrote it first. That import is exactly
what the architecture test forbids, and the fix is to move the code to a shared folder —
not to add the context to `sharedFolders`, which would exempt it from the rule in both
directions and stop it being a context at all. Keep shared code free of domain words:
anything that speaks one context's language belongs in that context, even if it looks
reusable — a primitive is `TextField`, never `CourseTitleField`. The locale files are the
one place a context's words sit in a shared folder, each under that context's namespace.
