# Adapters

**Primary** adapters translate an external protocol into a use-case call and translate
the result back. A controller that makes a decision is doing the application layer's
job. Request and response records live here, beside the controller, because they are
the shape of the protocol rather than the shape of the domain.

**Secondary** adapters implement domain ports. Persistence entities live here and are
mapped to domain types — do not annotate an aggregate with `@Entity` and call it a
domain model, because from then on the database schema drives the design.

Persistence is JPA, via `spring-boot-starter-data-jpa`. A context's persistence is three
types in `infrastructure.secondary`, and the split is what keeps Hibernate out of the
domain:

| Type | Role |
|---|---|
| `<Aggregate>Entity` | `@Entity`, private fields, mutable through setters, with `create(...)` and `toDomain()` |
| `Jpa<Aggregate>Repository` | `extends JpaRepository`, derived queries only |
| `<Aggregate>Repository` | `@Repository`, implements the domain port, maps and translates |

Every entity field is `private`, and every post-construction reassignment goes through a
setter declared on the class that owns the field — never a bare `field = value` from
outside it. Package-private access and direct mutation look free because Hibernate's
field-based access strategy reads and writes either one by reflection just as happily,
but neither was ever a deliberate trade, and a codebase that lets one entity do it stops
being able to tell a considered exception from a habit nobody checked. The one exception
is `TABLE_PER_CLASS` inheritance: a field a subclass must read or write directly is
`protected`, because Java's `private` is not visible to a subclass even in the same
package — and that is the only case, so `protected` should not appear anywhere else in a
persistence package. A same-package class that is not a subclass (a test fixture
populating a `@OneToMany` list, say) gets a package-private accessor instead of relaxed
field visibility. A field set once, during construction — a `create()` factory, a Lombok
`@Builder` — needs neither a setter nor special access: it is same-class access to a
private field, legal in Java regardless of when in the object's life it runs.

The adapter takes the unprefixed name because it is the one the context deals with; the
generated Spring Data interface is the implementation detail and carries the `Jpa`
prefix. Every driven adapter follows this, not only the persistence ones: name it for the
port it satisfies and annotate it `@Repository`, so `NotifierPort` is implemented by
`NotifierRepository`, not by `SmtpNotifier`. Naming an adapter after its technology dates
it the day the technology changes, and `ArchitectureTest`'s placement rule then covers
every driven adapter rather than the database ones alone.

Liquibase owns the schema, so set `spring.jpa.hibernate.ddl-auto=validate`: an entity that
has drifted from the changelog then fails at boot instead of at the first query. Set
`spring.jpa.open-in-view=false` too — left on, it holds a connection open for the whole
request and hides lazy-loading mistakes until they show up under load.

Use `saveAndFlush`, not `save`, wherever the adapter translates a constraint violation
into a domain exception. `save` only makes the entity persistent; Hibernate defers the
INSERT to the flush at commit, which the transaction interceptor performs after the
adapter has returned, so the `DataIntegrityViolationException` is raised outside the
`try` and leaves as a 500 rather than the 409 the catch was written for. Catch and
rethrow, never catch and continue: a swallowed violation leaves the transaction
rollback-only and surfaces as `UnexpectedRollbackException` at commit, further from the
cause than where it started.

Translate the constraint you mean, not its parent. `DataIntegrityViolationException`
covers every constraint on the write, so converting it wholesale answers "already
registered" to a NOT NULL violation. Match the constraint name off the Hibernate
`ConstraintViolationException` in the cause chain, rethrow anything else, and chain the
cause — it is the only record of which constraint actually fired.

The database generates ids. Give the column a `gen_random_uuid()` default and map the
field `insertable = false` with Hibernate's `@Generated(event = INSERT)`, so the value is
read back from the insert. `GenerationType.UUID` mints it in Java, which leaves the
column default unused by anything going through Hibernate and puts identity generation
back in code; a `<Aggregate>Id.generate()` in the domain is the same mistake one layer up.

Never edit a changeset that has run. Liquibase identifies it by checksum, so an in-place
edit fails validation at boot on every database that already applied it — including a
developer's, whose data survives `db-down`. Add a new changeset; `addDefaultValue` and
friends exist for exactly this.
