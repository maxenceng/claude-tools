# Outbound clients

A client that calls a vendor's API is a secondary adapter, the same as a repository is — it
implements a port the domain declared, and the domain never sees the vendor's own shapes.
It just isn't persistence's shape, so it doesn't get persistence's three-type split.

## Placement

It lives in `infrastructure.secondary.client`, and the wire shapes it maps are named
`*Response`/`*Request` beside it — a request or response is the shape of a protocol, not of
the domain, whichever protocol it is. `ArchitectureTest`'s placement rule for those names
allows both `infrastructure.primary` (this system's own protocol) and
`infrastructure.secondary.client` (a vendor's) for exactly this reason.

Everything else in that package defaults to package-private, the same as a persistence
entity does — only the client interface, the response its caller maps, and the failure it
can raise are public. When a helper in there needs a type from the package next door, that
need is telling you where the helper belongs; move it in rather than widening the type to
reach it. A class made public for one caller across a package boundary is a class in the
wrong package.

## Build it declaratively, with Feign

Use Spring Cloud OpenFeign's `@FeignClient` — not a hand-assembled `RestClient`, and not
`@HttpExchange`. The reason is narrower than "Feign is nicer": a vendor almost always needs
its own credential attached to every request (an API key as a query parameter, most often),
and a `RestClient`-based `ClientHttpRequestInterceptor` is handed a request whose URI is
already fixed, with no method to add a parameter to it — only to replace the whole request,
which is what pushes people toward wrapping it. Feign's `RequestTemplate` has a mutable
`.query(name, value)`/`.header(name, value)`, built for exactly this, and its `ErrorDecoder`
and `Client` are extension points built for the other half: translating a failure once, at
the client, instead of once per repository method that happens to call it.

Each client gets its own plain class supplying its Feign beans — not `@Configuration`. A
`@FeignClient`'s `configuration` attribute is registered into that one client's own child
context by Spring Cloud itself; annotating the class besides would also hand it to the
application's own component scan, which is the one context a bean meant for a single
client must never be reachable from.

That class supplies three things, and none of them differ by vendor — pull them from one
shared factory rather than writing them three times over:

- a `Decoder` bound to the vendor's own JSON shape (its field-naming convention, whether an
  unknown field is ignored or refused);
- a `Client` decorating the real transport, turning "no response at all" (a transport
  failure) into the vendor's own unreachable exception;
- an `ErrorDecoder` turning a non-2xx response into the same exception.

Nothing in any of those three names the vendor. Write them once, in the shared kernel's
`infrastructure.secondary` — not beside the first client that needed them — so the next
context to write its own `@FeignClient` reuses the factory instead of either reaching into
another context's package or duplicating it. A repository that still has a
`try`/`catch (RestClientException e)` after this exists has not finished the move: the
client itself should raise the vendor's exception directly, and the repository should read
a plain answer.

Where the vendor needs a credential, add a `RequestInterceptor` — `new`'d inside the one
`@Bean` method of the one configuration class that needs it, never a `@Component`. Spring
Cloud collects a bean of that type from a client's own context *and every ancestor of it*,
so one left in a shared parent context is applied to every client — this vendor's key on
another vendor's calls, or worse, a client authenticating its own token exchange with a
token it does not have yet.

## What the failure means depends on who's asking

The vendor's own exception — the one the `Client`/`ErrorDecoder` pair raises — is not
automatically a `DomainException`. Whether it should be one depends on what's on the other
end of the call:

- A controller-triggered lookup wants it to extend `DomainException`, carrying whichever
  `DomainErrorStatus` fits "an upstream dependency didn't answer," so the one global handler
  translates it the same way it translates every other business failure.
- A workflow-triggered lookup (see `references/workflows.md`) usually wants a plain
  exception instead: no business rule was broken, no HTTP caller is waiting on it, and
  Temporal's own activity retry is what decides whether the failure was a blip or the end of
  that run's attempt. Raising it as a `DomainException` would route it through machinery
  built for a request thread that isn't there.

A decode failure — a 2xx response whose body won't parse — is a different fact from either
of those, and is best left as Feign's own `DecodeException` rather than folded into the
vendor's unreachable exception. Nothing downstream usually branches on the difference
between "the vendor sent nothing usable" and "the vendor sent something this couldn't read,"
so matching them costs more than the distinction is worth: either the vendor's own exception
type ends up coupled to Feign's, or every call gets wrapped in a reflective proxy just to
re-catch what Feign already caught once.

## When not to reach for Feign

Feign's model is one fixed base URL with templated paths. A call to an arbitrary,
per-request URL — a thumbnail at a URL the previous response just handed back, say — has no
`@FeignClient` shape to declare, because there's no fixed path. Stay on `RestClient` for
that one call rather than forcing it into a client interface it doesn't fit; it doesn't need
the vendor-wide credential or failure handling either, since it isn't hitting the vendor's
authenticated endpoint.
