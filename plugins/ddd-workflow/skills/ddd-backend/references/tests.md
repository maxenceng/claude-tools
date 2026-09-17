# Unit tests

JUnit 5, AssertJ, Mockito. No Spring context anywhere in a unit test — if a business rule
needs `@SpringBootTest` to exercise it, the rule is in the wrong layer, and that is
diagnostic rather than a hurdle.

## Placement and naming

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

## No comments under `src/test`

Write no comment anywhere in `src/test/java` — no javadoc on a class or a method, no `//`
above an assertion, no header explaining what a fixture is for. The name is the
explanation, which is why the naming above is a rule and not a preference:
`shouldNotBuildIfSeatsIsNull` has already said everything a javadoc would repeat.

A comment there is worse than redundant. It is a second description of the behaviour that
nothing keeps in step — no compiler checks it and no assertion fails when it goes stale —
so it rots while the test stays green, and the next reader is misled by the half that
still looks authoritative.

`make test-comment-check` enforces this, so do not expect to argue with it in review. It
reads source, because comments do not survive into bytecode and ArchUnit cannot see them.

If a test seems to need explaining, that is a signal about the test. Rename it, or split
it into two that each assert one thing. Where the reasoning is genuinely worth keeping, it
has two homes that a comment does not: the assertion's `.as(...)` description, which is
printed when the test fails and so is read exactly when it matters, and the ADR or ticket
that decided the behaviour.

**One exemption: a file that holds architecture rules** — `@AnalyzeClasses` for ArchUnit,
`ApplicationModules` for Spring Modulith. Its rules are declarative fields rather than
named methods, so there is no name for the reasoning to live in, and moving it out would
separate the rules from their justification. ADR 0007. This exemption is not a precedent
for "my test is special": every other test under `src/test/java` is scanned, and the check
fails if it ever finds nothing left to scan.

## Fixtures

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

**A unit test class contains tests and nothing else.** A private `courseWithSeats(int)` at
the bottom of `CourseTest` is a fixture that only one class can reach, so the moment a second
test needs the same value it gets retyped with a different literal and the two drift. Put it
in the fixture, name it for the state — `fullCourse()`, `courseWithOneSeatLeft()` — and the
manager test, the controller test and the request test all pin the same boundary.
`TestConventionsTest.unit_tests_hold_only_tests` enforces this directly — a private method in
any `*Test` class fails the build, exempted only for the Spring-slice tests it cannot see
inside (`@WebMvcTest`, `@DataJpaTest`, `@SpringBootTest`, …) and the files that hold
`ArchitectureTest`-style rules, whose private methods are conditions, not fixtures.

Tests that boot a Spring context are out of scope, and the rule exempts them by annotation.
A `@WebMvcTest` building a `RequestBuilder`, or a `@DataJpaTest` arranging a context, is
constructing a call to a running application rather than a domain value — that belongs in
the test that makes the call, not in a fixture beside a type it does not describe.

Values the constructor *refuses* still belong in the fixture, returned as the raw type: a
fixture cannot hand back a `Seats` that cannot be built, so `negativeSeats()` returns an
`int`. That is not a leak — it is the fixture saying which side of the boundary
the value sits on.

## Assertions

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

## What each layer gets

**Value objects and identities.** Rejects null with the field named in the message,
builds from the fixture, plus one test per behaviour it exposes (`shouldAdd`,
`shouldGenerate`).

**Aggregates.** One test per invariant and per behaviour, including both sides of every
threshold — see below.

**Domain services and application services.** `@ExtendWith(MockitoExtension.class)`,
`@InjectMocks` on the subject, `@Mock` on the port. Stub with `when(...)`, assert on the
result. `<X>ApplicationServiceTest` should be the same tests as `<X>ManagerTest`, method for
method, differing only in the subject they call. That is not accidental duplication to
extract later: the manager test proves the rule exists, and the application service test
proves it is still reachable through the bean Spring wires — a rule can survive the first
and be bypassed by the second.

Where a rule moved out of a value object into the manager, its test moves with it. Leaving
`shouldNotBuildBelowThePublishingMinimum` in `SeatsTest` after the constructor stopped checking
gives a test that passes for the wrong reason or fails for the right one; either way the
rule is now the manager's and belongs in its test.

`@InjectMocks` assumes every non-mocked constructor argument can be defaulted or is absent.
A constructor mixing `@Mock`-able ports with `@Value`-injected primitive config (a batch size,
a threshold) can defeat it outright — Mockito may refuse to construct the subject at all rather
than leave the primitives at their default. Worse, a `@Value` field the domain validates as
`strictlyPositive()` or similar throws on construction before `ReflectionTestUtils.setField`
ever gets a chance to run, so that combination can't rescue it either.

