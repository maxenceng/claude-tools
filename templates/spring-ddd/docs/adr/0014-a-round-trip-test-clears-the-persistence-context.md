# 14. A round-trip test clears the persistence context

Date: 2026-10-09

## Status

Accepted.

## Context

`@DataJpaTest` runs each test in one transaction. A `findById` after a `save` in the same test
is served from Hibernate's first-level cache and issues no SELECT, so the assertion compares a
fixture with itself. It passes against a misnamed column, a missing mapping, or no table at
all — the defects such a test exists to catch.

## Decision

A test that asserts on a value read back from the database calls `entityManager.flush()` and
`entityManager.clear()` between the write and the read, with `EntityManager` injected through
`@PersistenceContext`. Tests that only assert a write was refused do not need it.

`make round-trip-check` (`scripts/check-round-trip-tests.py`) fails a `@DataJpaTest`
`*IntegrationTest` method that writes and reads back without `entityManager.clear()`. A project
with no `@Entity` yet passes; one with an entity and no such test fails, since the check would
otherwise be scanning nothing.

## Consequences

The check reads source, by method, with a pattern: a read-back through a helper it cannot see
is missed. It is a floor, not a proof.
