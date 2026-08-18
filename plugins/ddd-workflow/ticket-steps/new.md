# new

Capture, do not analyse. This step exists so a backlog can be written down in one sitting;
the modelling happens later, in `refine`, one ticket at a time.

**One idea per line of the argument.** Six lines means six tickets, numbered in sequence.
Write each one down as close to the words used as the title allows — a captured ticket is a
record of what someone asked for, and rephrasing it into what you think they meant is the
one way this step can be wrong.

Ask nothing about design. Not which aggregate, not what the criteria are, not whether it is
one ticket or two. Every one of those is a `refine` question, and asking it here costs the
speed this step exists for. If a line is genuinely two features, capture it as one and note
the doubt in *Notes* — splitting is a modelling decision.

## The one thing to settle

`context:`, because the id and the filename are built from it. Infer it: read
`docs/context-map.md` if there is one, otherwise take the prefixes already in
`docs/backlog/`. Most lines place themselves.

For any line you cannot place, ask **once, for all of them together**, naming just those
lines. A capture that stops on each ambiguous idea in turn is the thing this step replaces.

If a line fits no existing context even after asking, that is a new context — capture it
with `context: unassigned` and say so in your report. Do not invent a prefix; an id is
permanent and a wrong one outlives the confusion that produced it.

## Writing the file

Number by taking the highest existing `<CONTEXT>-<n>` for that context and adding one, in
sequence across the batch. `status: draft`, `created:` today's absolute date, `type:` from
the obvious reading of the line — `feature` unless it plainly says otherwise.

Every analysis section is left explicitly unanalysed, so that a reader can tell a captured
ticket from an abandoned one:

```markdown
---
id: CONTEXT-7
status: draft
context: <context>
type: feature
created: YYYY-MM-DD
---

# <the idea, in the words it was given in>

## Acceptance criteria

_Not analysed yet — `/ticket refine CONTEXT-7`._

## Model decision

_Not analysed yet — `/ticket refine CONTEXT-7`._

## Glossary impact

_Not analysed yet._

## Notes

<only what was actually said: a constraint mentioned in passing, a doubt about scope>
```

Report what you captured as a list of id and title, and say which ones need a context
decision. Then stop — do not offer to refine one, and do not refine the first because it
looks easy.
