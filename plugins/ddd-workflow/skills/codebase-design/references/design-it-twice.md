# Design it twice

When exploring alternative interfaces for a chosen deepening candidate, use this
parallel sub-agent pattern. Based on "Design It Twice" (Ousterhout): the first idea is
unlikely to be the best one.

Uses the vocabulary in `SKILL.md`: module, interface, seam, adapter, leverage.

## Process

### 1. Frame the problem space

Before spawning sub-agents, write a user-facing explanation of the problem for the
chosen candidate: the constraints any new interface would need to satisfy, the
dependencies it would rely on and which category they fall into (see
`deepening.md`), and a rough illustrative code sketch to make the constraints concrete —
not a proposal. Show this to the user, then move straight to step 2 so they can read
while the sub-agents work.

### 2. Spawn sub-agents

Spawn 3+ agents in parallel, each producing a radically different interface for the
deepened module. Give each a separate technical brief — file paths, coupling details,
the dependency category, what sits behind the seam — independent of the user-facing
framing from step 1, and a different design constraint:

- Agent 1: minimise the interface — 1–3 entry points, maximum leverage per entry point.
- Agent 2: maximise flexibility — support many use cases and future extension.
- Agent 3: optimise for the most common caller — make the default case trivial.
- Agent 4 (if applicable): design around ports & adapters for cross-seam dependencies.

Give each brief the `SKILL.md` vocabulary and `docs/glossary.md`'s domain vocabulary, so
every agent names things consistently with both the architecture language and this
project's domain language.

Each agent reports: the interface (types, methods, params, invariants, ordering, error
modes), a usage example, what the implementation hides behind the seam, the dependency
strategy and its adapters, and where leverage is high versus thin.

### 3. Present and compare

Present the designs sequentially so the user can absorb each one, then compare them in
prose by depth, locality, and seam placement. Give your own recommendation — which
design is strongest and why — and propose a hybrid if elements from different designs
combine well. Be opinionated: a strong read beats a menu.
