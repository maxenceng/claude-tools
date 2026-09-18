# Modelling

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

**Value objects** are records wrapping **one** attribute. Validate in the compact
constructor so an invalid instance cannot exist. `Seats` rejecting a negative count is
worth more than every downstream check for a negative count.

One attribute is the rule, not a guideline. A domain record holding several holds *value
objects*, never raw values — so a `String`, a `UUID` or a `Duration` appears in exactly one
place, the type that gives it a name and a rule. `boolean` is the only exception: there is
nothing to validate and no name worth inventing.

**Every domain type with more than a couple of fields gets a builder** — not only the ones
with an optional field. Use it everywhere the type is constructed: production factory
methods, entity `toDomain()` conversions, and test fixtures, in place of the positional
canonical constructor. The exception is a genuine value object — it stays constructed
directly, since one or two arguments read fine positionally and a builder would only add
ceremony. A named-setter call reads clearly regardless of argument count or order, and
survives a field being added, reordered, or made optional later without every call site
changing; that payoff exists whether or not the type happens to have an optional field
today, which is why the bar is "is this a value object", not "does this have one". Where a
type also needs a `minimal<Type>Builder` for the fixture problem below, that is additional
to this, not instead of it.

A second exception: a domain service whose fields are wired collaborators — ports, and
ports alone — assembled once by the application layer that constructs it, named
`<Aggregate>Manager`. Its fields are not domain data a reordered positional argument could
silently corrupt, which is the risk the builder rule exists to prevent, so it stays
constructed positionally. A `Manager` whose fields have drifted toward carried data rather
than wiring has outgrown the exception and the name at the same time — see *Frequent
mistakes*. So has one that has drifted toward wiring in another `Manager` instead of
a port — see *Domain services* below for what to do when a use case needs another
manager's decision.

The builder is hand-written, in the shape `Price` and `CastMember` already use — a nested
`<Type>Builder` with fluent setters and a `build()` that calls the existing compact
constructor, so every invariant the constructor already asserts still runs — never Lombok's
`@Builder`. The domain imports no framework, and `DomainIsFreeOfLombokTest` holds that as an
executable rule. Lombok's `@Builder` stays correct on JPA entities in
`infrastructure.secondary`, which is a different layer with no such restriction; the "every
multi-field type gets a builder" rule applies there too, just with the framework tool rather
than a hand-written one.

A record written as `(String reference, Duration validFor)` wants to be
`(EnrolmentReference, ValidityWindow)`. The payoff is not tidiness: every rule belonging to
the raw value — a format, a bound, a `toString` that must not print it — then has exactly one
home, and each type holding it inherits that rule instead of remembering it. A secret masked
on its wrapper cannot leak through the fourth record that happens to carry it.
`ArchitectureTest` enforces this, excluding the error kernel and `*Builder` types.

Validate there, never coerce. A compact constructor that lowercases an address or trims a
title also runs when a secondary adapter rebuilds a stored row, so the object comes back
disagreeing with the row it was built from, and `new Title(x).value()` stops
returning `x`. Where one form is canonical, reject the others — a pattern that admits only
the canonical form — and let the caller send the right thing. Normalising input is a
protocol concern; if it belongs anywhere it is the primary adapter, on the way in.

Validate what the value *is*, not what a use case will accept. A compact constructor can
only enforce what is true of every instance ever built, and it is built from stored rows as
well as from requests. "Not negative" is a property of `Seats`; "a course needs at least five
of them before it may be published" is a rule about what publishing accepts, and tightening
it later must not make rows already in the database unreadable. Write the rule as a method on
the value object — `assertEnoughToPublish()` — and call it from the manager. The type stays
constructible; the rule stays in one place and is enforced where the use case runs.

**A value object built from external config** (a threshold, a batch size read via
`@Value`) is constructed at its call site, not cached as a field built once at startup.
Caching turns Spring context startup into implicit validation of that config — appealing,
but a stronger guarantee than the same type gives anywhere else it is used, and one that
buys eager failure by coupling the value object's construction to the application's boot
sequence rather than to the work it is about to do. Build it inline in every method that
hands it to a manager, the same way a timestamp value object usually already is there
instead of cached: a misconfigured property then throws from the value object's own
assertion the first time it is actually needed, not at boot. Record that as a deliberate
trade (an ADR) rather than guarding against it with an eager pre-validation call — the
lazy failure is the intended result, not a regression to catch.

