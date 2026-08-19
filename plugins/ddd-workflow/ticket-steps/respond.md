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

   Answer unresolved threads only. REST hands back a thread someone already resolved
   looking exactly like a live one; `isResolved` exists in GraphQL alone, on
   `pullRequest.reviewThreads`. A red CI run belongs on the list too — the pipeline is a
   reviewer that always comments.

2. Then read the PR body for an `Open` section: the decisions `review` could not make.
   That is the other half of the round — not feedback waiting on the branch, but the
   branch waiting on a human.

   If comments exist, answer them. If none do and an `Open` section does, the PR is not
   idle, it is blocked: say what on, one line per item, and ask. Do not answer your own
   open question because nobody else has yet — a fork settled by the session that raised
   it is the fork going unreviewed.

   When the answer comes back in the session rather than on the PR, put it on the PR as
   well. A decision that lives only in a transcript is one the next reader re-asks.

   Only when all three endpoints are empty and nothing is open is the round genuinely
   empty. Say so and stop; inventing something to change is worse than reporting it.

3. Invoke the `superpowers:receiving-code-review` skill and follow it. Check each item against this
   codebase before implementing it, and push back with reasoning where a comment is wrong
   here. A reviewer is often right that something is wrong and wrong about what to do —
   an item worth acting on can still need a different fix than the one suggested.

4. If any item is unclear, ask about every unclear item before implementing any of them.
   They relate to each other, and a half-understood set implemented in order produces a
   change nobody asked for.

5. Run `make ci`, then commit the whole answer as one change and push it to the same
   branch. Subject line and at most a sentence; the threads carry the reasoning. Do not
   close and reopen the PR — the threads are the record of the exchange and do not
   survive it.

   Push here rather than at the end. CI is evidence you are about to need, and it takes
   minutes to arrive.

6. Re-check every acceptance criterion the change could have invalidated, against the
   pushed commit. Evidence gathered before the change does not cover the code after it,
   and a review fix that removes a dependency or a setting invalidates more than it
   looks.

   Read the CI run before deciding a criterion is unverifiable. The job starts services
   and boots the application, so it demonstrates things a local shell may not be able to
   — a criterion you cannot exercise on this machine is often already green in the
   pipeline. Unticking one that CI just proved, then re-ticking it, is churn in the
   history and a correction in public.

7. Untick any criterion nothing now demonstrates, rather than leaving the tick and
   quietly re-earning it. Say which ones and what would re-earn them.

8. Reply in each comment's own thread rather than as a new top-level comment:
   `gh api repos/{owner}/{repo}/pulls/<n>/comments/<id>/replies`. One or two sentences:
   what changed, or why nothing did. A silent fix leaves the reviewer diffing the branch
   to work out whether they were heard, and a disagreement that is never written down
   gets raised again by the next reader.

   Match the reviewer's register. Someone who writes "remove this, I know how Docker
   works" is telling you the explanation was the problem; a paragraph defending the fix
   repeats it.
