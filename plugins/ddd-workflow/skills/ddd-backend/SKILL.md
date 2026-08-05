---
name: ddd-backend
description: Conventions for writing backend code in a DDD/hexagonal Spring Boot project — adding a bounded context, modelling an aggregate, declaring ports and adapters, and testing each layer. Load before writing or restructuring backend code.
---

# DDD backend conventions

The hard rules are enforced by `ArchitectureTest` and `ModularityTest`. This document
covers the things a test cannot check: where a concept belongs, what to name it, and
which shape to reach for.

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

**Aggregate roots** are records with a builder, as `Course` is. State changes return a
new instance (`Course.enroll()` returns the enrolled course) rather than mutating in
place, so there is no partially-updated object to observe and no setter to add.

What makes it an aggregate is not the shape but the behaviour: it holds the rule that
constrains its own state, and every path that changes that state goes through a method
that checks it. `Course.enroll()` re-checks capacity even though its caller already did,
because the aggregate is the last place that can still refuse.

Validate in the compact constructor, but be clear about what it can enforce. It runs on
every construction, including when a secondary adapter rebuilds a stored course, so it
can only check what is true of every instance — presence, and value-object validity.
A rule about a *transition* ("you may not enrol into a full course") belongs on the
method that performs the transition.

**Value objects** are records. Validate in the compact constructor so an invalid
instance cannot exist. `Seats` rejecting a negative count is worth more than every
downstream check for a negative count.

Validate there, never coerce. A compact constructor that lowercases an address or trims a
name also runs when a secondary adapter rebuilds a stored row, so the object comes back
disagreeing with the row it was built from, and `new EmailAddress(x).value()` stops
returning `x`. Where one form is canonical, reject the others — a pattern that admits only
the canonical form — and let the caller send the right thing. Normalising input is a
protocol concern; if it belongs anywhere it is the primary adapter, on the way in.

Read the assertion you are calling before relying on it. `Assert.field("seats", seats)
.positive()` accepts zero; `.strictlyPositive()` is the one that does not. A value object
whose javadoc and whose assertion disagree is worse than one with no javadoc.

`AssertTest` pins that boundary for every numeric type. If you need a bound the asserters
do not express, add it there with a test rather than open-coding the check in a value
object, where the next aggregate cannot reuse it.

**Identities** are records wrapping a `UUID`, one per aggregate. Distinct `CourseId`
and `StudentId` types make it impossible to pass one where the other is expected —
a mistake `UUID` everywhere invites.

**Domain services** are records taking the ports they need, named `<Aggregate>Manager`.
Reach for one only when a sequence has to be fixed: `CourseManager.enroll` loads the
course, asks it whether a seat is free, and saves, and those three steps must not be
reordered or half-copied into a caller. It lives in `domain`, not `application`, because
that ordering is a rule. Pass-through methods on it are fine — they keep callers to one
entry point.

**Ports** are interfaces in `domain`, named for what the domain needs rather than for
what implements them. `CoursePort`, not `JpaCourseAdapter`. The domain declares the
requirement; infrastructure satisfies it.

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

**Primary** adapters translate an external protocol into a use-case call and translate
the result back. A controller that makes a decision is doing the application layer's
job. Request and response records live here, beside the controller, because they are
the shape of the protocol rather than the shape of the domain.

**Secondary** adapters implement domain ports. Persistence entities live here and are
mapped to domain types — do not annotate an aggregate with `@Entity` and call it a
domain model, because from then on the database schema drives the design.

Persistence is JPA, via `spring-boot-starter-data-jpa`. A context's persistence is three
types in `infrastructure.secondary`, and the split is what keeps Hibernate out of the
domain:

| Type | Role |
|---|---|
| `<Aggregate>Entity` | `@Entity`, package-private, mutable, with `from(aggregate)` and `toDomain()` |
| `SpringData<Aggregate>Repository` | `extends JpaRepository`, derived queries only |
| `Jpa<Aggregate>Repository` | `@Repository`, implements the domain port, maps and translates |

Liquibase owns the schema, so set `spring.jpa.hibernate.ddl-auto=validate`: an entity that
has drifted from the changelog then fails at boot instead of at the first query. Set
`spring.jpa.open-in-view=false` too — left on, it holds a connection open for the whole
request and hides lazy-loading mistakes until they show up under load.

