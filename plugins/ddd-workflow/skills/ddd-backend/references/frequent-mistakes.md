# Frequent mistakes

Anaemic aggregates — fields and accessors with the logic in a service. This is the
default failure mode of this architecture and no test catches it.

Reaching for an interface with exactly one implementation because it feels like good
practice. Ports exist to invert a dependency across a boundary. An interface that
crosses no boundary is indirection with no benefit.

Adding to the shared kernel because a type is needed in two places. Ask whether it is
genuinely one concept or two that happen to share a name today.

Naming things `Helper`, `Processor`, or `Util`. These names appear when the real concept
has not been found yet, and they persist long after it has. `<Aggregate>Manager` is the
one exception and only in its narrow sense — a domain service holding a required
ordering. A `Manager` that has grown methods unrelated to that ordering has stopped
being one and is hiding a concept that still needs a name.

Wiring one manager into another because both are already there and the second one already
does most of what the first needs. It reads as reuse and costs little to write, which is
exactly why it recurs: a manager needing another manager's decision is a real, common shape,
not a one-off. Take the other manager's port directly and re-implement the small decision
instead — a few duplicated lines is cheaper than a manager whose own correctness now depends
on a sibling's. Reach for the `*ApplicationService` composition only once that duplication
would itself be worth avoiding.

Adding a rule to `ArchitectureTest` for something ArchUnit cannot see. It reads bytecode,
so anything the compiler erases is invisible to it: imports, generic type arguments, and
`SOURCE`-retention annotations — which is every Lombok annotation. Naming `lombok..` in a
package-based rule passes on a domain built entirely of `@Getter`, because the annotation
is gone by the time ArchUnit looks. Rules about those need a test that reads source. The
bar for writing one is not "ArchUnit made this awkward" but "ArchUnit cannot observe this
at all".

Trusting a rule that has never been seen to fail. A rule that reads as protection and
gives none is worse than no rule, because the next reader stops looking. Break the thing
it forbids, watch the build go red, then put it back. This takes a minute and is the only
evidence that the rule works.

Guarding a vendor field against a value the vendor has never actually been observed to
send — an out-of-range percentage, a malformed shape — because a neighbouring field
genuinely needs the guard. The neighbour's guard earned its place with evidence; this one
borrows the shape without the evidence and reads as equally justified. If a bounded domain
type already refuses the value on construction, let it: failing loud is a legitimate
answer, and a silent-skip guard built for a case nobody has seen is speculative surface
area, not a fix.

Removing every such guard on "unevidenced" alone, without checking what removal does to
the failure. Two shapes don't fit the pattern above, and look identical to it until
checked: a guard whose own effect is already to fail loud rather than skip or narrow
silently — one protecting a cached value from being read back as valid, say — where
removing it trades one clear, attributable failure for a quieter or misattributed one, not
for a louder one; and a guard over a field the domain already treats as optional, where the
malformed case collapses to the same accepted absent-value outcome an ordinary missing one
already produces — removing it turns an accepted outcome into a new exception, the reverse
of the fix. "No evidence this happens" is the trigger for asking whether a guard earns its
keep, never the answer by itself — ask what removing it does to the failure before removing
it.

Documenting an intention rather than the code. A comment that states a rule the code
does not enforce is worse than silence: it is believed, and it stops the reader from
checking. If the invariant is real, enforce it; if it is not enforced yet, say exactly
where it is and is not.
