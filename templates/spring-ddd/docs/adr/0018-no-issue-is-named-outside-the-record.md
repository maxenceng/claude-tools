# 18. No issue is named outside the record

Date: 2026-10-29

## Status

Accepted. Supersedes ADR 0016.

## Context

ADR 0016 failed the build on a done ticket's id named outside the record, reading `status:` from
`docs/backlog/`. On Issues the merge itself closes the ticket, so a pull request that names `#42` in
`src/` is green when it merges and fails the next build of `main`. Knowing which issues are closed
would need the network and a token inside `make verify`.

## Decision

Outside `docs/adr/`, `docs/research/`, `docs/endpoints/` and `scripts/`, no file names an issue: not
`#n`, not an issue URL, open or closed. Those folders are exempt because they are meant to read as
history. `make ticket-check` (`scripts/check-ticket-references.py`) enforces it and never calls GitHub.

An issue URL fails in any text file. A bare `#n` fails only in Java and Markdown: in a stylesheet or a
frontend source `#123` is a colour, and in a workflow, a Makefile or a build file `#` opens a comment.
In Java and Markdown it fails, with a Markdown anchor (`#12-section`) and an HTML entity
(`&#35;`) let through. A scan that matches no file fails. The guard has a fixture that trips it, with a
stylesheet colour beside the references to prove the colour does not count (ADR 0015).

A commit subject says the change in words and carries no ticket id; the pull request body carries
`Closes #n`, and the squash adds the pull request's number. `/trace-endpoint`'s `tickets:` takes issue
numbers, and `docs/endpoints/` is exempt.

## Consequences

- A pointer to an open ticket from code, such as "the type #42 will share", is no longer allowed. A
  deliberate limit says what closes it in a `deferred:` comment instead.
- The check cannot tell an issue number in a Java string from one in a comment; none is allowed in
  either.
