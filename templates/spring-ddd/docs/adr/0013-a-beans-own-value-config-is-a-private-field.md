# 13. A bean's own `@Value` config is a private field

Date: 2026-10-09

## Status

Accepted. Replaces the template's earlier rule 7 carve-out, which limited field injection to
an `*ApplicationService`'s scalar config and asked for an ADR on first use.

## Context

Constructor injection keeps a collaborator explicit and settable in a plain unit test. Config
is different: a constructor taking a mock *and* a `String` key cannot be built with
`@InjectMocks`, so each test hand-wires the class, and every new setting changes every
construction site. The carve-out first covered application services only; each later kind of
bean that read a property — a client configuration, a `@Configuration` with a `@Bean` method —
reopened the question.

## Decision

A bean's own `@Value` config — on any stereotype, and on a configuration class that reads a
property for a `@Bean` method — is a private, non-`final` field with `@Value` on it. It is never
a constructor parameter and never a `@Bean` method parameter. A unit test builds the class with
`@InjectMocks` and sets the field with `ReflectionTestUtils`.

Collaborators are unchanged: a `final`, constructor-injected field; `@Autowired` on a field
stays forbidden. A group of related values bound together is `@ConfigurationProperties`' job.

`value_config_is_never_a_constructor_or_bean_method_parameter` enforces it. Its first run
caught `CourseCatalogueFeignConfiguration.apiKeyParameter`, whose key is now a field.

## Consequences

Config is set after construction, so a constructor cannot read it; anything derived from it
is built at its call site.
