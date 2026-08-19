# review

1. Set `status: in-review`.
2. Run `make ci`, and `make fe-check` if the frontend changed. Report what actually
   passed — not what should pass.

   `make ci` is not the pipeline. Read `.github/workflows/` and account for every step
   the job runs, because the workflow adds steps beyond it — a schema capture that boots
   the application needs whatever the application needs to start. A criterion that says
   "`make ci` passes" can be true while the build is red for the whole branch.
3. Dispatch `architecture-reviewer` for the modelling: does the behaviour sit where the
   ticket said it would, and does the language hold? Hand it the ticket's *Model
   decision* and the diff, so it reviews against what was decided rather than against
   taste.
4. Then run a general code review for correctness — `/code-review`, or the
   `pr-review-toolkit` reviewers. This plugin ships no general reviewer on purpose. They
   are separate reviewers with separate jobs; collapsing them buries the modelling
   findings in style noise.

   Scope both, because a reviewer is a cold start: it re-reads what this session already
   knows, and it costs the running sum of everything it opens rather than the last file.
   Name the files the correctness review should read and tell it not to open the whole
   branch diff. On a second round, skip `architecture-reviewer` where the modelling has
   not moved — re-reviewing what did not change buys the same report at full price.
5. Act on what came back before pushing, and do not stop to ask.

   A finding with one obvious fix and no design choice gets fixed here, together with the
   test that would have caught it. A finding that forks the design does not: it goes in
   the PR body under an `Open` heading, written as the decision it needs rather than as a
   fix. Push either way.

   Check a finding against the code before acting on it. A reviewer reads the diff and not
   always the file the diff lands in, so it will name a cause confidently and get it
   wrong, and a fix aimed at the wrong cause is worse than the defect, which at least sat
   still. Where a finding contradicts a javadoc or an ADR that argued the opposite on
   purpose, that contradiction is itself the finding — settle it in favour of the recorded
   decision, or say in the PR why the decision no longer holds.

   Stopping to ask here is what strands a branch. Nothing is pushed, no PR exists, and
   `respond` has no comments to read, so the round is lost rather than paused. The PR is
   the channel between verbs, and a fork is answered by a human on it — which is what
   `respond` is for.
6. Push and open a PR whose body links the ticket file and lists the acceptance criteria
   with their outcomes. Feedback arriving on that PR is `respond` — not a second
   `review`, which would re-run the reviewers over comments a human has already made.

Invoke the `superpowers:verification-before-completion` skill before ticking anything or
reporting that a step passed.

Tick an acceptance criterion only once something demonstrates it. An unticked box is
information; a ticked one that nothing verifies is a lie the next reader will act on.
