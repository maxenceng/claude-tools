# start

Refuse to start a ticket whose *Model decision* is empty, and say why. That section is
what separates a ticket from a wish, and filling it in afterwards means it was really
decided at the keyboard.

Then:

1. Set `status: in-progress`.
2. Create a branch named `<id>-<slug>`, matching the filename. Use a worktree if the
   current one has uncommitted work worth keeping.
3. Dispatch the agent for what the ticket touches, from the Delegation table below, and
   tell it to work test-first, domain outwards, running `make test` as it goes — the
   architecture rules fail on a misplaced class immediately, which is cheaper than
   finding it in review. `backend-ddd` loads the `ddd-backend` skill itself; invoke that
   skill directly only when the work is small enough to stay inline.
4. Write the boundary case first where the ticket has one. A rule tested only in the
   middle of its range passes with an off-by-one in it.
5. If the API surface changed, recapture the schema: `make run`, `make openapi`,
   `make openapi-client`. Running only the last regenerates types from a stale schema.
6. Apply the *Glossary impact* to `docs/glossary.md` in this change, not later.

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
