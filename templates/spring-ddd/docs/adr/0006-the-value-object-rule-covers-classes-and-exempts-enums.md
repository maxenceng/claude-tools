# 6. The value-object rule covers classes, allows three carriers, and exempts enums

Date: 2026-08-21

## Status

Accepted

## Context

`composite_domain_types_hold_value_objects` is the rule that stops a raw `String` or `int` being
spread across the domain types that use it: a type holding two or more components must name each
one. It is the most opinionated rule in `ArchitectureTest` and the one most likely to be met with
"it is only a string".

Three things about its first shape were wrong in ways that do not announce themselves.

**It selected `.areRecords()`.** A record is the usual way to write a value object here, so the
selector reads as harmless. It is not: model an aggregate as a class — because it has subtypes, or
because a base wants to hold shared fields once — and the rule silently stops applying. Nothing
fails. The guard is simply gone from the types that most need it, and the next person to add a raw
field is told nothing.

**It rejected every `java.*` component**, which includes `java.util.List`. That pushes every
collection into a single-field wrapper type — a `Genres` around a `List<Genre>` — and those
wrappers earn nothing. The element type already names the value; the list is a shape.

**It never covered enums**, for the same reason it never covered classes. An enum whose constants
carry a label and a pattern sat outside the rule from the day it was written.

## Decision

The rule covers every type in a `..domain..` package that is not in `..error..`, is not an enum, is
not a `Throwable`, and is not named `*Builder`, whenever it holds two or more instance fields.

Three raw types are allowed as components and nothing else: `java.util.List`, `java.util.Map`, and
`Pair` matched by simple name. They are carriers — shapes rather than values — and what they carry
is already a domain type. Everything else under `java.` and every primitive stays rejected.
`boolean` stays exempt: there is nothing to validate and no name worth inventing. A type with
fewer than two components is skipped, because a single-component record *is* the value object the
rule asks for.

**Enums are exempt on their own argument**, not as a convenience. An enum is already a closed
vocabulary: the type is the value object, and its instance fields are the definition of its
constants rather than state a caller composes and varies. The rule exists to stop a raw value being
spread across the types that use it, and nothing is spread when the type owns every value there is.

## Consequences

Dropping the selector and allowing the carriers belong together. Either alone is wrong: covering
classes while rejecting `List` makes the rule stricter than anyone wants, and allowing `List`
while only covering records leaves the hole open.

The rule now applies to types nobody had checked against it. Widening it in an existing codebase
should be expected to find something on the first run — that is the rule working, not a false
positive, and the fix is to wrap the value or to argue the exemption in an ADR of its own.

`Pair` is admitted by simple name, which is looser than the other two: any type so named, from any
package, passes. Accepted knowingly — no `Pair` ships here, and tightening it to a fully qualified
name is a one-line edit the day one arrives.
