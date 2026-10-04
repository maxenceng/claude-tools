# ddd-frontend Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the template frontend a real worked example (backed by one new read endpoint in `training`), then write the `ddd-frontend` skill that describes it and wire the `frontend` agent to it.

**Architecture:** Backend first (endpoint + contract), so the frontend has a generated client to build against; frontend example second; the skill third, written from the example that now exists; docs and version last.

**Tech Stack:** Spring Boot 4 / Java 25, springdoc, JUnit 5 + Mockito + AssertJ; React 19 + TypeScript + Vite + TanStack Query 5 + openapi-fetch, Vitest + Testing Library + MSW; markdown skill files.

**Spec:** `docs/superpowers/specs/2026-10-03-ddd-frontend-design.md`

## Global Constraints

- Endpoint: `GET /api/courses/popularity?title=<string>` → 200 `{"title": string, "popularity": int}`; 400 blank title; 404 no popularity; 503 vendor unreachable. All errors are `ProblemDetail` from the one `GlobalExceptionHandler`.
- New enum value `DomainErrorStatus.UNAVAILABLE` → `HttpStatus.SERVICE_UNAVAILABLE`.
- New ADR number: `0010`.
- MSW pinned exactly (`npm install --save-dev --save-exact msw@3.0.2`, or the current version if 3.0.2 is gone — record the version used).
- Frontend context folder is `src/training/`; query keys only via `trainingKeys`.
- New skill name: `ddd-frontend`; files under `plugins/ddd-workflow/skills/ddd-frontend/`.
- Non-plugin skills added to `NON_PLUGIN_SKILLS`: `vercel-react-best-practices` → `npx skills add vercel-labs/agent-skills@vercel-react-best-practices -g`; `vercel-composition-patterns` → `npx skills add vercel-labs/agent-skills@vercel-composition-patterns -g`.
- `ddd-workflow` version `2.0.0` → `2.1.0`, once, in the last task.
- Never hand-edit `templates/spring-ddd-archetype/` or `frontend/src/api/generated/`.
- Every commit ends with a blank line then `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Match the neighbouring code: read the closest existing file of the same kind before writing one, and name it in the report.

---

### Task 1: The popularity endpoint in `training`

**Files** (all under `templates/spring-ddd/`, package root `src/main/java/com/example/app/`):
- Modify: `error/domain/DomainErrorStatus.java` (add `UNAVAILABLE`)
- Modify: `error/infrastructure/primary/GlobalExceptionHandler.java` (map it)
- Modify: `training/infrastructure/secondary/client/CourseCatalogueUnreachableException.java` (extend `DomainException`)
- Create: `training/domain/PopularityNotFoundException.java`
- Create: `training/application/CoursePopularityApplicationService.java`
- Create: `training/infrastructure/primary/CoursePopularityController.java`, `CoursePopularityResponse.java`
- Create tests: `src/test/java/com/example/app/training/application/CoursePopularityApplicationServiceTest.java`, `src/test/java/com/example/app/training/infrastructure/primary/CoursePopularityControllerTest.java`
- Modify: `docs/openapi.json`, `frontend/src/api/generated/schema.d.ts` (regenerated, never hand-edited)
- Create: `docs/adr/0010-training-demonstrates-one-http-read-endpoint.md`
- Modify: `CLAUDE.md`, `docs/context-map.md`, `docs/glossary.md` where they describe `training`
- Modify: `plugins/ddd-workflow/skills/ddd-backend/SKILL.md` *Errors* section (repo root path)

**Interfaces:**
- Produces: the endpoint contract above, present in `docs/openapi.json` and the generated `paths` type as `/api/courses/popularity`.

- [ ] **Step 1: Write the failing application-service test**

```java
package com.example.app.training.application;

import static com.example.app.training.domain.PopularityFixture.popularity;
import static com.example.app.training.domain.TitleFixture.title;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

import java.util.Optional;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.example.app.training.domain.CourseCataloguePort;
import com.example.app.training.domain.PopularityNotFoundException;

@ExtendWith(MockitoExtension.class)
class CoursePopularityApplicationServiceTest {

    @Mock
    private CourseCataloguePort catalogue;

    @Test
    void shouldAnswerThePopularityTheCatalogueHas() {
        CoursePopularityApplicationService service = new CoursePopularityApplicationService(catalogue);
        when(catalogue.lookup(title())).thenReturn(Optional.of(popularity()));

        assertThat(service.popularityOf(title())).isEqualTo(popularity());
    }

