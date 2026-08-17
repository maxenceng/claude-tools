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
5. Push and open a PR whose body links the ticket file and lists the acceptance criteria
   with their outcomes. Feedback arriving on that PR is `respond` — not a second
   `review`, which would re-run the reviewers over comments a human has already made.

Invoke the `superpowers:verification-before-completion` skill before ticking anything or
reporting that a step passed.

Tick an acceptance criterion only once something demonstrates it. An unticked box is
information; a ticked one that nothing verifies is a lie the next reader will act on.
