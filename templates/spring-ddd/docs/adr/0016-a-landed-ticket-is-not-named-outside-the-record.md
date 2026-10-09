# 16. A landed ticket is not named outside the record

Date: 2026-10-09

## Status

Accepted.

## Context

A ticket id is a scheduling artifact. While the work is open, "the type this ticket will
share" is a useful pointer. Once the ticket is done, the same words are a claim about the past
that nothing keeps true, and they read as future work to whoever finds them next. Some can be
caught by tense ("when X-4 declares them"); others ("and from X-4 a show") cannot be told
from history by any pattern.

## Decision

Outside `docs/backlog/`, `docs/adr/`, `docs/endpoints/`, `docs/research/` and `scripts/`, no
file names a ticket whose `status:` is `done`. Those folders are exempt because they are meant
to read as history. Code and living documents name the behaviour instead; git and the ADRs
remember which ticket added it.

`make ticket-check` (`scripts/check-ticket-references.py`) enforces it. Any `PREFIX-n` is a
candidate and only an id a done ticket carries fails, so a context added later needs no edit.
A backlog with no done ticket passes; a scan that matches no file fails.

## Consequences

Closing a ticket can fail the build for a reference written while it was open — the moment to
rename it is the close-out, which is when the reference stops being true.