    @Test
    void shouldRefuseWhereTheCatalogueHasNone() {
        CoursePopularityApplicationService service = new CoursePopularityApplicationService(catalogue);
        when(catalogue.lookup(title())).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.popularityOf(title())).isInstanceOf(PopularityNotFoundException.class);
    }
}
```

Match the import grouping/order of `CourseManagerTest` and whatever `TestConventionsTest`/`ImportsAreExplicitTest` require (run them).

- [ ] **Step 2: Run it — expect a compile failure**

Run: `make test-one T=CoursePopularityApplicationServiceTest`
Expected: FAIL, `CoursePopularityApplicationService` / `PopularityNotFoundException` not found.

- [ ] **Step 3: Implement the domain exception and the service**

`training/domain/PopularityNotFoundException.java`:

```java
package com.example.app.training.domain;

import com.example.app.error.domain.DomainErrorStatus;
import com.example.app.error.domain.DomainException;

/** The catalogue vendor has no popularity for this title — yet; it may supply one later. */
public class PopularityNotFoundException extends DomainException {

    public PopularityNotFoundException(Title title) {
        super(DomainErrorStatus.NOT_FOUND, "No popularity for \"" + title.value() + "\" yet");
    }
}
```

`training/application/CoursePopularityApplicationService.java`:

```java
package com.example.app.training.application;

import org.springframework.stereotype.Service;

import com.example.app.training.domain.CourseCataloguePort;
import com.example.app.training.domain.Popularity;
import com.example.app.training.domain.PopularityNotFoundException;
import com.example.app.training.domain.Title;

@Service
public class CoursePopularityApplicationService {

    private final CourseCataloguePort catalogue;

    public CoursePopularityApplicationService(CourseCataloguePort catalogue) {
        this.catalogue = catalogue;
    }

    public Popularity popularityOf(Title title) {
        return catalogue.lookup(title).orElseThrow(() -> new PopularityNotFoundException(title));
    }
}
```

Adjust visibility, Javadoc and comment density to what `ArchitectureTest`, `TestConventionsTest` and the `ddd-backend` skill's *Visibility* and *Comments* sections require — read them first.

- [ ] **Step 4: Run it — expect PASS**

Run: `make test-one T=CoursePopularityApplicationServiceTest`

- [ ] **Step 5: Add `UNAVAILABLE` and make the unreachable exception a `DomainException`**

In `DomainErrorStatus`, after `INVALID`:

```java
    /** Something this depends on did not answer; the same request may work later. */
    UNAVAILABLE,
```

In `GlobalExceptionHandler.statusOf`, add `case UNAVAILABLE -> HttpStatus.SERVICE_UNAVAILABLE;`.

`CourseCatalogueUnreachableException` extends `DomainException` with `DomainErrorStatus.UNAVAILABLE`. `DomainException` has only `(status, message)`; add a second protected constructor `(DomainErrorStatus status, String message, Throwable cause)` calling `super(message, cause)` so the cause is kept. Rewrite its Javadoc: a controller now calls this lookup, so per `ddd-backend`'s `references/outbound-clients.md` it is a `DomainException` with `UNAVAILABLE`; keep the ADR 0009 reference. Keep `CourseCatalogueClientTest` green (`make test-one T=CourseCatalogueClientTest`).

- [ ] **Step 6: Write the failing controller test**

`CoursePopularityControllerTest` — a web slice test with the application service mocked. Spring Boot 4 moved the slice: use `org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest` and `org.springframework.test.context.bean.override.mockito.MockitoBean`; if the slice annotation does not resolve, add test-scoped `org.springframework.boot:spring-boot-starter-webmvc-test` to `pom.xml`. Four tests:

```java
@Test
void shouldAnswerThePopularity() throws Exception {
    when(service.popularityOf(title())).thenReturn(popularity());

    mvc.perform(get("/api/courses/popularity").param("title", title().value()))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.title").value(title().value()))
        .andExpect(jsonPath("$.popularity").value(popularity().value()));
}

@Test
void shouldRefuseABlankTitle() throws Exception {
    mvc.perform(get("/api/courses/popularity").param("title", " "))
        .andExpect(status().isBadRequest());
}

@Test
void shouldAnswerNotFoundWhereThereIsNoPopularity() throws Exception {
    when(service.popularityOf(title())).thenThrow(new PopularityNotFoundException(title()));

    mvc.perform(get("/api/courses/popularity").param("title", title().value()))
        .andExpect(status().isNotFound());
}

