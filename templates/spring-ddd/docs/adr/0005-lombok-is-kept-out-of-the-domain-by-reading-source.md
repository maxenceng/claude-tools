# 5. Lombok is kept out of the domain, and the guard reads source

Date: 2026-08-21

## Status

Accepted

## Context

Lombok is a dependency of this project and earns its place in `infrastructure.secondary`, where a
JPA entity is a mapping written for a framework and read as one. `@SuperBuilder` and `@Setter` on
an entity save real repetition and hide nothing a reader needs.

The domain is the opposite case. It is the part of a codebase meant to be read as prose by someone
deciding whether a rule is right, and a generated accessor is one that cannot be read at the place
it is used. `error.domain` already sets the example: its exception builders are written out by
hand.

The trap is in the enforcement. `domain_is_free_of_frameworks` names packages, so adding
`lombok..` to it looks like the whole fix. It is not one at all: **Lombok's annotations are
`SOURCE`-retention.** The compiler erases them along with the imports that named them, and every
ArchUnit rule reads bytecode. The rule sees the generated members, which are indistinguishable
from hand-written ones, and passes. This is not theoretical — it was verified by annotating a
domain type with `lombok..` already in the package list and watching every rule report green.

## Decision

`DomainIsFreeOfLombokTest` walks `src/main/java`, takes every `.java` file whose parent directory
is `domain`, and fails on any line mentioning `lombok`.

`lombok..` stays in `domain_is_free_of_frameworks`, but as a second line rather than the first: it
catches a Lombok type that survives compilation — `@NonNull` is `CLASS`-retained — and catches
nothing else. **Do not read that package list as the guard.** The `because` clause on the rule says
so, and this ADR is why.

Only `src/main/java` is scanned. Tests are free to use Lombok; nothing in `src/test/java` is a
domain type.

## Consequences

A domain type is written out in full: fields, accessors, `equals`/`hashCode` where equality
matters, and a builder if construction needs one. That is the price, and `error.domain` shows the
shape.

Matching the bare word `lombok` catches a comment or a javadoc mentioning it, not only an import.
Accepted as noise worth having — the false positive is loud and instantly understood, while a rule
matching only imports would miss a fully-qualified `@lombok.Getter` on a declaration.

This is the second rule in this project that reads source rather than bytecode, after ADR 0004,
and both exist for the same reason. That is the bar for a third.
