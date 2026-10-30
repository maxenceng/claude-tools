# 20. The ADR index is written by a script, and a stale one fails the build

Date: 2026-10-30

## Status

Accepted. Builds on ADR 0015 (a guard is proven by a fixture) and ADR 0019 (`README.md` is a section's index).

## Context

The site's sidebar lists the ADRs by file name, which says neither which ones still hold nor what each decided. A
hand-kept index would say both, and go stale the first time a branch adds an ADR and forgets it; the site would still
show it as complete. No maintained MkDocs or Zensical plugin writes one, and ADR 0019 adds no plugin.

## Decision

- **`make adr-index` writes `docs/adr/README.md`**: one line per ADR in number order, its number, its H1 title linked to
  the file, and its status. `scripts/write-adr-index.py` writes it; `scripts/adr_folder.py` holds the reading of the
  folder it shares with `check-adr-numbers.py`, so the index lists exactly the files the numbering check reads as
  numbered, duplicates and gaps included. The check, not the index, says whether the numbering is clean.
- **The status is derived, not copied.** `Superseded by NNNN.` when a sentence of the *Status* section opens with
  `Superseded by ADR NNNN`, after a full stop or on a line of its own; otherwise the section's first word (`Proposed`,
  `Accepted`, `Rejected`, `Deprecated`) followed by a period. A partial supersession written mid-sentence ("its retry
  limit is superseded by") stays `Accepted.`. An ADR whose heading, number or status cannot be read is refused by
  name, not listed with a guess.
- **`make adr-check` compares the index with what `adr-index` would write and never edits it**, naming the first
  differing line. A check that repaired the file would hide the branch that forgot. The index is not an unnumbered ADR;
  any other unnumbered file in `docs/adr/` still fails.
- **A guard may register several fixture trees in `scripts/guard-fixtures.py`**, one per branch worth proving, and a
  guard registered with none fails. The numbering check has one for a duplicate number, an unnumbered file, a stale
  index, a supersession on its own line, and each of the three refusals.

## Consequences

- Adding or superseding an ADR is two steps: write it, then `make adr-index`. `make ci` fails until the second is done.
- An ADR superseded only in part reads `Accepted.` in the index; the reader opens it for the rest. A supersession
  written with a condition ("once the import moves") reads `Superseded by NNNN.` whether or not the condition has come.
- A new status word means adding it to `STATUS_WORDS` in `scripts/adr_folder.py`; until then the index refuses the ADR.