@Test
void shouldAnswerUnavailableWhereTheCatalogueIsUnreachable() throws Exception {
    when(service.popularityOf(title())).thenThrow(new CourseCatalogueUnreachableException("down", null));

    mvc.perform(get("/api/courses/popularity").param("title", title().value()))
        .andExpect(status().isServiceUnavailable());
}
```

The 404/503 tests prove the global handler is in the slice (`@WebMvcTest` loads `@RestControllerAdvice`; if it does not, `@Import(GlobalExceptionHandler.class)` — it is package-private, so check `ArchitectureTest` before changing its visibility and prefer the import route that does not).

Note: the controller test lives in `training.infrastructure.primary` and must not import `training.infrastructure.secondary..` if `ArchitectureTest` forbids primary→secondary; if it does, construct the 503 case with a test-local `DomainException` subclass carrying `UNAVAILABLE` instead, and say so in the report.

- [ ] **Step 7: Run it — expect FAIL (no controller)**

Run: `make test-one T=CoursePopularityControllerTest`

- [ ] **Step 8: Implement the controller and response**

```java
@RestController
@RequestMapping("/api/courses")
class CoursePopularityController {

    private final CoursePopularityApplicationService popularities;

    CoursePopularityController(CoursePopularityApplicationService popularities) {
        this.popularities = popularities;
    }

    @GetMapping("/popularity")
    @Operation(summary = "A course's popularity, as the training catalogue vendor reports it")
    @ApiResponse(responseCode = "200", description = "The vendor has a popularity for this title")
    @ApiResponse(responseCode = "400", description = "The title is blank",
        content = @Content(schema = @Schema(implementation = ProblemDetail.class)))
    @ApiResponse(responseCode = "404", description = "The vendor has no popularity for this title yet",
        content = @Content(schema = @Schema(implementation = ProblemDetail.class)))
    @ApiResponse(responseCode = "503", description = "The vendor did not answer",
        content = @Content(schema = @Schema(implementation = ProblemDetail.class)))
    CoursePopularityResponse popularity(@RequestParam String title) {
        Title asked = new Title(title);
        return CoursePopularityResponse.from(asked, popularities.popularityOf(asked));
    }
}
```

```java
record CoursePopularityResponse(String title, int popularity) {

    static CoursePopularityResponse from(Title title, Popularity popularity) {
        return new CoursePopularityResponse(title.value(), popularity.value());
    }
}
```

Read `ddd-backend`'s *The HTTP contract* section first: every documented failure code must be one the global handler emits (they are). Match annotations/visibility to `ArchitectureTest`.

- [ ] **Step 9: Run the whole backend suite**

Run: `make test` then `make ci`
Expected: PASS, including `ArchitectureTest`, `ModularityTest`, `TestConventionsTest`, `ImportsAreExplicitTest`, PMD and Spotless (`make fmt` first if formatting fails).

- [ ] **Step 10: Recapture the contract**

```bash
make run          # background; wait until it answers
make openapi
make openapi      # second capture; must produce no diff
git diff --stat docs/openapi.json
make openapi-client
```

Expected: `docs/openapi.json` gains `/api/courses/popularity` with 200/400/404/503 and the response schema; `frontend/src/api/generated/schema.d.ts` gains the path. Stop the app afterwards. Run `make openapi-check` if the app is still running.

- [ ] **Step 11: ADR 0010 and template docs**

`docs/adr/0010-training-demonstrates-one-http-read-endpoint.md`, in ADR 0008's format (Date 2026-10-03, Status Accepted, Context/Decision/Consequences): the frontend had no neighbour to copy, so `training` gains one read endpoint and nothing else — still no persistence, no mutation (that needs persistence and its own ADR); `DomainErrorStatus` gains `UNAVAILABLE` because a controller now waits on the vendor; reopens and extends ADR 0008 for HTTP only. Update `CLAUDE.md`, `docs/context-map.md` and `docs/glossary.md` wherever they say `training` has no controller/endpoint. Run `make adr-check`.

In `plugins/ddd-workflow/skills/ddd-backend/SKILL.md` *Errors*: extend the enum snippet to `{ NOT_FOUND, CONFLICT, INVALID, UNAVAILABLE }` and add one sentence: `UNAVAILABLE` when something the request depends on did not answer — retrying later may work, and it is nobody's input error.

- [ ] **Step 12: Commit**

```bash
git add templates/spring-ddd plugins/ddd-workflow/skills/ddd-backend/SKILL.md
git commit -m "spring-ddd: training answers a course's popularity over HTTP (ADR 0010)"
```

---

### Task 2: The frontend worked example

**Files** (under `templates/spring-ddd/frontend/`):
- Create: `src/api/problem.ts`, `src/training/queries.ts`, `src/training/CoursePopularity.tsx`, `src/training/CoursePopularity.test.tsx`, `src/architecture.test.ts`, `src/test/server.ts`, `src/test/setup.ts`
- Modify: `src/App.tsx`, `vite.config.ts` (`test.setupFiles`), `package.json` + lockfile (msw)
- Delete: `src/App.test.tsx`

**Interfaces:**
- Consumes: `paths['/api/courses/popularity']` from the generated client (Task 1).
- Produces (Task 3 describes these by name): `ApiError` class with `status: number` and `detail: string`; `unwrap<T>(result): T` throwing `ApiError`; `trainingKeys` with `all` and `popularity(title)`; `useCoursePopularity(title)`; component `CoursePopularity`.

- [ ] **Step 1: Install MSW and wire the test server**

```bash
cd templates/spring-ddd/frontend
npm install --save-dev --save-exact msw@3.0.2
```

`src/test/server.ts`:

```ts
import { setupServer } from 'msw/node'

