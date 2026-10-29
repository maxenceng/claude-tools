# new

Capture, do not analyse. This step exists so a backlog can be written down in one sitting;
the modelling happens later, in `refine`, one ticket at a time.

`ticket-tracker` below is `${CLAUDE_PLUGIN_ROOT}/scripts/ticket-tracker`; it is the only way to
reach GitHub.

**One idea per line of the argument.** Six lines means six tickets. Write each one down as close to
the words used as the title allows — a captured ticket is a record of what someone asked for, and
rephrasing it into what you think they meant is the one way this step can be wrong.

Ask nothing about design. Not which aggregate, not what the criteria are, not whether it is
one ticket or two. Every one of those is a `refine` question, and asking it here costs the
speed this step exists for. If a line is genuinely two features, capture it as one and note
the doubt in *Notes* — splitting is a modelling decision.

## The one thing to settle

`context:`. Infer it: read `docs/context-map.md`. Most lines place themselves.

For any line you cannot place, ask **once, for all of them together**, naming just those
lines. A capture that stops on each ambiguous idea in turn is the thing this step replaces.

If a line fits no existing context even after asking, leave it without one: a draft may lack its
context, and it reads as unassigned until `refine` places it. Say so in your report. The script
refuses a `context:` label that `docs/context-map.md` does not name, apart from `cross-context`,
so a context is never invented here.

## Writing the tickets

One call per line, in order:

```
ticket-tracker create --title "<the idea, in the words it was given in>" [--context <context>] [--type <type>] [--notes "<only what was actually said>"]
```

`create` opens one issue from `.github/ISSUE_TEMPLATE/ticket.md`, labelled `status:draft`, with the
type `feature` unless the line plainly says otherwise (`--type fix`, `chore`, `spike`). Every
analysis section is left explicitly unanalysed, so that a reader can tell a captured ticket from an
abandoned one. `--notes` takes a constraint mentioned in passing or a doubt about scope, nothing
more.

The issue number GitHub allocates is the ticket's id, and `create` prints it. A call that refuses
(an unknown context, a missing template, no network) wrote nothing; say which line it was and
carry on with the rest.

Report what you captured as a list of number and title, and say which ones need a context decision.
Then stop — do not offer to refine one, and do not refine the first because it looks easy.
