# respond

Feedback has arrived on the PR and the branch has to answer it. The ticket stays
`in-review` throughout — this step changes code, not status, and it repeats as often as
the conversation does.

1. Collect all of it before changing anything, in one call. Feedback lives in three
   places — inline threads, top-level comments, review summaries — and reading one of
   them silently drops the rest. The script fetches them through GraphQL rather than the three REST
   endpoints: REST returns every comment wrapped in its diff hunk, a full user object and
   a dozen URLs, which is most of what this step used to cost, and it cannot tell a
   resolved thread from a live one — `isResolved` exists in GraphQL alone.

   `ticket-tracker pr-feedback <pr-number>` (`${CLAUDE_PLUGIN_ROOT}/scripts/ticket-tracker`, the only
   way to reach GitHub) returns it as one JSON object: `ci` (the state of the last commit's checks),
   `threads` (unresolved only, each with `path`, `line`, `anchor` and its `comments`), top-level
   `comments`, `reviews` with a body, and the PR `body`.

   Answer unresolved threads only; the filter already drops the rest. A thread's first
   comment's `databaseId` is the id step 8 replies to. `anchor` is the line the comment sits
   on, keeping only that line of the hunk: a leading `+` or `-` means it changed, a space
   means it is context. A `null` line means the thread is outdated. A red `ci` belongs on the list too — the
   pipeline is a reviewer that always comments. Read it with `gh run view <run-id>
   --log-failed`, not the full log: the failing step is the comment, the rest is noise
   priced per line.

2. Then read the PR body for an `Open` section: the decisions `review` could not make.
   That is the other half of the round — not feedback waiting on the branch, but the
   branch waiting on a human.

   If comments exist, answer them. If none do and an `Open` section does, the PR is not
   idle, it is blocked: say what on, one line per item, and ask. Do not answer your own
   open question because nobody else has yet — a fork settled by the session that raised
   it is the fork going unreviewed.

   Put every open item to the human in one batch, each with the trade-off named and a
   recommendation. Each round trip costs a session, and items open at the same time are
   usually entangled — answered one at a time, the first decision constrains the rest
   before anyone has seen them. This is the same instruction as step 4 and for the same
   reason; where both apply, they are one batch and not two.

   When the answer comes back in the session rather than on the PR, put it on the PR as
   well. A decision that lives only in a transcript is one the next reader re-asks.

   Only when threads, comments and reviews are all empty, CI is green and nothing is open is the round genuinely
   empty. Say so and stop; inventing something to change is worse than reporting it.

3. Where an agent applied the comments, check its report against the tree before trusting
   it: diff what you asked for against `git status` and read the files that matter. An
   agent reports what it remembers doing, and an interrupted-and-resumed one drops whole
   items silently.

   Check each item against this codebase before implementing it, and push back with
   reasoning where a comment is wrong here. A reviewer is often right that something is
   wrong and wrong about what to do — an item worth acting on can still need a different
   fix than the one suggested. In particular:

   - A terse comment anchored on a context line is not satisfied by the diff around it.
     The reviewer is pointing at a line that should have changed and did not; work out
     what change would touch it before deciding the comment is already answered.
   - A comment names one instance, not the only one. Grep the whole PR for the same
     shape and fix every occurrence. Occurrences outside the PR go to the human as a
     follow-up ticket to accept or decline, not into this branch.
   - Where the suggested mechanism would break but the direction is sound, say what
     breaks and build what the reviewer was after another way.

   - A request to "do it properly" — add metrics, a filter, a config option — starts with
     a grep for callers. Nothing calls it: say so and propose removing it instead.
   - A comment that contradicts a decision the human already made, in the ticket's
     *Model decision* or an ADR, is put to the human, not implemented.
   - Disagreement goes to the human in this session, in step 4's batch, before any code
     changes or any reply is posted. A rebuttal posted on the thread that the human then
     overrules costs a second round, and the comment may have been a deliberate test.
   - An item you cannot verify from here gets said as much — what you would need to
     check it — rather than applied on trust.

4. If any item is unclear, ask about every unclear item before implementing any of them.
   They relate to each other, and a half-understood set implemented in order produces a
   change nobody asked for.

   On a frontend ticket, map design comments to moves first; see *Design feedback* below.

5. Apply every item, then run `make verify` once — not after each fix. The items were
   checked against the code in step 3; a full pipeline run per comment buys the same
   evidence several times over. Run the one test an item touches while working it if
   you need the signal. Then commit the whole answer as one change and push it to the
   same branch. Subject line and at most a sentence; the threads carry the reasoning. Do not
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
   `ticket-tracker pr-reply <pr-number> <id> --body-file <file>`, where `<id>` is the
   `databaseId` of the thread's first comment — GitHub refuses a reply to a reply. One or two sentences:
   what changed, or why nothing did. A silent fix leaves the reviewer diffing the branch
   to work out whether they were heard, and a disagreement that is never written down
   gets raised again by the next reader.

   State the change, not gratitude or agreement — "Fixed: the guard now runs before the
   save", not "Great catch, thanks!". The diff is the acknowledgement. Where you pushed
   back and the reviewer turns out right, say so in a sentence and fix it, without
   defending the first answer.

   Match the reviewer's register. Someone who writes "remove this, I know how Docker
   works" is telling you the explanation was the problem; a paragraph defending the fix
   repeats it.

## Design feedback

On a frontend ticket, translate a design comment into one of impeccable's named moves
before acting on it — "too loud" is `quieter`, "feels generic" is `bolder`, "cluttered" is
`distill` — and apply it through the `impeccable:impeccable` skill. Name the move in the
reply. A named move is something the reviewer can ask for again and recognise when they
see it; a one-off tweak is neither. Feedback no move fits is applied as written.