export const server = setupServer()
```

`src/test/setup.ts`:

```ts
import { afterAll, afterEach, beforeAll } from 'vitest'
import { cleanup } from '@testing-library/react'
import { server } from './server'

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => {
  server.resetHandlers()
  cleanup()
})
afterAll(() => server.close())
```

In `vite.config.ts` `test`, add `setupFiles: ['./src/test/setup.ts']`. If MSW's API differs in the installed major (check its README for `setupServer`/`http`/`HttpResponse`), adapt and record it. If jsdom's `fetch`/relative URL makes `openapi-fetch` with `baseUrl: '/'` fail under MSW, set the test environment URL (`environmentOptions: { jsdom: { url: 'http://localhost/' } }`) rather than changing `client.ts`.

- [ ] **Step 2: Write the failing architecture test**

`src/architecture.test.ts`: read every `.ts`/`.tsx` under `src/` (excluding `src/api/generated/`), extract import specifiers with a regex over `from '…'` and `import('…')`, resolve relative ones against the file's directory, and assert:
1. a file in `src/<context>/` (any top-level folder other than `api`, `test`) never imports from another `src/<other-context>/`;
2. only files in `src/api/` import from `src/api/generated/`.

Each rule is its own `it(...)` naming the rule; failures list `file → import`. Use `node:fs`/`node:path` (`import.meta.dirname` or `fileURLToPath(new URL('.', import.meta.url))`).

Prove it bites: temporarily add `import '../training/queries'` to a throwaway `src/other/x.ts` and an import of `../api/generated/schema` from `src/training/`, run `npx vitest run src/architecture.test.ts`, expect both rules to FAIL naming those files, then delete the throwaway lines.

- [ ] **Step 3: `src/api/problem.ts` with its test**

```ts
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

type Result<T> = { data?: T; error?: unknown; response: Response }

/** The data of a successful call; a failed one becomes an ApiError carrying the ProblemDetail. */
export function unwrap<T>({ data, error, response }: Result<T>): T {
  if (error !== undefined || data === undefined) {
    const detail =
      typeof error === 'object' && error !== null && 'detail' in error && typeof error.detail === 'string'
        ? error.detail
        : response.statusText
    throw new ApiError(response.status, detail)
  }
  return data
}
```

`src/api/problem.test.ts`: success returns data; a ProblemDetail body becomes `ApiError` with its status and `detail`; a body without `detail` falls back to `statusText`. Run `npx vitest run src/api` — PASS.

- [ ] **Step 4: Write the failing component test**

`src/training/CoursePopularity.test.tsx` — render inside a fresh `QueryClient` per test (`retry` left to the hook's own policy), type a title with `@testing-library/react` (`fireEvent.change`, no new dependency), and one test per state:
- populated: 200 `{ title, popularity: 73 }` → shows `73`;
- not found: 404 ProblemDetail → shows a neutral "no popularity yet" message, not an alert;
- unavailable: 503 → shows an alert with a Retry button; clicking it after `server.use` swaps in a 200 shows the value;
- invalid: 400 ProblemDetail with `detail: "title must not be blank"` → shows that detail tied to the input (`aria-describedby`);
- loading: a delayed handler shows a busy indicator (`role="status"` or `aria-busy`).

Handlers use `http.get('*/api/courses/popularity', …)`. Run: FAIL (no component).

- [ ] **Step 5: `src/training/queries.ts`**

```ts
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { ApiError, unwrap } from '../api/problem'