Where that config belongs to the service alone — nothing else reads it, and the constructor
does not need it to precompute anything — take it out of the constructor entirely and
field-inject the `@Value` directly instead. That is a narrow, explicit carve-out of "nothing
is field-injected" (worth its own ADR the first time a project adopts it), not a general
escape hatch: every other collaborator — ports, managers — stays a `final`,
constructor-injected field. It restores `@InjectMocks` outright, because the constructor now
takes only mockable ports, and lets `ReflectionTestUtils.setField` set the config directly in
`@BeforeEach`. Anything the constructor used to precompute from that config — a cached
`Duration`, a cached value object — has to move to the call site too: a field-injected
`@Value` is not set until after the constructor returns, so the constructor cannot read it at
all, not merely "should not" to stay buildable.

Check by running the test before assuming a pattern is available. Manual construction —
`new Service(mockA, mockB, BATCH_SIZE, THRESHOLD)` in a `@BeforeEach` — is still the right
answer wherever the config is a genuine constructor concern: shared by more than one
collaborator, or needed to build something else at construction time. It is not a shortcut
to reach for by default where field injection would resolve the same class more directly.

**Secondary adapters.** `@Mock` the `Jpa*` repository, `@InjectMocks` the adapter, and
assert on what comes back through the port — including the exception translation, which is
the only part carrying a decision. The entity gets its own test: `create(...)` against the
fixture ignoring the generated id, and `toDomain()` compared recursively.

Be clear about what this does not cover. No database is involved, so the SQL, the column
names and the changelog are all unexercised — a mapping test passes just as happily against
a table that does not exist, and a test that stubs the repository into throwing a constraint
violation proves only that the `catch` works, never that the constraint exists.

So each aggregate also gets one `<Aggregate>RepositoryIntegrationTest`: `@DataJpaTest`,
`@AutoConfigureTestDatabase(replace = NONE)`, `@Testcontainers(disabledWithoutDocker = true)`,
`@Import` the adapter, and a `@ServiceConnection` container on the real image. Liquibase runs
against it, so it is the only test that fails when a unique index is deleted from the
changelog — `ddl-auto=validate` checks columns and types, not constraints. Keep it to the
things only a database can answer: the constraint fires, the generated id comes back.
`disabledWithoutDocker` is what lets the suite still pass on a machine with no Docker.

**Primary adapter mappers.** `*Request` and `*Response` records get a round-trip test
against the domain fixture, one per meaningful shape (`shouldBuildToMinimalDomain`,
`shouldBuildToFullDomain`).

**Controllers** would take `@WebMvcTest`. Note that Spring Boot 4 moved the MVC slice out
of `spring-boot-starter-test` into `spring-boot-webmvc-test`; if `@WebMvcTest` will not
resolve, that dependency is missing rather than the annotation being gone.

## What earns a test

Test the boundary, not the middle. A capacity rule covered at 0-of-10 and 10-of-10 passes
with an off-by-one still in it — 9-of-10 is the case that catches it. Whenever a rule has
a threshold, the tests that matter are the ones either side of it.

Before trusting a test you just wrote, break the code it covers and watch it fail. This is
not ceremony: a test that asserts on a mock's return value frequently passes whether or
not the thing it claims to check is wired at all, and it will keep passing after someone
removes that thing.

Do not add a test for a getter, a builder setter, or a record accessor. They have no
behaviour, and a suite padded with them takes longer to run and trains people to skim.

Do not re-pin a value object's own construction-time validation from one of its callers.
Once `QuarantineThresholdTest` (or whichever value object's own test) covers "a
non-positive value throws," an application-service or manager test that feeds the same
value object the same bad primitive and asserts the same exception exercises nothing
about the service — it reaches the value object's compact constructor through a longer
path and proves the same thing twice. This holds even where the failure moved, such as
a value object now built lazily at its call site instead of eagerly in a constructor:
the new *timing* of the failure is worth an ADR, not a test in every caller that now
triggers it.

The same failure shows up when a manager method stops doing anything but delegate. A
test that stubs a one-line call to a port or a collaborator and asserts the stub's
return value comes back unchanged is not covering the manager — it is covering
Mockito. This is the common aftermath of moving real behaviour out of a manager (into
another collaborator, or up into the `*ApplicationService`): the method that used to
justify the test is now a pass-through, and the test that used to exercise it still
compiles and still passes, having stopped proving anything. Delete it rather than
reshape it; the behaviour that used to live there is tested where it moved to.
