# 17. The harness works tickets on GitHub Issues through one script

Date: 2026-10-29

## Status

Accepted. Supersedes the `docs/backlog/` convention and the Vikunja mirror the harness used before 3.0.0.

## Context

`/ticket`, `/wayfinder` and `/debt` read and wrote `docs/backlog/*.md`, one file per ticket with a
frontmatter, and mirrored status to Vikunja when it was configured. A status change rode along on the
ticket branch, so which copy of a file was true needed its own rule, and an id was a filename, a
branch name and a prefix someone had to count.

GitHub gives a ticket what the files faked. The issue number is allocated, so it is unique and never
races; labels carry status, context and type; sub-issues and dependencies are native; the merge's
closing keyword closes the issue. It gives no conditional write, only an `updatedAt` to compare
before writing.

## Decision

- **A ticket is an issue, named by its number.** `status:draft|todo|in-progress|in-review`,
  `context:<name>` and `type:<feature|fix|chore|spike|map|decision>` are labels; the body keeps the
  `##` sections and has no frontmatter. An open issue with no status label is a draft. From `todo` on,
  an issue without exactly one `context:` and one `type:` label, with two status labels, or closed as
  not planned, is unreadable and every verb refuses it with the reason. A closed-as-completed issue is
  done whatever labels it still carries.
- **One script carries every GitHub operation.** The plugin's `scripts/ticket-tracker` is Python,
  standard library only, over `gh`. Every `/ticket` step, `/wayfinder` and `/debt` calls it, and no
  step file carries a `gh issue` or `gh api` snippet. Rejected: a snippet per step, which drifts across
  files; an MCP server, which is a process to keep running for what a script does per call.
- **A status move is one edit** adding the new label and removing the old. A missing `status:` or
  `type:` label is created as it is applied. A `context:` label is created only if
  `docs/context-map.md` names the context; `context:cross-context` is the harness's own and every
  project accepts it.
- **A section write replaces only that `##` section and refuses, changing nothing, if the issue's
  `updatedAt` moved since it was read.** A human's edit from the GitHub UI is never overwritten.
- **No verb works offline, and nothing is cached.** A verb that cannot reach GitHub refuses with that
  reason and writes nothing; `/debt` still sweeps code markers and ADRs and reports its ticket source
  as skipped. `make verify` never needs the network.
- **`start` branches with `gh issue develop`**, `review` writes `Closes #<n>` in the pull request body,
  and `done` runs after the merge: it writes *Notes* into the issue, clears leftover labels, closes an
  issue left open by a missed keyword as completed, and opens a pull request only for files it changed,
  closing nothing.
- **A map's decisions are its sub-issues; a graduated feature ticket is not.** The frontier is the
  map's open `status:todo` sub-issues whose dependencies are all closed. Claiming adds
  `status:in-progress`; a decision, resolved or ruled out, closes as completed; the map's own file
  changes go on one pull request that `Refs` it, and the map is closed by hand.
- **Vikunja, `tracker_id`, the Obsidian board and `docs/backlog/` are gone.** There is one cut-over, at
  the plugin's 3.0.0, with no mode that detects `docs/backlog/` and keeps both.

## Consequences

- "What state was this in when we merged" is answered by the issue's timeline, not by the repository's
  history.
- Without the network `/ticket` and `/wayfinder` do nothing. That is chosen over a read cache, which
  would be a second copy of status.
- Two sessions claiming the same frontier ticket in the same second both win; accepted for one
  developer.
- A project upgrades to 3.0.0 only once its backlog is on Issues.
