# Comments

Comment the decision, not the mechanics. `enroll()` returning a new `Course` needs no
comment; *why* it re-checks capacity when the caller already did is worth two lines,
because the next reader will otherwise delete the check as redundant.

Two lines is the ceiling, not the target, and it buys less outside Java. `pom.xml`,
`compose.yaml`, `application.properties`, the `Makefile` and CI workflows get a line at
most and usually nothing: their readers already know the tools, and a paragraph on how
Docker publishes a port reads as a prompt rather than as code. A dependency that is easy
to get wrong earns one line naming the trap. Everything else earns silence — including,
especially, the reasoning you found interesting while working it out.

Class- and method-level javadoc runs longer, but the ceiling still applies to what it is
allowed to restate. State what the type is once. Where an ADR already carries the
decision's reasoning, name its number and stop — `CapturedAt` citing "ADR 0028" needs no
second sentence re-arguing what 0028 already argues. A paragraph earns its place only for
a decision the ADR does not cover, such as `CapturedAt` living on the listing rather than
inside `Price`.

Check a comment against the code before trusting it, especially one that sounds precise.
`Seats` was documented as rejecting zero while its assertion accepted zero, and zero is
what every new course is created with — the comment had been wrong for as long as it had
existed, and it read more authoritatively than the code.

Treat a bulk rename as a comment hazard. A find-and-replace across a file rewrites prose
as happily as identifiers; one such pass had left 156 occurrences of a domain field name
scattered through a generic utility's javadoc, describing parameters that had never had
that name.

Names are documentation and rot the same way. A fixture called `invalidCourse` that
returns a perfectly valid full course sends every reader looking for the invalidity.

`@ApiResponse`, `@Schema` and the like are documentation that ships to another codebase.
Check the codes against the handler that actually produces them.

A `FIXME` is a decision someone deferred. Either carry it out or record why it still
stands — reviewing comments and leaving the `FIXME` untouched is how it survives another
year. When you do act on one, delete it in the same change; a `FIXME` describing work
already done is worse than one describing work outstanding.

A `deferred:` comment is the other case: not work outstanding but a limit someone chose to
live with. It names the ceiling and what would justify closing it — `// deferred: <what it
cannot do> — <what would make it worth fixing>` — and `/debt` collects those across code,
ADR *Consequences* and ticket *Notes*. Write the trigger even when it is "when a second
caller exists"; a marker without one is how a decision becomes an accident. Nothing under
`src/test` carries one: tests hold no comments, and a limit of the code is not a property
of the test that covers it.