Use `saveAndFlush`, not `save`, wherever the adapter translates a constraint violation
into a domain exception. `save` defers the insert to commit, which happens after the
adapter has returned, so the `DataIntegrityViolationException` is raised outside the
`try` and leaves as a 500 rather than the 409 the catch was written for.

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

### Placement and naming

One test class per production class, named `<Class>Test`, in the **same package** as its
subject under `src/test/java`. Same package is what lets a package-private type be tested
without widening it — `CourseController` and `CourseResponse` are package-private and stay
that way. Never make something public for a test.

Name tests after the behaviour, in camelCase:

| Shape | Example |
|---|---|
| `should<Behaviour>` | `shouldEnroll`, `shouldBuild`, `shouldGenerate` |
| `shouldNot<Behaviour>If<Condition>` | `shouldNotBuildIfSeatsIsNull` |
| `shouldThrow<Exception>` | `shouldThrowCourseFullException` |

`testEnroll2` tells a future reader nothing about what broke.

### Fixtures

Every type a test needs to **construct** gets a `<Type>Fixture` beside it, in the same
package: value objects, aggregates, and the wire records. Services, ports, adapters and
exceptions get none — they are built by Mockito or by the test itself.

A fixture is a `final class` with a private constructor and nothing but static methods,
imported statically by its users. Its visibility matches its reach: domain fixtures are
`public` because the application and infrastructure tests import them, while
`CourseResponseFixture` is package-private because nothing outside the primary adapter
needs it. Widen one only when a real caller appears.

Two rules make them worth having:

**Deterministic values.** `CourseIdFixture` returns a fixed UUID, never
`UUID.randomUUID()`. A random fixture turns a failure into a coin flip and makes the
report useless.

**A builder and a built pair**, wherever the type has a builder:

```java
public static CourseBuilder courseBuilder() { ... }   // pre-filled, valid
public static Course course() { return courseBuilder().build(); }
```

The builder variant is what lets a test vary exactly one field and leave the rest valid —
`courseBuilder().id(null).build()` — rather than restating the whole object and burying
which part the test is about.

Name a fixture for the **state** it represents, not its shape: `course()`, `fullCourse()`,
`courseWithOneSeatLeft()`, `enrolledCourse()`, `zeroSeats()`, `negativeSeats()`. Where a
type has optional fields, provide the `minimal*` / `full*` pair — `minimalCourseToUpdate()`
and `fullCourseToUpdate()` — so the "nothing supplied" case is always one call away.

A fixture named for its shape rots the moment the state matters. `invalidCourse()` here
returned a perfectly valid course that happened to be full, and sent every reader looking
for the invalidity.

### Assertions

AssertJ only. Three forms cover nearly everything:

```java
// Value comparison — recursive, so nested value objects compare by content
assertThat(courses.findById(courseId()))
        .usingRecursiveComparison()
        .isEqualTo(course());

// Failure — isExactlyInstanceOf, and assert the message names the field
assertThatThrownBy(() -> courseBuilder().seats(null).build())
        .isExactlyInstanceOf(MissingMandatoryValueException.class)
        .hasMessageContaining("seats");

// Construction succeeds — a method reference reads best
assertThatCode(CourseFixture::course).doesNotThrowAnyException();
```

`isExactlyInstanceOf`, not `isInstanceOf`: the loose form passes when a subclass or a
wrapper slips through, which is exactly the regression worth catching. Use
`.ignoringFields("id")` when the subject generates a value the test cannot predict.

### What each layer gets

**Value objects and identities.** Rejects null with the field named in the message,
builds from the fixture, plus one test per behaviour it exposes (`shouldAdd`,
`shouldGenerate`).

**Aggregates.** One test per invariant and per behaviour, including both sides of every
threshold — see below.

**Domain services and application services.** `@ExtendWith(MockitoExtension.class)`,
`@InjectMocks` on the subject, `@Mock` on the port. Stub with `when(...)`, assert on the
result. An application service that delegates to a domain service will have a test that
looks almost identical to the domain service's — that duplication is expected and is not
worth extracting, because the two change for different reasons.

