---
name: ddd-backend
description: Conventions for writing backend code in a DDD/hexagonal Spring Boot project — adding a bounded context, modelling an aggregate, declaring ports and adapters, and testing each layer. Load before writing or restructuring backend code.
---

# DDD backend conventions

The hard rules are enforced by `ArchitectureTest` and `ModularityTest`. This document
covers the things a test cannot check: where a concept belongs, what to name it, and
which shape to reach for.

## Read the neighbour first

Before writing a type, open its counterpart in the most established context and match
it. A project's real conventions live in its code, not here — this document is general
and the code is specific, so where they differ the code wins. Name the file you matched
when you report back, because that is what makes the check visible rather than assumed.

The question to answer is not "what is a reasonable way to write this" but "how did this
project already write this". A new aggregate copies the shape of an existing aggregate.
A new manager copies an existing manager, including what it *does not* do — if no manager
in the codebase validates its arguments, the new one does not either, and the absence is
the convention. A new value object copies the one next to it, including whether it bounds
its value.

This is the cheapest check available and it catches the failure this document cannot: a
convention that is real, consistent and written down nowhere. Grepping one sibling file
takes seconds; a reviewer explaining the same convention for the third time does not.

## Package layout

```
com.example.<app>.<context>
├── package-info.java              @ApplicationModule
├── domain
│   ├── <Aggregate>.java           aggregate root
│   ├── <ValueObject>.java         records
│   ├── <Aggregate>Id.java         identity
│   ├── <Aggregate>Manager.java    domain service, when ordering matters
│   ├── <Name>Port.java            interfaces the domain requires
│   └── <Rule>Exception.java       named after the rule that was broken
├── application
│   └── <UseCase>ApplicationService.java
└── infrastructure
    ├── primary                    driving adapters: HTTP, CLI, messaging consumers
    └── secondary                  driven adapters: persistence, external APIs
```

A bounded context is a direct subpackage of the application root. Its nested packages
are internal: another context can only reach what sits in the context's root package.
This is enforced, so a cross-context import of `training.domain.Course` fails the build
rather than being caught in review.

Two kernels sit outside the contexts and are open modules, so their nested packages stay
visible: `shared` and `error`. `error` holds `DomainException`, `Assert` and the single
global exception handler; `shared` holds application-wide technical configuration such as
the `OpenAPI` bean, under `shared.infrastructure.primary`. Keep both small — anything
that belongs to one context belongs in that context.

## Adding a bounded context

1. Create the package and a `package-info.java` with `@ApplicationModule`.
2. Add `domain`, `application`, `infrastructure.primary`, `infrastructure.secondary`.
3. Expose to other contexts only from the context root package.
4. Record the context and its relationships in `docs/context-map.md`, and its terms in
   `docs/glossary.md`, in the same change. Written later, both describe what someone
   remembers rather than what was built.
5. Run `make arch`.

Most of the shape is enforced, not advised. `ArchitectureTest` checks that `@Service`
classes are `*ApplicationService` in `application`, that `@Repository` is in
`infrastructure.secondary`, that `*Request`/`*Response` live in `infrastructure.primary`,
that domain exceptions extend `DomainException`, that domain fields are final, and that
nothing is field-injected. Run it and read the failures rather than checking this list by
eye — and if a rule reports it "failed to check any classes", something was renamed out
from under it.

Do not add to the shared kernel to avoid the exposure step. The shared kernel couples
every context to itself, so each addition costs more than the last.

## Modelling

**Aggregate roots** are records with a builder. State changes return a new instance
rather than mutating in place. The aggregate is the last place that can still refuse, so
it re-checks its own rules even when a caller already did. Validate presence and
value-object validity in the compact constructor; a rule about a *transition* belongs on
the method that performs the transition.

**Value objects** are records wrapping **one** attribute, validated in the compact
constructor so an invalid instance cannot exist.

**Every domain type with more than a couple of fields gets a builder** — hand-written,
never Lombok's `@Builder`, in the shape `Price` and `CastMember` use. Two exceptions: a
genuine value object (one or two positional arguments read fine) and a domain service
whose fields are wired ports, not domain data.

**A value object built from external config** is constructed at its call site, not
cached as a field built once at startup — a misconfigured property should throw the
first time it's actually needed, not at boot.

A value object never takes a port; loading, saving and anything that calls out belong to
the manager.

