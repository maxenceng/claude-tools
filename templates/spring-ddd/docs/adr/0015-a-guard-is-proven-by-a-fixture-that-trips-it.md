# 15. A guard is proven by a fixture that trips it

Date: 2026-10-09

## Status

Accepted.

## Context

A guard under `scripts/check-*` is watched to fail once, on the day it is written, and never
made to fail again. A glob that stops matching, a branch no longer reached, or a message that
drifts all leave it green while it checks nothing — and a green guard is read as protection.

## Decision

Each Python guard has a fixture tree under `scripts/fixtures/<name>/` holding the files that
trip the one branch it exists for. `scripts/guard-fixtures.py` globs `scripts/check-*` and runs
each as a subprocess with its working directory and `CHECK_ROOT` set to its fixture tree, then
asserts a non-zero exit *and* the message of the intended branch — exit code alone would pass
a guard that only tripped its own "scanned nothing" branch. A surefire report with a skip is
synthesised at run time, since `.gitignore`'s `target/` would drop a committed one.

Every `scripts/check-*` must be registered. `check-openapi.sh`, whose failure case is a running
application, is registered as proven by its own boot: it diffs a deliberately mutated copy of
the committed schema through the same `schema_matches` comparison before the real one.

`scripts/prove-guard-harness.py` proves the harness: it mutates the registry in memory and
asserts each way of proving nothing is rejected. It is named `prove-*`, not `check-*`, so it
needs no fixture of its own; that is where the regress stops. Both run in `make ci`.

## Consequences

A new guard is not mergeable until it has a fixture, which is the default "watched to fail"
made mechanical.
