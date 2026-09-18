---
name: project-retro
description: Find repetition worth automating — repeated manual command sequences, repeated corrections, and duplicated code — and turn each into a script, a Makefile target, a build check, or a rule. Takes an optional effort level (low/medium/high) controlling scan depth. Use at the end of a work session or when something feels like it has been done before.
---

# Turning repetition into automation

Two kinds of repetition are worth catching, and they have different fixes.

## Effort

Takes an optional effort level as an argument — `low`, `medium` (default), or `high` —
controlling how much history and how deep a duplication scan to pull in. Repeated
corrections are always in scope at every level: they cost nothing to check, since the
conversation already has them.

| | `low` | `medium` | `high` |
|---|---|---|---|
| Repeated work | conversation only, skip `git log`/`git diff` | `git log --oneline -30`, `git diff --stat HEAD~5` | `git log --oneline -100`, `git diff --stat HEAD~15`, and a `git log --all --grep` for the same kind of change further back |
| Duplicated code | skip `make dup` | `make dup`, read the report | `make dup`, and read the flagged files themselves where the report's context is too thin to judge |

Use `low` for a quick end-of-session pass when nothing about the session felt
repetitive. Reach for `high` only when a `medium` pass found something worth digging
into further, not by default — the wider windows cost real tokens for a scan that
usually confirms what the narrower one already found.

## Repeated work

Look at what actually happened in this session and in recent history, at the window
your effort level sets (see *Effort* above):

```bash
git log --oneline -30
git diff --stat HEAD~5
```

Ask what was done more than twice by hand. Typical finds are a fixed sequence of
commands run before every commit, the same file edited alongside another every time,
a manual setup step needed after every clone, or a check performed by reading code
that a tool could perform.

Then pick the cheapest durable fix, in this order:

1. **A build check** — if the repetition is verifying something, make it fail the
   build. A rule that fails automatically is never forgotten and costs nothing to run.
2. **A Makefile target** — if it is a command sequence. Add it to the `Makefile` so it
   is written once and callable by humans, CI, hooks, and agents alike.
3. **A hook** — if it should happen automatically after certain edits.
4. **A skill** — if it is a judgement-based procedure rather than a command.
5. **A script in `scripts/`** — when the logic is too involved for a Make recipe.

Prefer the earliest option that fits. A rule enforced by the build beats a rule
written in a document, because the document is advisory and the build is not.

## Repeated corrections

Corrections are the highest-value signal in the session, because each one will recur
until something changes. Look for guidance given more than once — a convention that
had to be restated, a wrong assumption made twice, an approach rejected repeatedly.

Fix the cause rather than the instance:

- Recurring architectural correction → add a rule to `ArchitectureTest`. Now it fails
  rather than needing to be said again.
- Recurring naming or vocabulary correction → add the word to `docs/glossary.md`,
  including the word being displaced.
- Recurring "why did you do it that way" → the reasoning is missing. Write an ADR.
- Recurring convention correction → it belongs in the relevant skill, not in CLAUDE.md,
  so it loads when relevant instead of on every request.

## Duplicated code

Skip this section entirely at `low` effort. Otherwise:

```bash
make dup
```

Read the report rather than the codebase — the scan is free and reading source to
hunt for duplication is not.

Not all duplication should be removed. Two blocks that look alike but change for
different reasons should stay apart; merging them creates a shared thing pulled in two
directions, which is worse than the duplication. Before extracting, ask whether both
copies would really change together. If the answer is no, leave them and consider
raising the `cpd.minimumTokens` threshold instead.

When extraction is right, put the result where it belongs in the architecture — shared
domain behaviour goes on the domain type, not into a `Utils` class.

## Reporting

For each item, state the repetition observed, the fix, and where it should live. Keep
the list short and ranked by how often the repetition actually occurred — three real
automations beat twelve speculative ones.

Then apply the ones that are clearly right, and ask about the ones that are judgement
calls.
