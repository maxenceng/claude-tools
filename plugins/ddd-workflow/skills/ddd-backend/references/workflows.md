# Workflows

A Temporal workflow and its activities are driving adapters, the same as a controller is.
Both the interface and the `@WorkflowImpl`/`@ActivityImpl` implementation live in the owning
context's `infrastructure.primary`, beside the controllers. Reserve the `Impl` suffix for
exactly this Temporal pairing — nothing else in the codebase should be named `*Impl`, so an
`ArchitectureTest` rule that checks for the suffix catches a controller or a repository
picking it up by habit.

An activity interface's methods take and return domain value types, never the primitives
underneath them. What crosses there is serialised into a Temporal history that outlives the
code that wrote it, so a later shape change to one of those types needs `Workflow.getVersion`
to keep an in-flight run replaying against it — a real cost, taken deliberately in exchange
for a readable signature, and worth revisiting only where a shape change and a long-running
run are likely to collide.

That package otherwise defaults the way any adapter package does, but a type an activity
interface returns is one exception that must be `public`: Temporal proxies the interface
dynamically at runtime, from a different JDK module than the one declaring it, and a
package-private return type is invisible to that proxy. Every call then fails with an
`IllegalAccessError` indistinguishable from a transient one, so the activity's retry policy
just retries forever instead of failing the run the way it should.

A workflow implementation sequences calls; it does not decide. Business rules stay where
they already are — a domain manager — and the workflow method only asks for them in order,
even where the loop looks busy. Where an activity answers with a value that may be absent (no
prior watermark, an empty page), wrap it into an `Optional` the moment it crosses from the
activity call, and write the rest of the method against the `Optional` — a workflow juggling
raw nulls inline is doing the manager's job with none of its guarantees.

See `references/outbound-clients.md` for what an activity that calls a vendor should raise on
failure — usually not a `DomainException`, since nothing about a transport failure is a
business rule broken, and Temporal's own retry is what's deciding whether to try again.