export const trainingKeys = {
  all: ['training'] as const,
  popularity: (title: string) => [...trainingKeys.all, 'popularity', title] as const,
}

export function useCoursePopularity(title: string) {
  return useQuery({
    queryKey: trainingKeys.popularity(title),
    queryFn: async () =>
      unwrap(await api.GET('/api/courses/popularity', { params: { query: { title } } })),
    enabled: title.trim() !== '',
    retry: (failures, error) => !(error instanceof ApiError && error.status < 500) && failures < 1,
    placeholderData: keepPreviousData,
  })
}
```

Remove `keepPreviousData` if the tests show it masks a state transition; say so in the report.

- [ ] **Step 6: `src/training/CoursePopularity.tsx` and `App.tsx`**

A labelled title input (debounce not required — submit on a form `onSubmit` so a query fires per submitted title, not per keystroke), and one branch per state from `useCoursePopularity`: idle (nothing asked yet), loading, populated, 404 → neutral message, 400 → detail under the input via `aria-describedby`, other errors → `role="alert"` with a Retry `<button>` calling `refetch()`. Semantic HTML, Tailwind classes in the style of the current `App.tsx`; no new dependencies. Keep it to one screen of code; split presentation from the hook call if it grows past that.

`App.tsx` keeps its `<main>` and heading, drops the "No context yet" paragraph, and renders `<CoursePopularity />`. Delete `src/App.test.tsx` (its own comment asks for this once a real screen exists).

- [ ] **Step 7: Run the frontend pipeline**

Run: `make -C templates/spring-ddd/frontend ci`
Expected: typecheck, tests (architecture, problem, component), dup, `design-check` (impeccable) and build all PASS. Fix any impeccable finding in the component rather than ignoring it.

- [ ] **Step 8: Commit**

```bash
git add templates/spring-ddd/frontend
git commit -m "spring-ddd: the frontend gets a worked example — training's course popularity"
```

---

### Task 3: The `ddd-frontend` skill and its wiring

**Files:**
- Create: `plugins/ddd-workflow/skills/ddd-frontend/SKILL.md`, `references/queries.md`, `references/errors.md`, `references/tests.md`, `references/structure.md`
- Modify: `plugins/ddd-workflow/agents/frontend.md`
- Modify: `scripts/verify-plugin.sh` (`NON_PLUGIN_SKILLS`)
- Modify: `templates/spring-ddd/frontend/CLAUDE.md`

**Interfaces:**
- Consumes: the files and names Task 2 produced — read them; the skill describes them and must not contradict them.

- [ ] **Step 1: Write `SKILL.md`**

Frontmatter: `name: ddd-frontend`; `description: Conventions for writing frontend code in a DDD project's React + TypeScript client — a context's folder, its queries, error states and tests, against the generated OpenAPI client. Load before writing or restructuring frontend code.`

Model it on `plugins/ddd-workflow/skills/ddd-backend/SKILL.md` (read it first: voice, opening, "the code wins"). Rules only, each section a few lines plus a pointer to its reference. Sections and the rules each must state:

- **Read the neighbour first** — copy `src/training/`; where this skill and the code differ, the code wins; name the file matched in the report.
- **The API boundary** — the generated client is the whole truth; never edit `src/api/generated/`; never read backend source; regenerate in two steps (`make openapi`, then `make openapi-client`); only `src/api/` imports `generated/` (enforced by `architecture.test.ts`).
- **Layout** — one folder per backend bounded context under `src/`, named like it; contexts never import each other (enforced); shared code lives in `src/api/` or a deliberate shared folder, not in another context. → `references/structure.md`
- **Server state** — TanStack Query owns it, `useState` owns local state, never copy one into the other; keys only from the context's `<context>Keys` factory; one hook per server read, in `<context>/queries.ts`; every call goes through `unwrap`. → `references/queries.md`
- **Errors** — failures are `ApiError` (status + ProblemDetail `detail`); map status to state: 400 → message on the field, 404 → a normal empty-like state, 409 → explain and offer what to do, 5xx → alert with Retry; never retry a 4xx. → `references/errors.md`
- **The four states** — loading, empty/not found, error, populated, each rendered and each tested; plus idle where the query waits on input.
- **Tests** — MSW at the network boundary, never mock the client or the hook; one test per state; query by role/label; a fresh `QueryClient` per test. → `references/tests.md`
- **Design** — appearance follows the ticket's *Design direction* and `/ticket design`; `make fe-ci` runs impeccable's detector; do not restyle outside the ticket.
- **General React advice** — invoke the `vercel-react-best-practices` skill and the `vercel-composition-patterns` skill when installed; if not, say once and continue. Their Next.js / React Server Component / server-fetching rules do not apply to this Vite SPA.
- **Frequent mistakes** — inline query key arrays; `any` instead of `unknown` + narrowing; redeclared API types; an error screen for a 404; a test that mocks `api.GET`; a component that fetches and renders in one function past one screen.

- [ ] **Step 2: Write the four references**

Each explains the *why* behind its section's rules with code excerpts copied from the Task 2 files (cite paths). `queries.md` also covers mutations — `useMutation`, invalidating `trainingKeys.all`-style prefixes on success, mapping a 400 onto form fields — and states plainly that the template has no mutation yet (ADR 0010), so this part is unverified by its build. `structure.md` explains why context folders mirror backend contexts and when to extract shared code.

- [ ] **Step 3: Allow the Vercel skills in the checker — red first**

Run: `./scripts/verify-plugin.sh`
Expected: FAIL naming `vercel-react-best-practices` / `vercel-composition-patterns` as undefined.

Add both to `NON_PLUGIN_SKILLS` with the install lines from Global Constraints. Run again: PASS; `external:` lists both with their install lines and lists no `ddd-frontend` (it is now a local skill).

- [ ] **Step 4: Rewire the `frontend` agent**

In `plugins/ddd-workflow/agents/frontend.md`, mirror `backend-ddd.md`: right after the opening line, "Invoke the `ddd-frontend` skill before writing code. It carries the conventions; this prompt only carries the judgement." Remove the *Conventions* and *Accessibility and appearance* bodies now covered by the skill (keep a one-line pointer if the agent would otherwise lose a rule the skill lacks — check each against SKILL.md). Keep *The contract boundary* regeneration warning short and keep *Verifying* unchanged. Frontmatter unchanged.

- [ ] **Step 5: Shrink the template's `frontend/CLAUDE.md`**

Keep the title line, the stack line, *Commands* (add `make design-check`), and replace *The API boundary* + *Conventions* with: "Conventions live in the `ddd-frontend` skill; `src/training/` is the worked example to copy." plus the two non-negotiables (never edit `src/api/generated/`; never read backend source for an API answer).

- [ ] **Step 6: Verify and commit**

```bash
./scripts/verify-plugin.sh
make -C templates/spring-ddd/frontend ci
git add plugins/ddd-workflow scripts/verify-plugin.sh templates/spring-ddd/frontend/CLAUDE.md
git commit -m "ddd-workflow: ddd-frontend skill; the frontend agent loads it"
```

---

### Task 4: Docs, version, full verification

**Files:**
- Modify: `README.md`, `HOWTO.md`, `plugins/ddd-workflow/.claude-plugin/plugin.json`

- [ ] **Step 1: README** — under *Skills*, add after `ddd-backend`:

```markdown
- `ddd-frontend` — the frontend's counterpart: a context's folder, its query hooks and
  keys, how a ProblemDetail becomes a UI state, and MSW tests per state. The template's
  `frontend/src/training/` is the worked example it describes, and `architecture.test.ts`
  enforces the import rules. It uses Vercel's `vercel-react-best-practices` and
  `vercel-composition-patterns` skills when they are installed.
```

In the agents table, the `frontend` row's purpose stays; nothing else changes there. In the dependencies paragraph added for archify, add the two Vercel install lines as optional.

- [ ] **Step 2: HOWTO** — in *2. One-time, per machine*, add the two optional `npx skills add vercel-labs/agent-skills@… -g` lines, marked optional.

- [ ] **Step 3: Version** — `plugins/ddd-workflow/.claude-plugin/plugin.json`: `"version": "2.0.0"` → `"version": "2.1.0"`.

- [ ] **Step 4: Everything**

```bash
./scripts/verify-plugin.sh
./scripts/check-plugin-version-bump.sh main
./scripts/verify-archetype.sh
make -C templates/spring-ddd verify
```

Expected: all pass. `verify-archetype.sh` proves the new Java packages, the MSW setup files and the regenerated client survive archetype generation.

- [ ] **Step 5: Commit**

```bash
git add README.md HOWTO.md plugins/ddd-workflow/.claude-plugin/plugin.json
git commit -m "ddd-workflow 2.1.0: document ddd-frontend"
```
