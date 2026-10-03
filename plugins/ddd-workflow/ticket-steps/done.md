# done

1. Confirm the work is merged. If it is not, say so and stop. Check before anything else:
   the rest of this step writes a record of what landed, and nothing has landed yet.
2. Set `status: done`. Closing a ticket writes files, so it lands on a branch and a PR
   like any other change — `start` said this and the habit does not survive a step that
   does not repeat it.
3. Fill in *Notes* with anything the code will not show — an approach rejected, a
   constraint found. Skip it if there is genuinely nothing; padding trains people to stop
   reading the section.
4. Invoke the `project-retro` skill if anything during the ticket was done by hand more
   than twice, or if the same correction came up repeatedly.
5. Raise an ADR if a decision was made that someone could reasonably reverse later
   without knowing why it was taken. An ADR already written during the ticket counts —
   check before writing a second description of the same decision.

   Read *Model decision* against the code before deciding there is nothing to write. If
   review reversed the modelling, that section now argues for a shape the code does not
   have, and it is the first thing the next person reads. Leave it as written — it is the
   record of what was decided — and write the ADR that supersedes it. A ticket whose
   *Model decision* contradicts the code, with nothing pointing anywhere else, is how a
   settled question gets reopened by someone who thinks they have found a bug.
6. Bring the endpoint atlas up to date. This runs here rather than at `review` because
   only merged code is worth a diagram — a branch's call flow can still change under
   review, and a diagram of a flow that never landed misleads everyone who finds it.

   Trace from up-to-date main: `git fetch origin`, then check out `origin/main` (or
   rebase onto it) before branching for the close-out. A squash-merge rewrites the
   branch's commits, so a trace taken on the feature branch records a `traced_at` that no
   longer exists once the PR lands.

   Find the endpoints the ticket touched: controllers changed in the merged diff, plus
   controllers in the same context whose call path reaches a class the diff changed.
   Invoke the `/trace-endpoint` command (the `ddd-workflow:trace-endpoint` skill, through
   the Skill tool) on each, passing this ticket's id as the trailing argument so it
   lands in `tickets` — for example, `/trace-endpoint POST /api/orders ORDERING-12`.
   For an endpoint the ticket removed, delete its `.md` and `.html` and its line in
   `docs/endpoints/README.md`.

   A frontend-only ticket usually touches no endpoint. Say so and move on rather than
   tracing something to show the step ran.

   All of it goes in the same branch and PR as `status: done`.
7. Ask whether this ticket taught `ddd-backend`, another shared skill, or an agent's
   instructions something worth keeping — a convention this project only discovered under
   review, a pattern an ADR here now documents generally rather than for this project alone.
   If so, carry it back into the `claude-tools` repo, in its own change: edit the plugin
   source and bump its `plugin.json` version, never the installed copy under
   `~/.claude/plugins/cache/`. A cache edit is invisible to every other project using the
   plugin and is overwritten by the next update or reinstall, which is exactly how a shared
   skill silently falls behind the projects it is meant to guide.

## Vikunja

Once `status: done` is written, and only if `VIKUNJA_URL`, `VIKUNJA_TOKEN` and
`VIKUNJA_PROJECT_ID` are all set, move the ticket's task to the bucket titled `done` —
see the Vikunja section of `/ticket` itself for the lookup shape. A correctly configured
done-bucket marks the task done as a side effect of the move; send one more call anyway,
since a board that reads done is worth the extra request and costs nothing if redundant:

```bash
curl -sf -X POST "$VIKUNJA_URL/api/v1/tasks/$TRACKER_ID" \
  -H "Authorization: Bearer $VIKUNJA_TOKEN" -H "Content-Type: application/json" \
  -d '{"done": true}'
```

Skip this section, and say so once, when any of the three variables is unset.