**A value that is sometimes absent**: one field not always supplied stays nullable
behind an `Optional<T>` accessor. Once more than one field varies together, split into a
`sealed interface` instead.

**Identities** are records wrapping a `UUID`, one per aggregate.

**Domain services** (`<Aggregate>Manager`) are records taking the ports they need, for a
sequence that must not be reordered or half-copied into a caller. They run the use
case's rules cheapest-first — check what costs nothing before what costs a query.

**Use case input** with more than one part gets a record of its own.

**Ports** are interfaces in `domain`, named for what the domain needs. Only a domain
service holds a port — an adapter that holds one, or depends on another adapter, is a
second place deciding what the use case means.

**A manager depends on ports only, and never on another manager.** Where a manager's own
use case genuinely needs a decision another manager makes, take that manager's port
directly and re-implement the small decision inline, or, where duplicating it would
itself be the bug, wire both managers into the `*ApplicationService` instead.

Read `references/modelling.md` before modelling an aggregate, value object, domain
service, or use-case input — it has the reasoning behind each rule and the trade-offs
this summary drops (the builder exceptions in full, the sealed-type threshold, what a
`Manager` drifting toward carried data means, the `ArchitectureTest`/`AssertTest` rules
that pin these).

**Exceptions** extend `DomainException`, are named after the rule (`CourseFullException`),
and pass a `DomainErrorStatus` to `super`. See *Errors* below.

## Application layer

Application services orchestrate: load an aggregate, call one method on it, save it,
return a result. They hold no business rules.

The reliable smell is a conditional in an application service that encodes a policy.
`if (course.enrolledSeats() >= course.seats().get())` in a service means the rule
escaped the aggregate — move it to `Course.enroll()` and let it throw.

They return the aggregate. That is safe here because aggregates are immutable records,
so an adapter cannot mutate what it is handed. The wire format still stays independent:
the primary adapter owns a response record and maps to it (`CourseResponse.from(course)`).

Where a domain service exists, the application service delegates to it and adds only the
Spring wiring. That looks like duplication and is not: it is the one place the framework
is allowed to touch, keeping the sequencing rule testable without a context.

## Adapters

**Primary** adapters translate an external protocol into a use-case call and back.
Request/response records live beside the controller, not in the domain.

**Secondary** adapters implement domain ports. Persistence entities are mapped to domain
types, never annotated `@Entity` directly. A context's persistence is three types in
`infrastructure.secondary`:

| Type | Role |
|---|---|
| `<Aggregate>Entity` | `@Entity`, private fields, mutable through setters, with `create(...)` and `toDomain()` |
| `Jpa<Aggregate>Repository` | `extends JpaRepository`, derived queries only |
| `<Aggregate>Repository` | `@Repository`, implements the domain port, maps and translates |

Name a driven adapter for the port it satisfies, not its technology: `NotifierPort` is
implemented by `NotifierRepository`, not `SmtpNotifier`.

Read `references/adapters.md` before writing a primary or secondary adapter — it covers
entity field access rules, `saveAndFlush` vs `save`, translating the specific constraint
exception rather than its parent, database-generated ids, and never editing a Liquibase
changeset that has run.

**An outbound client to a vendor's API is a secondary adapter too**, just not persistence's
shape. Read `references/outbound-clients.md` before writing one — it covers the package
placement, the declarative client shape, and the factories every vendor client reuses so the
second one is smaller than the first.

Where the trigger is a schedule rather than a request — a nightly re-sync, a batch lookup —
the driving side is a Temporal workflow, not a controller. Read
`references/workflows.md` before writing one.

## Errors

One `@RestControllerAdvice` for the whole application, in
`error.infrastructure.primary`. `ArchitectureTest` fails the build if a second one
appears anywhere else.

A per-context handler looks tidier and is a trap: it has to be remembered when a context
is added, and until someone does, that context's failures leave as 500s. It also cannot
be written without importing the context's internals, which the module boundaries forbid.

So the handler maps a status *enum*, not exception types:

```java
public abstract class DomainException extends RuntimeException {
    protected DomainException(DomainErrorStatus status, String message) { ... }
}

// error.domain — deliberately not HTTP
public enum DomainErrorStatus { NOT_FOUND, CONFLICT, INVALID }
```

