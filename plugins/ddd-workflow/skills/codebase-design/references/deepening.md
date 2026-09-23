# Deepening

How to deepen a cluster of shallow modules safely, given its dependencies. Assumes the
vocabulary in `SKILL.md`: module, interface, seam, adapter.

## Dependency categories

Classify a deepening candidate's dependencies first — the category decides how the
deepened module gets tested across its seam.

1. **In-process** — pure computation, in-memory state, no I/O. Always deepenable: merge
   the modules and test through the new interface directly. No adapter needed.
2. **Local-substitutable** — dependencies with a real local test stand-in (an
   in-process Postgres, an in-memory filesystem). Deepenable if the stand-in exists;
   the deepened module's tests run against it. The seam stays internal, with no port at
   the module's external interface.
3. **Remote but owned (ports & adapters)** — your own services across a network
   boundary. Define a port at the seam; the deep module owns the logic, the transport is
   injected as an adapter. Tests use an in-memory adapter, production an HTTP/gRPC/queue
   one. This is the same shape `ddd-backend` already uses for outbound ports — deepening
   here means widening what sits behind the port, not changing the port pattern itself.
4. **True external (mock)** — third-party services you don't control (Stripe, Twilio).
   The deepened module takes the dependency as an injected port; tests provide a mock
   adapter.

## Seam discipline

- **One adapter means a hypothetical seam. Two adapters means a real one.** Don't
  introduce a port unless at least two adapters are justified — typically production
  plus test. A single-adapter seam is indirection with no payoff.
- **Internal seams vs. external seams.** A deep module can have internal seams, private
  to its own tests, in addition to the external seam at its interface. Don't expose an
  internal seam through the interface just because a test happens to use it.

## Testing strategy: replace, don't layer

- Old unit tests on the shallow modules become waste once tests at the deepened
  module's interface exist — delete them rather than keeping both.
- Write new tests at the deepened module's interface: the interface is the test
  surface.
- Assert on observable outcomes through the interface, not internal state.
- A test should survive an internal refactor, because it describes behaviour, not
  implementation. If a test has to change when the implementation does, it was testing
  past the interface.
