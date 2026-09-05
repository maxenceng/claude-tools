# 9. Outbound clients are built with Feign

Date: 2026-09-05

## Status

Accepted

## Context

`training` (see [ADR 8](0008-the-template-ships-one-worked-example-context.md)) needed a
client for a vendor's API — a course's popularity, supplied by an external training
catalogue this system does not own. Two things had to be decided for the first time: how the
client is built, and where its wire shapes live relative to the existing rule that a
`*Request`/`*Response` lives beside the controller it protocols for.

A vendor almost always needs its own credential on every request — an API key, most often,
carried as a query parameter or a header. Spring's own `RestClient`, via a
`ClientHttpRequestInterceptor`, is handed a request whose URI is already built, with no
method to add a parameter to it, only to replace the request outright. That pushes toward
wrapping the request by hand for something that should be a one-line concern. Spring Cloud
OpenFeign's `RequestTemplate` has a mutable `.query(name, value)`/`.header(name, value)`,
built for exactly this, and its `ErrorDecoder` and `Client` extension points do the other
half a hand-rolled client would otherwise leave to whichever repository calls it: translating
a transport failure or a refused response into a checked failure, once, at the client itself.

## Decision

`CourseCatalogueClient` is a `@FeignClient` interface. It lives in
`training.infrastructure.secondary.client`, and `CourseCatalogueResponse` lives beside it —
`ArchitectureTest`'s wire-shape placement rule now allows `infrastructure.secondary.client`
as well as `infrastructure.primary`, because a response is the shape of a protocol, not of
the domain, whichever protocol answered it.

Its Feign beans come from a plain (not `@Configuration`) `CourseCatalogueFeignConfiguration`,
because a `@FeignClient`'s `configuration` attribute is registered into that one client's own
child context by Spring Cloud itself — annotating the class besides would also hand it to
the application's own component scan, the one context a bean meant for a single client must
never be reachable from. It builds its `Decoder`, `Client` and `ErrorDecoder` from
`OutboundClientSupport`'s three static factories in `shared.infrastructure.secondary`, not by
hand: nothing about decoding a vendor's JSON, or turning "no response" and "a refused
response" into that vendor's own unreachable exception, is specific to this one vendor, and
the next client this template or a project built from it writes reuses the same three
methods instead of duplicating them. The one thing that *is* specific to this vendor — its
API key — is a `RequestInterceptor`, `new`'d inside the configuration class's own `@Bean`
method rather than declared as a `@Component`: Spring Cloud collects a bean of that type from
a client's context *and every ancestor of it*, so a component-scanned interceptor would
attach this vendor's key to every other client's calls too.

`CourseCatalogueUnreachableException` is a plain `RuntimeException`, not a `DomainException`.
Nothing about a vendor call failing is a business rule broken, and `training` has no
controller waiting on the answer — `CourseManager.fillPopularity` treats a failed lookup the
same as a miss the vendor genuinely had no answer for, either way leaving `popularity`
unset rather than raising past the manager. A project that calls a vendor client from a
controller, rather than a background fill, would want that exception to extend
`DomainException` instead, so the one global handler translates it like any other failure;
see `ddd-backend`'s `references/outbound-clients.md` for both shapes.

Everything else in `training.infrastructure.secondary.client` defaults to package-private —
only the client interface, the response, and the exception are public — the same rule an
entity's package already followed, now checked by `ArchRule`
`outbound_client_helpers_stay_package_private` for this package too.

## Consequences

`pom.xml` gains `spring-cloud-dependencies` (import scope) and
`spring-cloud-starter-openfeign`. No `RestClient`/`HttpServiceProxyFactory` example exists
anywhere in this template to contradict this one — there was none before `training`.

A decode failure — a response that arrived but will not parse — surfaces as Feign's own
`DecodeException` rather than being folded into `CourseCatalogueUnreachableException`.
Nothing in `CourseManager` branches on the difference between "the vendor sent nothing
usable" and "the vendor sent something this could not read," so coupling the vendor's own
exception type to Feign's, just to erase a distinction nothing acts on, costs more than it
buys.

A client calling an arbitrary per-request URL rather than one vendor's fixed base — a
thumbnail at a URL a previous response just handed back, say — has no `@FeignClient` shape
to declare and stays on `RestClient`. `training` has no such call to demonstrate; the next
project that needs one is the one that writes the worked example for it.
