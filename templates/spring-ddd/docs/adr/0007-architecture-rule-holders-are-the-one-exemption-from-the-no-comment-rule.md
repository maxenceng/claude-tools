# 7. Architecture rule holders are the one exemption from the no-comment rule

Date: 2026-08-21

## Status

Accepted. Refines [2. Enforce architecture with executable rules](0002-enforce-architecture-with-executable-rules.md).

## Context

`CLAUDE.md` and the `ddd-backend` skill both state that nothing under `src/test/` carries a
comment: the test name is the explanation, and a comment beside it is a second description
of the behaviour that nothing keeps in step, so it rots while the test stays green.

The rule was stated absolutely and enforced nowhere, and the template's own test tree
disagreed with it in four files — which is the worst combination available, because a
generated project copies those files as the example of good style. Prose that the
reference implementation contradicts teaches the contradiction.

Reading the four, the violations were not all the same thing. `AssertTest` had a class
javadoc restating what its method names already said. `ArchitectureTest`,
`TestConventionsTest` and `ModularityTest` had something else: rationale attached to
declarative `ArchRule` fields and to a `ApplicationModules` verification.

That difference is the whole decision. The no-comment rule works because a test is a
*named method* — `shouldNotBuildIfSeatsIsNull` has already said everything a javadoc would
repeat. An `ArchRule` field is not a named method. It is a declarative statement of a
constraint, and the reason the constraint exists has nowhere else in the file to live.
Moving that reasoning out would put the rules in one file and their justification in
another, which is the drift ADR 0002 exists to prevent.

## Decision

Nothing under `src/test/java` carries a comment, with one exemption: a file that holds
architecture rules. Detected by `@AnalyzeClasses` (ArchUnit) or `ApplicationModules`
(Spring Modulith), because those markers are what make a file a description of the
architecture rather than a test of behaviour.

`scripts/check-test-comments.py` enforces it, wired into `make ci`. Comments do not survive
into bytecode, so ArchUnit cannot see this — the same reason `DomainIsFreeOfLombokTest`
reads source ([ADR 5](0005-lombok-is-kept-out-of-the-domain-by-reading-source.md)).

The check fails when *every* test is exempt. A rule that matched nothing has silently
stopped applying, and reporting success while doing it is worse than failing.

## Consequences

The reasoning that used to sit in a comment above a test now goes in the assertion's
`.as(...)` description, where a failure prints it, or in an ADR. `AssertTest` was changed
that way rather than losing what its comments said.

The exemption is detected by a marker string rather than by a type, because the check reads
source. A file that holds architecture rules without naming either marker — a future rule
engine that is neither ArchUnit nor Modulith — would be scanned and would have to move its
reasoning out or extend `RULE_HOLDER_MARKERS`. That is deliberate: the exemption should
cost a deliberate edit rather than widening on its own.

The rule is now enforced for test *sources* only. A comment in a test resource — a fixture
YAML, an `archunit.properties` — is untouched, and `make config-check` governs the config
files it lists. Nothing checks the rest.

deferred: the check reads whole files and re-reads them on every `make ci`, which is
irrelevant at this size and would not be at ten thousand test sources — revisit if `make
ci` ever starts feeling slow at the lint stage
