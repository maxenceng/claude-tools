# 4. Every imported type is named

Date: 2026-08-21

## Status

Accepted

## Context

A wildcard import hides what a file depends on. `import jakarta.persistence.*;` at the head of an
entity says nothing about whether that entity uses `@ElementCollection`, and the reader has to
scan the body to find out. The cost is small per file and compounds across a codebase where the
head of a file is the fastest way to see what a class is entangled with.

`ArchitectureTest` is where this project's rules live, and it cannot enforce this one. ArchUnit
reads bytecode, and imports do not survive compilation — they are a source-level convenience that
the compiler resolves and discards. A rule saying "no wildcard imports" would pass on every
codebase, including one made entirely of them.

## Decision

`ImportsAreExplicitTest` walks `src/main/java` and `src/test/java` and fails on any line matching
an import ending in `.*`, static or otherwise. It reports the file and line, so the fix is
mechanical.

Reading source rather than bytecode is the exception, not the pattern. The test for whether
another one is justified is not "ArchUnit made this awkward" but "ArchUnit cannot observe this at
all" — which is true of imports, of `SOURCE`-retention annotations (see ADR 0005), and of generic
type arguments, and false of nearly everything else.

## Consequences

An IDE set to collapse imports past a threshold will fight this. Configure it not to; the
`.editorconfig` and the formatter settle formatting arguments, and this is one of them.

The check is a plain file scan, so it costs milliseconds and runs inside `make test` with
everything else. It does not need a separate target.

It matches on the import line only. A fully-qualified wildcard cannot exist in Java, so there is
no second form to catch.
