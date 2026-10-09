# 12. A context is named through its `published` package, and asked through a bean it exposes

Date: 2026-10-09

## Status

Accepted. Replaces the template's earlier hard rule 4, "reached by ID through a context's root package".

## Context

The template first said another context is reached by ID through its root package. Putting
ids directly in a module's root works, but the root is public because it is the root, not
because anyone decided what belongs there, and it offers nowhere to say "this, and only this,
is public".

Spring Modulith already has the mechanism. `@NamedInterface` on a nested package's
`package-info.java` makes that package part of the module's API; every other nested package
stays internal, and `ModularityTest`'s `verify()` fails a build that reaches into one.

Two alternatives were rejected in the project this template was drawn from. A sibling module
per context (`identityshared`) doubles the direct subpackages and puts part of a context's
model outside it. The `shared` kernel couples every context to every id.

Some contexts need more than a name: whether a referenced record exists, or a write on the
other side. An id cannot answer that.

## Decision

**A context's ids live in `<context>.published`**, a `@NamedInterface` package created the
first time another context needs one. It holds ids, and the value types or enums other
contexts would otherwise copy — nothing that acts. The domain rules (no framework, no setters,
final state, inward dependencies) apply to it exactly as to `domain`; `@NamedInterface` on its
own `package-info` is the one framework dependency `domain_is_free_of_frameworks` lets through.

**A context that must ask or tell another calls a plain bean the other exposes** from its own
`@NamedInterface` `infrastructure.query` (answers) or `infrastructure.command` (writes)
package, backed by that context's application layer. Only the consumer's driven adapter calls
it — `another_context_reaches_a_query_or_command_package_only_from_a_driven_adapter`:

- when the consumer's domain needs the answer, it declares a port of its own, held by its
  manager, and the adapter behind that port calls the bean;
- when the answer only stands in for a foreign key, the adapter writing the row calls the bean
  directly and throws the domain's own exception, with no port.

## Consequences

`published` and `infrastructure.query`/`command` answer different questions — what a context
is called by, and what it can be asked — so `published` never grows a type that acts. A
consumer never reaches the provider's domain or application packages; a refactoring there
breaks nothing outside it.
