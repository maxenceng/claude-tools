# ddd-frontend skill and a frontend worked example

`ddd-backend` works because the template has a real example to read: its first rule is
"read the neighbour first; where this document and the code differ, the code wins." The
frontend has no neighbour — `App.tsx` says "No context yet", the smoke test asks to be
deleted, and `docs/openapi.json` has no paths because `training` has no HTTP endpoint
(ADR 0008 kept it that thin on purpose, and said the next demonstration reopens the
trade-off).

This change gives the frontend a neighbour, then writes the skill that describes it.

## Part 1 — one read endpoint in `training` (template backend)

- `GET /api/courses/popularity?title=…`
  - `CoursePopularityController` in `training.infrastructure.primary`, returning
    `CoursePopularityResponse(String title, int popularity)` mapped by `from(...)`.
  - `CoursePopularityApplicationService` in `training.application`: builds `Title`, calls
    `CourseCataloguePort.lookup`, throws when empty. No rules.
- Outcomes, all through the one global handler:

  | Case | Status | Mechanism |
  |---|---|---|
  | blank title | 400 | `Title`'s `Assert` → `AssertionException` (exists) |
  | vendor has no popularity | 404 | new `PopularityNotFoundException`, `DomainErrorStatus.NOT_FOUND` |
  | vendor unreachable | 503 | new `DomainErrorStatus.UNAVAILABLE` → `HttpStatus.SERVICE_UNAVAILABLE` |

- `CourseCatalogueUnreachableException` becomes a `DomainException` with `UNAVAILABLE`,
  and its Javadoc changes accordingly: a controller is now the caller, and
  `references/outbound-clients.md` prescribes exactly this for a controller-triggered
  lookup. `DomainErrorStatus` gaining a value is a change to the shared error kernel;
  `ddd-backend`'s *Errors* section gets one line for `UNAVAILABLE` ("a dependency did not
  answer; retrying later may work").
- `@ApiResponse` for 200/400/404/503; recapture `docs/openapi.json` and the generated
  client (`make run`, `make openapi`, `make openapi-client`).
- Tests: controller slice test for all four outcomes; application-service test; existing
  `ArchitectureTest`/`ModularityTest` stay green.
- ADR 0010 extends ADR 0008: `training` now also demonstrates one HTTP read endpoint,
  still without persistence, so the frontend has a real contract. Template `CLAUDE.md`,
  `docs/context-map.md` and `docs/glossary.md` updated where they describe `training`.

## Part 2 — the frontend worked example (template `frontend/src/`)

```
api/client.ts                 exists — the openapi-fetch client
api/problem.ts                ProblemDetail → ApiError (status, detail); unwrap() throws it on a failed call
training/                     one folder per backend bounded context
  queries.ts                  trainingKeys factory + useCoursePopularity(title)
  CoursePopularity.tsx        title input → loading / not found / unavailable + retry / value
  CoursePopularity.test.tsx   one test per state, network mocked with MSW
architecture.test.ts          context folders never import each other; api/generated only through api/
App.tsx                       renders <CoursePopularity/>
```

- Query keys come from a per-context factory (`trainingKeys.popularity(title)`), never
  inline arrays.
- The query does not retry a 4xx; a 503 shows a visible Retry rather than silent retries.
  The query is disabled while the title is blank.
- Status → UI: 400 shows the backend's `detail` under the input; 404 is a normal "no
  popularity yet" state, not an error screen; 503 is an error with Retry.
- `architecture.test.ts` is a small Vitest test parsing import specifiers under `src/` —
  the frontend's `ArchitectureTest`, with no ESLint added. It must be shown to fail on a
  planted cross-context import before it is trusted.
- MSW is the one new devDependency, pinned exactly; tests mock the network, not the
  client, so the real generated types and fetch path run.
- `App.test.tsx` (the self-declared temporary smoke test) is deleted.
- The screen passes `make fe-ci`, including impeccable's `design-check`.

## Part 3 — the skill and its wiring

```
plugins/ddd-workflow/skills/ddd-frontend/
  SKILL.md               rules only, short
  references/
    queries.md           key factories, hooks, retry policy, mutations + invalidation
                         (mutations not demonstrated in the template — the file says so)
    errors.md            ProblemDetail → ApiError, status → UI state, why 404 is not an error screen
    tests.md             MSW at the network boundary, one test per state, what not to test
    structure.md         folder per context, the import rules and why, when to split a component
```

`SKILL.md` sections: *Read the neighbour first* (copy `training/`), *The API boundary*
(moved from the agent), *Layout*, *Server state*, *Errors*, *The four states*, *Tests*,
*Design* (defer to *Design direction* and `/ticket design`; impeccable owns appearance),
*Frequent mistakes*. Each a few lines of rule plus a pointer to its reference.

Wiring:
- `agents/frontend.md`: "Invoke the `ddd-frontend` skill before writing code", like
  `backend-ddd`; conventions move out, the agent keeps role, contract boundary and
  verification.
- `vercel-react-best-practices` and `vercel-composition-patterns` added to
  `verify-plugin.sh`'s `NON_PLUGIN_SKILLS`, install
  `npx skills add vercel-labs/agent-skills@<name> -g`. The skill invokes them when
  installed and says once that they are missing otherwise — advisory, not required.
  Their Next.js/server-only rules do not apply to this Vite SPA, and the skill says so.
- Template `frontend/CLAUDE.md` shrinks to commands plus a pointer to the skill (it is
  always resident).
- README and HOWTO: the skill, and the optional Vercel installs.
- `ddd-workflow` 2.0.0 → 2.1.0.

## Verification

`make -C templates/spring-ddd verify`, `./scripts/verify-archetype.sh`,
`./scripts/verify-plugin.sh`, `./scripts/check-plugin-version-bump.sh main`.

## Out of scope

- A mutation example in the template (needs persistence — its own ADR).
- Routing (one screen), a component library.