**Secondary adapters.** `@Mock` the `SpringData*` repository, `@InjectMocks` the adapter,
and assert on what comes back through the port — including the exception translation,
which is the only part carrying a decision. The entity gets its own test: one round trip,
`from(fixture).toDomain()` compared recursively against the fixture.

Be clear about what this does not cover. No database is involved, so the SQL, the column
names and the changelog are all unexercised — a mapping test passes just as happily
against a table that does not exist. Booting the application with
`ddl-auto=validate` is what catches entity-versus-schema drift; until there is an
integration test, say so rather than ticking a persistence criterion on the strength of
these.

**Primary adapter mappers.** `*Request` and `*Response` records get a round-trip test
against the domain fixture, one per meaningful shape (`shouldBuildToMinimalDomain`,
`shouldBuildToFullDomain`).

**Controllers** would take `@WebMvcTest`. Note that Spring Boot 4 moved the MVC slice out
of `spring-boot-starter-test` into `spring-boot-webmvc-test`; if `@WebMvcTest` will not
resolve, that dependency is missing rather than the annotation being gone.

### What earns a test

Test the boundary, not the middle. A capacity rule covered at 0-of-10 and 10-of-10 passes
with an off-by-one still in it — 9-of-10 is the case that catches it. Whenever a rule has
a threshold, the tests that matter are the ones either side of it.

Before trusting a test you just wrote, break the code it covers and watch it fail. This is
not ceremony: a test that asserts on a mock's return value frequently passes whether or
not the thing it claims to check is wired at all, and it will keep passing after someone
removes that thing.

Do not add a test for a getter, a builder setter, or a record accessor. They have no
behaviour, and a suite padded with them takes longer to run and trains people to skim.

## Comments

Comment the decision, not the mechanics. `enroll()` returning a new `Course` needs no
comment; *why* it re-checks capacity when the caller already did is worth two lines,
because the next reader will otherwise delete the check as redundant.

Two lines is the ceiling, not the target, and it buys less outside Java. `pom.xml`,
`compose.yaml`, `application.properties`, the `Makefile` and CI workflows get a line at
most and usually nothing: their readers already know the tools, and a paragraph on how
Docker publishes a port reads as a prompt rather than as code. A dependency that is easy
to get wrong earns one line naming the trap. Everything else earns silence — including,
especially, the reasoning you found interesting while working it out.

Check a comment against the code before trusting it, especially one that sounds precise.
`Seats` was documented as rejecting zero while its assertion accepted zero, and zero is
what every new course is created with — the comment had been wrong for as long as it had
existed, and it read more authoritatively than the code.

Treat a bulk rename as a comment hazard. A find-and-replace across a file rewrites prose
as happily as identifiers; one such pass had left 156 occurrences of a domain field name
scattered through a generic utility's javadoc, describing parameters that had never had
that name.

Names are documentation and rot the same way. A fixture called `invalidCourse` that
returns a perfectly valid full course sends every reader looking for the invalidity.

`@ApiResponse`, `@Schema` and the like are documentation that ships to another codebase.
Check the codes against the handler that actually produces them.

A `FIXME` is a decision someone deferred. Either carry it out or record why it still
stands — reviewing comments and leaving the `FIXME` untouched is how it survives another
year. When you do act on one, delete it in the same change; a `FIXME` describing work
already done is worse than one describing work outstanding.

## Frequent mistakes

Anaemic aggregates — fields and accessors with the logic in a service. This is the
default failure mode of this architecture and no test catches it.

Reaching for an interface with exactly one implementation because it feels like good
practice. Ports exist to invert a dependency across a boundary. An interface that
crosses no boundary is indirection with no benefit.

Adding to the shared kernel because a type is needed in two places. Ask whether it is
genuinely one concept or two that happen to share a name today.

Naming things `Helper`, `Processor`, or `Util`. These names appear when the real concept
has not been found yet, and they persist long after it has. `<Aggregate>Manager` is the
one exception and only in its narrow sense above — a domain service holding a required
ordering. A `Manager` that has grown methods unrelated to that ordering has stopped
being one and is hiding a concept that still needs a name.

Documenting an intention rather than the code. A comment that states a rule the code
does not enforce is worse than silence: it is believed, and it stops the reader from
checking. If the invariant is real, enforce it; if it is not enforced yet, say exactly
where it is and is not.
