# start

`ticket-tracker` below is `${CLAUDE_PLUGIN_ROOT}/scripts/ticket-tracker`; it is the only way to
reach GitHub.

Run `ticket-tracker ready <n> start` first. It refuses, with the reason, a ticket in `draft` (it needs
`/ticket refine <n>` first: a draft is a captured sentence, not a decision, and starting one means
the design gets made at the keyboard by whoever picked the ticket up), a ticket whose *Model decision*
is empty or still the unanalysed marker (the status says it was analysed; the empty section says it
was not, and the section is the one telling the truth), a ticket touching `frontend/**` whose *Design
direction* is missing or still the unanalysed marker, and any ticket it cannot read. Do not start past
a refusal.

Then:

1. `ticket-tracker move <n> in-progress`.
2. `ticket-tracker develop <n>`, which creates `<n>-<title-slug>` through GitHub's issue-branch linking, linked to
   the issue by GitHub, and prints its name; `--checkout` also checks a new branch out, and `checkedOut` says whether it did. Add a worktree on that
   branch if the current one has uncommitted work worth keeping. If it reports the branch already
   existed (`"existing": true`), or a local branch of that name is already there, diff it against main
   before reusing it: an abandoned attempt that forked long ago will bring deleted files back. Rename
   it aside (`<n>-stale-<date>`), say so in one line, and branch fresh.
3. Dispatch the agent for what the ticket touches, from the Delegation table below, and
   tell it to work test-first and domain outwards: write one failing test, run it and see
   it fail for the reason the test names — a test that passes on first run proves
   nothing — then the least code that turns it green, then the next test. One test at a
   time, not the suite up front: tests written before any code pin the shape you
   imagined rather than the behaviour that emerged. It runs
   `make test` as it goes — the architecture rules fail on a misplaced
   class immediately, which is cheaper than finding it in review. `backend-ddd` loads the
   `ddd-backend` skill itself for the shape each test takes; invoke either skill directly
   only when the work is small enough to stay inline.
   Hand the `frontend` agent the ticket's *Design direction* along with its criteria.
4. Write the boundary case first where the ticket has one. A rule tested only in the
   middle of its range passes with an off-by-one in it.
5. If the API surface changed, recapture the schema: `make run`, `make openapi`,
   `make openapi-client`. Running only the last regenerates types from a stale schema.
6. Apply the *Glossary impact* to `docs/glossary.md` in this change, not later.
7. Commit subjects say the change in words and carry no ticket id; the pull request body is where
   `Closes #<n>` goes (`review`).

## Delegation

Choose the implementation agent from what the change touches, not from what it is about:

| The change touches | Agent |
|---|---|
| `src/**` inside a bounded context | `backend-ddd` |
| `frontend/**` | `frontend` |
| `Makefile`, `compose.yaml`, `Dockerfile`, `.github/**`, `scripts/**`, or the build itself | `devops` |

A ticket touching two of those rows is two dispatches in dependency order, not one agent
working outside its brief.

Stay inline when the whole change is a file already read this session. Dispatching costs a
cold start and a re-read of context the session already holds. Agents are named here
because role-specific judgement at implementation is worth that cost — not because
delegation is better by default.
