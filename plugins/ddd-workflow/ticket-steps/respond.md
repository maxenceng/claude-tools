# respond

Feedback has arrived on the PR and the branch has to answer it. The ticket stays
`in-review` throughout — this step changes code, not status, and it repeats as often as
the conversation does.

1. Collect all of it before changing anything. Comments arrive at three different
   endpoints, and reading one of them silently drops the rest:

   ```
   gh api repos/{owner}/{repo}/pulls/<n>/comments    # inline, anchored to a line
   gh api repos/{owner}/{repo}/issues/<n>/comments   # top-level, on the PR
   gh api repos/{owner}/{repo}/pulls/<n>/reviews     # review summaries
   ```

   If all three come back empty, say so and stop. There is nothing to answer, and
   inventing something to change is worse than reporting an empty round.

2. Invoke the `superpowers:receiving-code-review` skill and follow it. Check each item against this
   codebase before implementing it, and push back with reasoning where a comment is wrong
   here. A reviewer is often right that something is wrong and wrong about what to do —
   an item worth acting on can still need a different fix than the one suggested.

3. If any item is unclear, ask about every unclear item before implementing any of them.
   They relate to each other, and a half-understood set implemented in order produces a
   change nobody asked for.

4. Run `make ci`, then commit the whole answer as one change and push it to the same
   branch. Subject line and at most a sentence; the threads carry the reasoning. Do not
   close and reopen the PR — the threads are the record of the exchange and do not
   survive it.

   Push here rather than at the end. CI is evidence you are about to need, and it takes
   minutes to arrive.

5. Re-check every acceptance criterion the change could have invalidated, against the
   pushed commit. Evidence gathered before the change does not cover the code after it,
   and a review fix that removes a dependency or a setting invalidates more than it
   looks.

   Read the CI run before deciding a criterion is unverifiable. The job starts services
   and boots the application, so it demonstrates things a local shell may not be able to
   — a criterion you cannot exercise on this machine is often already green in the
   pipeline. Unticking one that CI just proved, then re-ticking it, is churn in the
   history and a correction in public.

6. Untick any criterion nothing now demonstrates, rather than leaving the tick and
   quietly re-earning it. Say which ones and what would re-earn them.

7. Reply in each comment's own thread rather than as a new top-level comment:
   `gh api repos/{owner}/{repo}/pulls/<n>/comments/<id>/replies`. One or two sentences:
   what changed, or why nothing did. A silent fix leaves the reviewer diffing the branch
   to work out whether they were heard, and a disagreement that is never written down
   gets raised again by the next reader.

   Match the reviewer's register. Someone who writes "remove this, I know how Docker
   works" is telling you the explanation was the problem; a paragraph defending the fix
   repeats it.
