# app

Spring Boot 4 / Java 25 backend with DDD bounded contexts and hexagonal layering, and a
React 19 frontend typed from the backend's OpenAPI schema.

No business context exists yet. `shared` and `error` are kernels, not contexts — add the
first real one and record it in `docs/context-map.md`.

## Quick start

```bash
make doctor     # check the toolchain first; it is usually the toolchain
make ci         # lint, tests, duplication
make fe-check   # frontend typecheck and tests
```

Both should pass on a fresh checkout. `make help` lists every target.

```bash
make run        # start the backend on :8080
make -C frontend dev   # dev server, proxies /api to :8080
```

Use `make`, never `mvn` directly — the Makefile selects the Java 25 toolchain, and
calling the wrapper yourself fails with "release version 25 not supported".

## Structure

```
com.example.app.<context>.{domain, application, infrastructure.{primary, secondary}}
```

One bounded context per direct subpackage of the root. Dependencies point inward:
infrastructure → application → domain. The domain knows about no framework.

Two open kernels sit outside the contexts: `shared` for application-wide technical
configuration, and `error` for `DomainException`, `Assert` and the single global
exception handler. Keep both small.

## The rules are executable

`ArchitectureTest` carries 14 rules covering dependency direction *and* the shape of a
context — where a `@Service` lives and what it is called, where `@Repository` lives, that
domain exceptions extend `DomainException`, that domain fields are final. `ModularityTest`
verifies the context boundaries and regenerates the architecture diagrams.

When one fails, the code is wrong. Changing a rule is a decision, and decisions go in
`docs/adr/`.

If a rule reports *failed to check any classes*, it matched nothing — something was
renamed out from under it. While the project has no bounded context,
`src/test/resources/archunit.properties` suppresses that; **delete it once the first
context exists.**

## The API boundary

`frontend/src/api/generated/` is produced from the backend's OpenAPI schema and is the
whole truth about the API. Never hand-edit it, and never read backend source to answer a
frontend question about the API — if the generated types do not answer it, the backend
annotation is missing.

Regenerating is three steps, and running only the last one regenerates types from a stale
schema, which is how the client silently drifts:

```bash
make run              # in another shell
make openapi          # writes docs/openapi.json
make openapi-client   # writes the typed client
```

`docs/openapi.json` is committed. Failure codes come from the global exception handler —
check it before writing `@ApiResponse` annotations.

## Where to look

- `CLAUDE.md` — what this project is, and the hard rules; deliberately short
- `docs/backlog/` — features to do and their status
- `docs/glossary.md` — the words the code uses
- `docs/context-map.md` — contexts and their relationships
- `docs/adr/` — why things are the way they are
- `target/spring-modulith-docs/` — generated diagrams, refreshed by `make docs`

## Working with Claude Code

```
/plugin marketplace add maxenceng/claude-tools
/plugin install ddd-workflow@maxence-tools
```

Then `/ticket` to see the backlog, `/ticket start <ID>` to work one, `/onboard` when
returning to the project after a while. The conventions live in the `ddd-backend` skill
so they load when relevant rather than on every request.