A value object never takes a port. `Course.enrol(studentId, waitingListPort)` looks
convenient and is the wrong shape: it drags the outside world into a type whose whole value
is that it is inert, and it makes one type responsible for both creating and reconstituting.
Loading, saving and anything that calls out belong to the manager, which is what ports are
for.

Read the assertion you are calling before relying on it. `Assert.field("seats", seats)
.positive()` accepts zero; `.strictlyPositive()` is the one that does not. A value object
whose javadoc and whose assertion disagree is worse than one with no javadoc.

`AssertTest` pins that boundary for every numeric type. If you need a bound the asserters
do not express, add it there with a test rather than open-coding the check in a value
object, where the next aggregate cannot reuse it.

**A value that is sometimes absent** is two different problems, and they take different
shapes. Where one field on an otherwise-unchanged type is simply not supplied by every
source — a score no catalogue always has, a duration only one source provides — make the
field nullable and answer it through an `Optional<T>` accessor; everything else about the
type stays as it was, and `composite_domain_types_hold_value_objects` still holds because the
field is a domain type, just possibly unset.

Reach past that for a sealed type the moment more than one thing varies together. A result
that either carries several fields or carries none of them — never one without the others —
is not "one field missing," it is two shapes, and a nullable field only documents that as a
comment the next caller can forget to read. Split it: a `sealed interface` with one record
variant per shape puts the invariant where the compiler enforces it, and a caller pattern-matches
instead of reading past a null check that may or may not be there. Default to the first
shape — it costs one field and an `Optional` — and reach for the second only once a nullable
field would need a comment explaining which other fields it drags with it.

**Identities** are records wrapping a `UUID`, one per aggregate. Distinct `CourseId`
and `StudentId` types make it impossible to pass one where the other is expected —
a mistake `UUID` everywhere invites.

**Domain services** are records taking the ports they need, named `<Aggregate>Manager`.
Reach for one when a sequence has to be fixed: `CourseManager.enroll` loads the course,
asks it whether a seat is free, and saves, and those three steps must not be reordered or
half-copied into a caller. It lives in `domain`, not `application`, because that ordering
is a rule. Pass-through methods on it are fine — they keep callers to one entry point.

The manager is also where the use case's rules run, in the order that makes them cheapest
to fail: check what costs nothing before what costs a query, and query before you spend a
expensive call. That ordering is itself worth a test —
`verifyNoInteractions(courses, waitingLists)` on the refused-input path pins it, and nothing
else will.

**Use case input** with more than one part gets a record of its own — `EnrolStudent`, not
`enrol(courseId, studentId)`. It gives the request a name in the ubiquitous language, keeps
the port and service signatures stable as the use case grows, and gives the fixtures
somewhere to hang variants (`enrolStudentIntoAFullCourse()`).

**Ports** are interfaces in `domain`, named for what the domain needs rather than for
what implements them. `CoursePort`, not `JpaCourseAdapter`. The domain declares the
requirement; infrastructure satisfies it.

Only a domain service *holds* a port. An adapter implements one and never depends on
another: an adapter holding a port is a second place deciding what a missing row means, and
the manager stops being the only entry to the use case. Nor may a driven adapter reach into
the application layer — that inverts the direction everything else points. When an adapter
genuinely needs a row, it uses the Spring Data interface beside it in `secondary`. A port
method no manager calls should not be on the port at all.

**A manager depends on ports only, and never on another manager** — the same rule as the
adapter's, one layer up. `EnrolmentManager(CoursePort, WaitingListManager)` looks like reuse
and is the wrong shape: it makes `EnrolmentManager` a second place deciding what
`WaitingListManager`'s use case means, the same borrowed authority a port-holding adapter
would have. Where a manager's own use case genuinely needs a decision another manager makes,
take that manager's port directly and re-implement the small decision inline — cheap
duplication is the price, not a reason to nest — or, where the decision is large enough that
duplicating it would itself be the bug, wire both managers into the `*ApplicationService`
instead and have it call one, then the other, passing the first's result to the second. The
call is per case, not a blanket preference for either shape.
