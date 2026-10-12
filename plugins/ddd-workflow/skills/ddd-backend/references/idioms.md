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

## Strings

A text block for anything spanning lines — OpenAPI descriptions (a trailing `\` keeps one
logical line), SQL in tests. `"…".formatted(…)` for interpolation, including a one-token
prefix in an exception message. Never `+` between string pieces. Before pushing, grep the
diff for `" + `.

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
