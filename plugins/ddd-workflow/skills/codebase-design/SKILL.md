---
name: codebase-design
description: Shared vocabulary for designing deep modules — a lot of behaviour behind a small interface. Use when designing or improving a module's interface, finding deepening opportunities, deciding where a seam goes, making code more testable or AI-navigable, or when another skill needs the deep-module vocabulary.
---

# Codebase design

Design **deep modules**: a lot of behaviour behind a small interface, placed at a clean
seam, testable through that interface. Use this language wherever code is being designed
or restructured. The aim is leverage for callers, locality for maintainers, and
testability for everyone.

This is a vocabulary layer, complementary to — not a replacement for — the aggregate/
port/adapter shape `ddd-backend` already enforces. A hexagonal port *is* a seam; this
skill is about how deep the module behind it should be.

## Glossary

Use these terms exactly — not "component," "service," "API," or "boundary":

- **Module** — anything with an interface and an implementation. Scale-agnostic: a
  method, a class, a whole bounded context.
- **Interface** — everything a caller must know to use the module correctly: the type
  signature, plus invariants, ordering constraints, error modes, required configuration,
  performance characteristics. Not just the type-level surface.
- **Implementation** — what's inside. Distinct from **adapter**: a thing can be a small
  adapter with a large implementation (a Postgres repository) or a large adapter with a
  small one (an in-memory fake).
- **Depth** — leverage at the interface: how much behaviour a caller, or a test, can
  exercise per unit of interface they have to learn. **Deep** = a lot of behaviour behind
  a small interface. **Shallow** = the interface is nearly as complex as the
  implementation.
- **Seam** *(Michael Feathers)* — where you can alter behaviour without editing in that
  place: the location a module's interface lives at. Never "boundary" — that word is
  taken by DDD's bounded context.
- **Adapter** — a concrete thing satisfying an interface at a seam. Names the *role*
  (what slot it fills), not the substance.
- **Leverage** — what callers get from depth: more capability per unit of interface
  learned.
- **Locality** — what maintainers get from depth: bugs, changes and knowledge
  concentrate in one place instead of spreading across callers.

## Deep vs. shallow

A deep module — small interface, a lot behind it — pays for itself every time it's
called or tested. A shallow one — interface almost as large as the implementation — is
often just a pass-through, and every caller pays its full cost to learn it for little
behaviour in return.

When shaping an interface, ask: can the number of methods shrink? Can the parameters
simplify? Can more complexity move inside?

## Principles

- **Depth is a property of the interface, not the implementation.** A deep module can
  be internally composed of small, swappable parts — they're just not part of the
  interface. A module can have **internal seams**, private to its own tests, as well as
  the **external seam** at its interface.
- **The deletion test.** Imagine deleting the module. If complexity vanishes, it was a
  pass-through. If it reappears across N callers, the module was earning its keep.
- **The interface is the test surface.** Callers and tests cross the same seam. Wanting
  to test *past* the interface usually means the module is the wrong shape.
- **One adapter means a hypothetical seam. Two adapters means a real one.** Don't
  introduce a seam unless something actually varies across it.

## Designing for testability

1. **Accept dependencies, don't create them.** `processOrder(order, paymentGateway)`,
   not a function that `new`s its own `StripeGateway` inside.
2. **Return results, don't produce side effects.** `calculateDiscount(cart): Discount`,
   not `applyDiscount(cart): void` mutating `cart.total` in place.
3. **Small surface area.** Fewer methods means fewer tests to write; fewer parameters
   means simpler test setup.

## Relationships

A **module** has exactly one **interface**. **Depth** is measured against that
interface. A **seam** is where the interface lives. An **adapter** sits at a seam and
satisfies the interface. Depth produces **leverage** for callers and **locality** for
maintainers.

## Rejected framings

- **Depth as implementation-lines ÷ interface-lines** (Ousterhout) — rewards padding the
  implementation. Depth-as-leverage is used instead.
- **"Interface" as a language's `interface` keyword or a class's public methods** — too
  narrow; interface here is every fact a caller must know.
- **"Boundary"** — overloaded with DDD's bounded context. Say **seam** or **interface**.

## Going deeper

- Deepening a cluster given its dependencies: read `references/deepening.md` first — it
  covers dependency categories (in-process, local-substitutable, ports & adapters, true
  external) and testing a deepened module without layering old tests on top of new ones.
- Exploring alternative interfaces for a chosen candidate: read
  `references/design-it-twice.md` first — it covers the parallel-sub-agent pattern for
  designing the same interface several radically different ways before picking one.

Adapted from [mattpocock/skills](https://github.com/mattpocock/skills)'s
`codebase-design` (MIT); vocabulary derives from John Ousterhout's *A Philosophy of
Software Design*.
