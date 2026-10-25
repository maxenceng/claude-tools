# Java idioms

Each of these came back as a review comment, usually terse, on code that otherwise worked.
They are idiom, not design, so they are fixed everywhere they appear in the change — the
flagged line is a sample.

## `instanceof`, not a cast

```java
// no — the javadoc explains why this cannot fail, and a ClassCastException says nothing if it does
VideoGame stored = (VideoGame) contents.findById(game.contentId());

// yes
if (!(contents.findById(game.contentId()) instanceof VideoGame stored)) {
    throw new ContentNotFoundException(game.contentId());
}
```

The same applies to a sealed `switch` whose extra arms exist only to throw: one
`instanceof` with a typed exception says it more directly.

## Streams, not accumulators

An empty list filled in a `for`, a `forEach` that `put`s into a map, and a local
reassigned each iteration all get the same comment, however small the method.

```java
// batches
IntStream.iterate(0, i -> i < ids.size(), i -> i + BATCH)
        .mapToObj(i -> ids.subList(i, Math.min(i + BATCH, ids.size())))

// a keyed result, in order
.collect(Collectors.toMap(Price::store, identity(), (first, second) -> second, LinkedHashMap::new))

// a fold
listings.stream().reduce(stored, VideoGame::withListing, (first, second) -> second)
```

Pass the merge function to `toMap`. Without it, a duplicate key throws where the `put`
it replaced silently kept the last value, so the rewrite changes behaviour.

The point is to avoid mutation, not the `for` keyword. A `forEach` that `add`s, a
collection handed to a helper that fills it, and `new ArrayList<>()` followed by
conditional `add`s are the same accumulator. A list made of parts, some of them
conditional, is a stream of streams:

```java
// no — the out-parameters are filled by both helpers
Set<Path> present = new HashSet<>();
Set<Path> unlisted = new HashSet<>();
listTranscripts(present, unlisted);

// yes — the helper returns a value, and the values combine
TranscriptListing listing = folders.map(this::listFolder).reduce(TranscriptListing.none(), TranscriptListing::and);

// yes — parts, one of them only when a condition holds
return Stream.of(
                Stream.of(heading),
                facts.stream(),
                shown ? Stream.of(footer) : Stream.<Row>empty())
        .flatMap(Function.identity())
        .toList();
```

State that changes over time — a set of folded rows, the changes a loop has seen but not
yet handled — is an immutable value replaced as a whole (`folded = toggled(folded, key)`),
not a collection changed in place. Where the project has PMD, make it fail the build. An
XPath rule over `ConstructorCall` of the mutable collection types inside a
`MethodDeclaration`, a `forEach` whose lambda or method reference calls `add`/`put`/`remove`,
and those calls on a `FormalParameter`, catches all three shapes.

## A loop that ends

A worker thread's loop is `while (!Thread.currentThread().isInterrupted())`, never
`while (true)` left only through an exception. The IDE warns on the second, and the first
says how the thread stops: whoever closes the adapter interrupts it.

## No copy of a field without a reason

`Optional<WatchService> open = service;` before reading `service` twice draws "why create
a variable here?". A local copy of a field is justified only when the field can change
between the reads in a way that matters. Say which way in the code, or read the field
directly.

## Strings

A text block for anything spanning lines — OpenAPI descriptions (a trailing `\` keeps one
logical line), SQL in tests. `"…".formatted(…)` for interpolation, including a one-token
prefix in an exception message. Never `+` between string pieces. Before pushing, grep the
diff for `" + `.

## A string is named, and a count is not compared to zero

A string literal in a method body is a constant waiting for a name: a flag, a key, a state
another system writes. Name it as a `static final` field, once. A literal stays inline
only where it is already a name or a message: an annotation, an enum constant's
arguments, an exception's message, an `Assert` call's field name, and the template that
`.formatted` is called on.

```java
// no — "PENDING" is GitHub's word, retyped wherever a state is checked
return "PENDING".equals(state);

// yes
private static final String PENDING = "PENDING";
return PENDING.equals(state);
```

A method's answer compared to `0` is a question without a name. Ask it by name instead:
`isEmpty()`, or a method the type gains (`rows.hasLines()`, `area.hasNoRoom()`).

```java
// no
if (rows.size() > 0) { … }

// yes
if (rows.hasLines()) { … }
```

Where the project has PMD, make both fail the build. One XPath rule matches a
`StringLiteral` that has none of the exempt ancestors. Another matches an
`InfixExpression` comparing a `MethodCall` to the `NumericLiteral` 0.

## `return switch`, not a statement switch

When the result depends on which kind a sealed value is, each arm yields its result.
Do not let a statement switch mutate a local that is returned afterwards. An arm that
adds nothing (`-> {}`) gives this shape away.

```java
// no — the switch fills a list declared above it
List<String> argv = new ArrayList<>(claude);
switch (command) {
    case NewClaude _ -> {}
    case ResumeClaude resume -> argv.addAll(List.of(RESUME_FLAG, resume.session().value()));
}
return argv;

// yes
return switch (command) {
    case NewClaude _ -> claude;
    case ResumeClaude resume -> Stream.concat(claude.stream(), Stream.of(RESUME_FLAG, resume.session().value())).toList();
};
```

## Unnamed bindings

`case MovieLibraryEntry _ -> ContentKind.MOVIE;` — bind a name only when the arm uses it.
Check every arm of the switch and every `instanceof`, not only the one flagged.

## Warnings

The reviewer reads the CI log, and a new warning on a touched line is a defect of the PR.
Before pushing, grep the build output for `WARNING].*\.java` and `deprecated` on files the
branch changed. Choose a replacement for a deprecated API by compiling with it and reading
the warnings, or its source or javadoc. `javap` signatures do not show `@Deprecated`, which
is how a deprecated method once got replaced with its equally deprecated overload.

Make the compiler fail the build rather than relying on that grep: `-Xlint:all -Werror` in
the compiler plugin, for main and test sources, so a deprecated call, an unchecked cast or a
raw type is red. Fix what it reports when it is switched on; do not suppress it. Turn off
`serial` (`-Xlint:all,-serial`) unless the project really serialises its exceptions. Without
that, every exception needs a `serialVersionUID` that means nothing. The cost of the gate is a
JDK upgrade: a new lint there turns the build red.

## `Optional` is unwrapped where it is checked

An `Optional` checked in one place and unwrapped in another, `if (prompt.isPresent()) …
prompt.get()`, depends on the reader keeping the two together. Hand the value on instead:
`prompt.map(asked -> answer(asked, key))`, and the method that answers takes the value
itself, not the `Optional`. The same goes for a no-argument `orElseThrow()`. Reach the value
through `map`, `or` or `orElse`, or throw a named exception from `orElseThrow(Supplier)`.
Where the project has ArchUnit, fail on a call to `Optional.get()` or to the no-argument
`orElseThrow()` in main sources. It sees both, since they are method calls in the bytecode.

## No `var`

Write the type out: in a local declaration, a try-with-resources, a lambda parameter and a
record pattern alike, in main and test sources. PMD's `UseExplicitTypes` only covers the
first. It misses a record pattern's `var`, and PMD usually does not read `src/test`. A
short script over the sources closes the gap. It has to skip `var` inside comments and
strings, and `var` used as a variable name.
