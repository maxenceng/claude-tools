---
description: Chart a fuzzy effort too big for one session as a map of decision tickets in docs/backlog/, then resolve them one at a time until the way is clear
argument-hint: "[loose idea to chart] | [map id to work]  (no args: show the open map, if any)"
---

A loose idea has arrived, too big for one session, wrapped in fog: the way from here to
the **destination** isn't visible yet. Wayfinding finds that way — it doesn't charge at
the destination. It charts the way as a **map** in `docs/backlog/`, then works its
**decision tickets** (questions whose resolution is a decision, not slices of a build to
execute) one at a time until the route is clear.

Requires the `mattpocock-skills` plugin (`claude plugins install mattpocock-skills`)
installed alongside this one — both modes below call `mattpocock-skills:grilling` by
name.

Lives in `docs/backlog/`, same files-with-frontmatter convention `/ticket` uses (see that
folder's `README.md`), with `type: map` and `type: decision` added to the vocabulary and
a `blocked_by:` field carrying the dependency edges `/ticket`'s single-tracker world
doesn't need. A map is not a ticket queue: **plan, don't do**. Each decision ticket
resolves a decision, and the map is done when nothing is left to decide before someone
goes and does the thing. The pull to just do the work is usually the signal you've
reached the edge of the map and it's time to hand off.

## The map

One file, `type: map`, named for its destination (`<CONTEXT>-<n>-<slug>.md`, same
numbering as any ticket). Its body:

```markdown
## Destination

<What reaching the end of this map looks like: the spec, decision, or change this
effort is finding its way to. One or two lines; every session orients to it before
picking a ticket.>

## Notes

<Domain, skills every session should consult, standing preferences for this effort.>

## Decisions so far

<!-- One line per closed decision ticket: enough to judge relevance, then follow the
     link for the detail the ticket holds. -->

- [<title>](<file>): <one-line gist of the answer>

## Not yet specified

<!-- In-scope fog you can't ticket yet — see "Fog of war" below. -->

## Out of scope

<!-- Work ruled beyond the destination — see "Out of scope" below. -->
```

The map is an index, not a store: a decision lives in exactly one place, its ticket, and
the map only gists it and links. Open tickets aren't listed on the map either — find
them by grepping `docs/backlog/` for `blocked_by:` referencing this map plus
`status: todo` for the frontier, `status: in-progress` for claimed-but-unresolved.

## Decision tickets

A ticket per decision, `type: decision`, same frontmatter as any backlog ticket plus
`blocked_by: [<ids>]` for every ticket that must be `done` first. A ticket is
**unblocked** when everything in its `blocked_by` list has `status: done`; the
**frontier** is every unblocked, unclaimed, `status: todo` decision ticket — the edge of
the known. Body:

```markdown
## Question

<The decision or investigation this ticket resolves.>

## Kind

<research | prototype | grilling | task — see "Kinds" below.>

## Resolution

_Not resolved yet._
```

A session **claims** a ticket by setting `status: in-progress` before any work, so a
concurrent session skips it. `status: done` plus a filled-in `## Resolution` is how it
resolves — the answer isn't part of the body until then.

### Kinds

Every ticket is either **HITL** (worked *with* a human who speaks for themselves) or
**AFK** (the agent alone). A HITL ticket only resolves through that live exchange — an
agent that answers its own HITL questions has broken this.

- **research** (AFK) — reading docs, third-party APIs, or local resources to surface a
  fact a decision waits on. Resolved by a sub-agent calling the Skill tool with
  `research`. Use when the answer lives outside the working directory.
- **prototype** (HITL) — raise the fidelity of the discussion with a cheap, rough,
  concrete artifact to react to. Call the Skill tool with `prototype`; link the result as
  an asset in the resolution.
- **grilling** (HITL) — conversation, the default case. Call the Skill tool with
  `mattpocock-skills:grilling`, and with `ddd-workflow:domain-modeling` alongside it to keep
  `docs/glossary.md` current as terms crystallise.
- **task** (HITL or AFK) — manual work that must happen before a decision can be made:
  nothing to decide, prototype, or research, but the discussion is blocked until it's
  done. Signing up for a service so its API can be judged, provisioning access. The one
  kind that *does* rather than decides, and it earns its place by unblocking a decision,
  not by delivering the destination. Resolution records what was done and any resulting
  facts (a credential's location, a new URL, a row count) later tickets depend on.

## Fog of war

The map is deliberately incomplete: don't chart what you can't yet see. Beyond the live
tickets is the fog — decisions and investigations you can tell are coming but can't yet
pin down, because they hang on questions still open. Resolving a ticket clears the fog
ahead of it, graduating whatever's now specifiable into fresh tickets, one at a time.

Write fog into **Not yet specified** as loosely or fully as the view allows. The test for
ticket-vs-fog is whether the question can be stated precisely *now*, not whether it can
be answered now — ticket when it's already sharp, even if blocked; fog when it can't yet
be phrased that sharply. Don't pre-slice fog into ticket-sized pieces; one patch may
graduate into several tickets, or none, once the frontier reaches it.

## Out of scope

The destination fixes the scope, so work beyond it is out of scope, not fog: give it its
own line in **Out of scope**, gist plus why, linking the closed ticket. Out-of-scope work
never graduates — it returns only if the destination is redrawn, as a fresh effort. If an
existing ticket turns out to sit past the destination, close it (`status: done` with a
`## Resolution` saying why it was ruled out, not what was decided) rather than resolving
it on the route; it stays out of **Decisions so far**, which records the route actually
walked.

## Invocation

Never resolve more than one decision ticket per session, except research tickets.

### Chart the map (`$ARGUMENTS` is a loose idea)

1. **Name the destination.** Call the Skill tool with `mattpocock-skills:grilling` and
   `ddd-workflow:domain-modeling` to pin down what this map is finding its way to. Settle scope
   first.
2. **Map the frontier**, breadth-first this time: fan out across the whole space rather
   than deep on one thread, surfacing open decisions and the first steps takeable now.
   **If this surfaces no fog** — the way is already clear, small enough for one session —
   you don't need a map; say so and stop.
3. **Create the map** ticket, `status: in-progress` from the start — charting is
   analysis, so there's no `draft` to pass through: Destination and Notes filled in,
   Decisions-so-far empty, the fog sketched into Not yet specified.
4. **Create the decision tickets you can specify now**, `status: todo` (also skipping
   `draft` for the same reason), then wire `blocked_by` in a second pass — ids exist only
   once the files do. Everything not yet specifiable stays in the fog.
5. **Fire research sub-agents** in parallel for each `research` ticket just created,
   each calling the Skill tool with `research`.
6. Stop — charting is one session's work, and hand-resolves nothing.

### Work through the map (`$ARGUMENTS` is a map's id, optionally plus a ticket id)

1. Load the map file — the low-res view, not every ticket body.
2. Choose the ticket: the one named, or the first frontier ticket by id order. **Claim
   it** (`status: in-progress`) before any work.
3. Resolve it, zooming into any related or closed ticket's body on demand, and calling
   whatever skills the map's `## Notes` names. Default to `mattpocock-skills:grilling` plus
   `ddd-workflow:domain-modeling` when in doubt.
4. Record the resolution in the ticket, set `status: done`, and append a
   **Decisions so far** line to the map.
5. Add newly-surfaced tickets (create, then wire `blocked_by`); graduate any fog the
   answer made specifiable, removing it from **Not yet specified** so it lives only as
   its new ticket. If the answer reveals a ticket sits beyond the destination, rule it
   **out of scope** rather than resolving it. Update or delete map parts the decision
   invalidates.

Other sessions may be working unblocked tickets concurrently — expect the tracker to
move under you between reads.

Adapted from [mattpocock/skills](https://github.com/mattpocock/skills)'s `wayfinder`
(MIT), retargeted at `docs/backlog/` instead of a general issue-tracker abstraction; the
upstream skill's optional real-tracker native-blocking path was dropped for now — this
version is local-markdown only.