Each exception declares its status where the rule lives, and the handler translates
`DomainErrorStatus` to `HttpStatus` in one switch. A new context is covered the moment
its exceptions extend `DomainException`; nobody has to remember anything.

`DomainErrorStatus` is not an HTTP leak into the domain. The domain distinguishes "does
not exist" from "not allowed right now" for its own reasons, and the same distinction
maps to different codes over different protocols.

Choose the status by what it tells the caller: `CONFLICT` when the request is fine and
the state is not (a full course — retry later and it may work), `INVALID` when the
request is wrong however the state changes.

`AssertionException` is a separate hierarchy — it guards types rather than business
rules — and the same handler answers `400` for it.

## The HTTP contract

The `@ApiResponse` annotations on a controller are the API contract: the frontend's
client is generated from them, so a wrong code there becomes a wrong type in the
frontend. Every failure code a route can produce comes from the global handler — read
it before writing them, and do not document a code no handler emits.

The generated client goes stale silently, because regenerating is two steps and only the
second is obvious:

```
make run              # the schema is read from the live app
make openapi          # writes docs/openapi.json
make openapi-client   # writes the typed client
```

Commit `docs/openapi.json`. Without it there is nothing to diff a drifting client
against, and the drift surfaces as a field that is `undefined` at runtime rather than as
a compile error.

Because it is committed, the capture has to be **stable and portable**, and springdoc's
defaults are neither. Two settings earn their place:

```properties
springdoc.writer-with-order-by-keys=true   # sort keys, or an unrelated edit reorders
                                           # the file and buries the real diff
```

and a relative server URL, set on the `OpenAPI` bean:

```java
.servers(List.of(new Server().url("/")))
```

Left alone, springdoc writes an absolute `http://localhost:8080`, which pins whichever
machine ran the capture and produces a spurious diff on every other one.

The description itself lives in an `OpenAPI` bean in `shared.infrastructure.primary` —
title, description, license, and an **API version distinct from the build version**.
Bumping the Maven version does not change what a client may rely on; a breaking change
to a route does. Only the second belongs in the schema.

Verify a capture by taking it twice and diffing. If the two differ, the schema is not
committable yet, whatever it looks like on one run.

## Unit tests

JUnit 5, AssertJ, Mockito. No Spring context anywhere in a unit test — if a business rule
needs `@SpringBootTest` to exercise it, the rule is in the wrong layer, and that is
diagnostic rather than a hurdle.

Read `references/tests.md` before writing one — it covers placement and naming, why
`src/test` carries no comments, fixture conventions, assertion style, what each layer's
test looks like (including the `@InjectMocks`/field-injection interaction to check before
assuming a pattern is available), and what earns a test at all.

## Comments

Comment the decision, not the mechanics — two lines is the ceiling for Java, less
elsewhere, and class/method javadoc restates a decision's reasoning only where no ADR
already covers it. Check a comment against the code before trusting it; names rot the
same way comments do. A `FIXME` is a decision deferred — carry it out or record why it
stands; a `deferred:` comment names a limit someone chose to live with and the trigger
that would justify closing it.

Read `references/comments.md` for the worked examples — a stale assertion doc, a bulk
rename that corrupted javadoc, and the `FIXME` vs `deferred:` distinction in full.

## Frequent mistakes

- Anaemic aggregates — logic living in a service instead of the aggregate. The default
  failure mode of this architecture, and no test catches it.
- An interface with exactly one implementation, reached for out of habit rather than to
  invert a real dependency across a boundary.
- Adding to the shared kernel because a type is needed in two places, without asking
  whether it's genuinely one concept or two that happen to share a name.
- Naming things `Helper`, `Processor`, or `Util` — signs the real concept hasn't been
  found yet.
- Wiring one manager into another because both are already there and the second does
  most of what the first needs.
- Adding a rule to `ArchitectureTest` for something ArchUnit cannot see — it reads
  bytecode, so imports, generics, and Lombok annotations are invisible to it.
- Trusting a rule that has never been seen to fail. Break the thing it forbids, watch
  the build go red, then put it back — that's the only evidence the rule works.
- Guarding a vendor field against a value the vendor has never been observed to send,
  because a neighbouring field's guard earned its place with evidence and this one
  borrows the shape without it.
- Documenting an intention the code does not enforce.

Read `references/frequent-mistakes.md` before a self-review — each has a worked example,
and the guard-removal item has two look-alike cases that resolve oppositely once checked.
