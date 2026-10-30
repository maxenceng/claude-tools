# done

`ticket-tracker` below is `${CLAUDE_PLUGIN_ROOT}/scripts/ticket-tracker`; it is the only way to
reach GitHub. This step runs after the merge. Its first move is `ticket-tracker show <n>`: keep the
`updatedAt` it returns for the write in step 3.

1. Confirm the work is merged. The `ticket-tracker done` call in step 3 is that check: it refuses
   when no branch that `develop` linked to the ticket has a merged pull request and no merged pull
   request names it with `Refs #<n>` or a closing keyword, and says so;
   then stop. Make that call before steps 4 to 7: the rest of this step writes a record of what
   landed, and nothing has landed yet.
2. There is no status to set. The merge's `Closes #<n>` closed the issue as completed, and a
   closed-as-completed issue is `done` whatever labels it still carries. Closing the ticket now
   writes files only if the work below changes any, and then it lands on a branch and a PR like
   any other change — `start` said this and the habit does not survive a step that does not repeat it.
3. Fill in *Notes* with anything the code will not show — an approach rejected, a
   constraint found. Skip it if there is genuinely nothing; padding trains people to stop
   reading the section. Put the text in a file and run
   `ticket-tracker done <n> --notes-file <file> --expect-updated-at <updatedAt>`. In one edit it
   writes the *Notes* section into the issue and removes every leftover `status:` label; if the
   issue is still open — the keyword was missed, or the pull request said `Refs` because the ticket
   had steps left after the merge — it closes it as completed and says so.
   With nothing to write, run `ticket-tracker done <n>` alone for the labels and the close.
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
   the Skill tool) on each, passing this ticket's issue number as the trailing argument so it
   lands in `tickets` — for example, `/trace-endpoint POST /api/orders 12`.
   For an endpoint the ticket removed, delete its `.md` and `.html` and its line in
   `docs/endpoints/README.md`.

   A frontend-only ticket usually touches no endpoint. Say so and move on rather than
   tracing something to show the step ran.

   Whatever files this step changes go on one branch and one PR, opened with
   `ticket-tracker pr-create --title "<the change, in words>" --body-file <file> --refs <n>`: it
   closes nothing, since the issue is already closed, and a body with a closing keyword is refused.
   Open that PR only if this step changed files; with no change there is no branch and no PR.
7. Ask whether this ticket taught `ddd-backend`, another shared skill, or an agent's
   instructions something worth keeping — a convention this project only discovered under
   review, a pattern an ADR here now documents generally rather than for this project alone.
   If so, carry it back into the `claude-tools` repo, in its own change: edit the plugin
   source and bump its `plugin.json` version, never the installed copy under
   `~/.claude/plugins/cache/`. A cache edit is invisible to every other project using the
   plugin and is overwritten by the next update or reinstall, which is exactly how a shared
   skill silently falls behind the projects it is meant to guide.

   A case that came up only once still gets asked about. It is not dropped because it fell
   short of step 4's threshold. List each one: a review correction made once, a convention
   found once, an approach rejected once. Ask the user about each case as its own question,
   with the comment or commit it came from. Offer three answers: carry it into a named
   shared skill, keep it in this project, or drop it. Do not batch the cases into one
   yes/no, and do not pre-filter the ones that look too small. Deciding whether a one-off
   generalises is the user's call. A correction the next project will hit again looks just
   like a one-off the first time.
