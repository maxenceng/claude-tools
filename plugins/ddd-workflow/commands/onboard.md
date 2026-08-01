---
description: Build an understanding of this project and refresh its architecture docs
---

Bring yourself up to speed on this project, and leave its documentation more accurate
than you found it.

## Investigate

Delegate the reading to the `codebase-explorer` agent so the file contents stay out of
this conversation. Ask it for the functional purpose of the project, the bounded
contexts and their relationships, where the business rules live, and anything where
the code and the documentation disagree.

If the project is large, dispatch one explorer per bounded context rather than one for
everything — each returns a summary, and the summaries are what you keep.

## Refresh what has drifted

Regenerate the derived documentation:

```bash
make docs
```

Then compare what the explorer found against what the project claims:

- `docs/context-map.md` — are the listed contexts the ones that exist?
- `docs/glossary.md` — does the code use these words? Add terms that appear in code
  but not here; flag synonyms that have crept in.
- `docs/adr/` — are there decisions visible in the code with no recorded reasoning?

Update the files where the code is clearly right and the document is stale. Where they
disagree in a way that suggests the code is wrong, do not edit either — report it.

## Report

Write a short orientation: what the project does, how it is structured, where the
interesting logic lives, and what to be careful about. Then list the drift you found
and what you changed.

Mention any missing ADR you noticed. A decision visible in the code with no recorded
reasoning is the thing most likely to be accidentally reversed later.
