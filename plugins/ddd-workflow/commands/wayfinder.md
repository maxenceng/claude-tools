---
description: Chart a fuzzy effort too big for one session as a map of decision tickets on GitHub Issues, then resolve them one at a time until the way is clear
argument-hint: "[loose idea to chart] | [map id to work]  (no args: show the open map, if any)"
---

A loose idea has arrived, too big for one session, wrapped in fog: the way from here to
the **destination** isn't visible yet. Wayfinding finds that way — it doesn't charge at
the destination. It charts the way as a **map**, an issue, then works its
**decision tickets** (questions whose resolution is a decision, not slices of a build to
execute) one at a time until the route is clear.

Requires the `mattpocock-skills` plugin (`claude plugins install mattpocock-skills`)
installed alongside this one — both modes below call `mattpocock-skills:grilling` by
name.

Maps and decisions are GitHub issues like any ticket (see `/ticket`), labelled `type:map` and
`type:decision`. Every GitHub operation goes through
`${CLAUDE_PLUGIN_ROOT}/scripts/ticket-tracker`, called `ticket-tracker` below, and no other way; it
refuses with a reason when a ticket is unreadable or GitHub is unreachable, and then this command
does nothing. A decision's dependencies are GitHub's native ones (`add-blocker`), and a map's
decisions are its sub-issues (`add-sub-issue`). A map is not a ticket queue: **plan, don't do**.
Each decision ticket resolves a decision, and the map is done when nothing is left to decide before
someone goes and does the thing. The pull to just do the work is usually the signal you've
reached the edge of the map and it's time to hand off.

## The map

One issue, `type:map`, titled for its destination. `ticket-tracker create --template map --title
"<destination>" --context <context>` opens it from `.github/ISSUE_TEMPLATE/map.md`. Its body:

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

- #<n>: <one-line gist of the answer>

## Not yet specified

<!-- In-scope fog you can't ticket yet — see "Fog of war" below. -->

## Out of scope

<!-- Work ruled beyond the destination — see "Out of scope" below. -->
```

The map is an index, not a store: a decision lives in exactly one place, its ticket, and
the map only gists it and links. Open tickets aren't listed on the map either — they are its
sub-issues; `ticket-tracker frontier <map>` lists the ones ready to work.

## Decision tickets

A ticket per decision, `type:decision`, a sub-issue of its map, with a native dependency on every
decision that must be closed first. `ticket-tracker create --template decision --title "<question>"
--context <context>` opens it from `.github/ISSUE_TEMPLATE/decision.md` already `status:todo`. A
ticket is **unblocked** when every issue it depends on is closed; the **frontier**, from
`ticket-tracker frontier <map>`, is the map's open `status:todo` sub-issues whose dependencies are
all closed — the edge of the known. Body:

```markdown
## Question

<The decision or investigation this ticket resolves.>

## Kind

<research | prototype | grilling | task — see "Kinds" below.>

## Resolution

_Not resolved yet._
```

A session **claims** a ticket with `ticket-tracker move <n> in-progress` before any work, which
adds `status:in-progress` and removes `status:todo` in one edit, so a concurrent session's
frontier skips it. It resolves by writing the *Resolution* section
(`ticket-tracker write-sections`) and then `ticket-tracker close <n>`, which closes it as
completed — the answer isn't part of the body until then. A feature ticket that graduates out of a
decision is an ordinary ticket and is **not** a sub-issue: `add-sub-issue` refuses anything but a
decision.

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
own line in **Out of scope**, gist plus why, naming the closed ticket's number. Out-of-scope work
never graduates — it returns only if the destination is redrawn, as a fresh effort. If an
existing ticket turns out to sit past the destination, close it as completed
(`ticket-tracker close <n>`, with a *Resolution* saying why it was ruled out, not what was decided)
rather than resolving it on the route; there is no dropped status, so a ruled-out decision closes
the way a resolved one does. It stays out of **Decisions so far**, which records the route actually
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
3. **Create the map** — `ticket-tracker create --template map`, `status:in-progress` from the
   start; charting is analysis, so there's no `draft` to pass through. Fill Destination and Notes,
   leave Decisions-so-far empty, and sketch the fog into Not yet specified
   (`ticket-tracker write-sections`).
4. **Create the decision tickets you can specify now**, `status:todo` (also skipping
   `draft` for the same reason), then in a second pass make each a sub-issue of the map
   (`ticket-tracker add-sub-issue <map> <n>`) and wire its dependencies
   (`ticket-tracker add-blocker <n> <blocker>`) — numbers exist only once the issues do.
   Everything not yet specifiable stays in the fog.
5. **Fire research sub-agents** in parallel for each `research` ticket just created,
   each calling the Skill tool with `research`.
6. Stop — charting is one session's work, and hand-resolves nothing.

### Work through the map (`$ARGUMENTS` is a map's id, optionally plus a ticket id)

1. Load the map (`ticket-tracker show <map>`) — the low-res view, not every ticket body — and
   its frontier (`ticket-tracker frontier <map>`).
2. Choose the ticket: the one named, or the first frontier ticket by number. **Claim
   it** (`ticket-tracker move <n> in-progress`) before any work. Two sessions claiming in the same
   second both win; that is accepted for one developer.
3. Resolve it, zooming into any related or closed ticket's body on demand, and calling
   whatever skills the map's `## Notes` names. Default to `mattpocock-skills:grilling` plus
   `ddd-workflow:domain-modeling` when in doubt.
4. Record the resolution in the ticket's *Resolution* section, `ticket-tracker close <n>`, and
   append a **Decisions so far** line to the map (read the map again for its `updatedAt`, then
   `write-sections`).
5. Add newly-surfaced tickets (create, then sub-issue and dependencies); graduate any fog the
   answer made specifiable, removing it from **Not yet specified** so it lives only as
   its new ticket. If the answer reveals a ticket sits beyond the destination, rule it
   **out of scope** rather than resolving it. Update or delete map parts the decision
   invalidates. A newly-surfaced ticket of `/ticket`'s own vocabulary (`feature`, `fix`, `chore`,
   `spike`) is a real ticket `/ticket start` will pick up, not a wayfinder artifact: create it
   with the ticket template, `--status todo`, and no `add-sub-issue` — it is not part of the map.
6. A map's file changes — a glossary term, an ADR a decision produced — go on one branch and
   **one pull request** that refs the map (`ticket-tracker pr-create --refs <map>`), never one per
   decision, and closing nothing. **The map is closed by hand**, once its destination is reached
   and no decision ticket remains open; `ticket-tracker close` refuses a map on purpose.

Other sessions may be working unblocked tickets concurrently — expect the tracker to
move under you between reads; a section write that refuses because the issue changed is that.

Adapted from [mattpocock/skills](https://github.com/mattpocock/skills)'s `wayfinder`
(MIT), retargeted at GitHub Issues, whose native sub-issues and dependencies carry the map's
structure.
