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
- `make fmt` / `make lint` — apply / verify formatting
- `make ci` — everything CI runs

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

## Where to look

- `docs/backlog/` — features to do and their status; driven by `/ticket`
- `docs/glossary.md` — ubiquitous language; use these words in code
- `docs/context-map.md` — contexts and their relationships
- `docs/adr/` — why things are the way they are
- `target/spring-modulith-docs/` — generated diagrams, refreshed by `make docs`
