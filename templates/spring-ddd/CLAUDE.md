# app

Spring Boot 4 / Java 25. DDD bounded contexts with hexagonal layering.

## What this is

<!-- REPLACE-ME: delete this comment and the four prompts below once written. This file is
     read on every request, so keep the result to about the length it already is — four
     short paragraphs. Anything longer belongs in docs/ and is read when relevant. -->

*What the system does*, in two sentences, in the language of the domain rather than of the
stack. Everything below this section is stack; none of it says what is being built.

*Who uses it*, and whose vocabulary wins when a plain word and a technical one both fit.
This settles naming arguments before they reach the glossary.

*What is deliberately out of scope.* The most valuable line here, and the only one nothing
else in the project records — an agent will keep building, and a written fence makes "that
is out of scope" a fact rather than an argument.

*What stage it is at*: greenfield, live, or migrating. The same request deserves a
different answer before and after there are users.

## Commands

Use `make`, never `mvn` directly — the Makefile selects the Java 25 toolchain.

- `make doctor` — check the toolchain when something looks broken
- `make test` — all tests, architecture rules included
- `make test-one T=SomeTest` — one class or method, when the full run is too slow to iterate on
- `make fmt` / `make lint` — apply / verify formatting
- `make adr-check` — fail on a duplicate or missing ADR number; run it before choosing one
- `make verify` — everything CI runs, in CI's order. This is the one to trust before a PR;
  `make ci` is only the backend job's first step

## Structure

```
com.example.app.<context>.{domain, application, infrastructure.{primary, secondary}}
```

One bounded context per direct subpackage of the root. No business context exists yet;
`shared` and `error` are kernels, not contexts.

The shape of a context is enforced by the rules below rather than copied from an
example, so `make arch` will tell you when a new one is wrong.

## Hard rules

Enforced by `ArchitectureTest` and `ModularityTest`. When one fails, fix the code;
do not weaken the rule without an ADR.

1. Dependencies point inward: infrastructure → application → domain.
2. The domain imports no framework — no Spring, no Jakarta, no Jackson.
3. Ports are interfaces in `domain`; adapters implement them in `infrastructure.secondary`.
   Only a domain service *holds* one — an adapter implements a port, it never depends on
   another. And nothing in `infrastructure.secondary` calls the application layer.
4. Other contexts are reached by ID through a context's root package, never by
   importing its internals.
5. Aggregates expose behaviour, not setters. A value object wraps one attribute; a domain
   record holding several holds value objects, never raw values.
6. One `@RestControllerAdvice`, in `error.infrastructure.primary`. Domain exceptions
   carry a `DomainErrorStatus`; only that handler knows about HTTP.
7. A context keeps its shape: `@Service` is an `*ApplicationService` in `application`,
   `@Repository` lives in `infrastructure.secondary`, `*Request`/`*Response` live in
   `infrastructure.primary`, domain exceptions extend `DomainException`, domain fields
   are final, and nothing is injected into a field.

## Conventions

For anything the rules above do not cover — adding a context, naming, test style —
invoke the `ddd-backend` skill instead of inferring from existing code.

## Defaults

Settled. Act on these rather than asking.

- A coverage gap closes in the ticket that opened it. Write the test, do not defer it.
- A decision someone could reverse later without knowing why gets an ADR, in the same change.
- Work lands on a branch and a PR, never straight to `main`. Push once `make verify` is green.
- Formatting is whatever `make fmt` produces. `.editorconfig` matches the spotless config;
  neither is up for negotiation per file.
- Re-check an acceptance criterion against the pushed commit, never against an earlier run.
- A review finding with one obvious fix and no design choice gets fixed in the same pass,
  not reported and left. Only a finding that forks the design waits to be raised.
- Nothing under `src/test/` carries a comment — no javadoc, no `//`. The test name is the
  explanation; why the behaviour is what it is belongs in the assertion's `.as(...)`, the
  ADR or the ticket. `make test-comment-check` enforces it. The one exemption is a file
  holding architecture rules, whose rules are fields rather than named methods — ADR 0007.
- A comment in a config file records the choice, never what the tool does, and fits in two
  lines. `make config-check` enforces the length; the rest is judgement.
- A limit deliberately chosen carries a `// deferred:` comment naming the ceiling *and* what
  would make it worth closing — `// deferred: <what it cannot do> — <what triggers closing it>`.
  Ceiling first, trigger second; a marker with no trigger never gets revisited. `/debt`
  collects these alongside ADR *Consequences* and ticket *Notes*. A limit nobody chose is not
  debt, it is an oversight — raise it instead.
- A new rule, check or guard is not done until it has been watched to fail on the case it
  exists for. A rule nobody has seen fail is a rule nobody has tested — and one that reads
  as protection while giving none is worse than no rule, because the next reader stops looking.
- A build result is read from a captured exit code — `make verify > log 2>&1; echo $?` — never
  from a pipeline, which reports the last command's status and not `make`'s. `Skipped: 0` is
  part of the result; `make verify` fails on a skip.

Ask when the choice is a genuine trade-off rather than a default: a review that contradicts
something asked for explicitly, a change to a published contract, or a rule that would have
to carve out an exception to hold.

## Where to look

- `docs/backlog/` — features to do and their status; driven by `/ticket`
- `docs/glossary.md` — ubiquitous language; use these words in code
- `docs/context-map.md` — contexts and their relationships
- `docs/adr/` — why things are the way they are
- `target/spring-modulith-docs/` — generated diagrams, refreshed by `make docs`
