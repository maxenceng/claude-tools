package com.example.app.shared.infrastructure.secondary;

import java.io.IOException;
import java.util.function.Function;

import org.springframework.cloud.openfeign.support.SpringDecoder;
import org.springframework.http.converter.HttpMessageConverter;

import feign.Client;
import feign.Request;
import feign.Response;
import feign.Util;
import feign.codec.Decoder;
import feign.codec.ErrorDecoder;

/**
 * What every vendor's Feign configuration needs, built once here instead of once per vendor: a
 * decoder bound to that vendor's own JSON shape, and the two places a call gives back nothing
 * usable at all — a transport that never got a whole response, and a response whose status refused
 * it — brought back into the one exception each vendor's repository would otherwise have to catch
 * for. Whichever raises it, the caller is given no way to tell them apart, because it never could.
 *
 * <p>Lives here rather than beside a vendor's own configuration classes: nothing in it names a
 * vendor, and a second context writing its own {@code @FeignClient} would otherwise have to reach
 * into another context's package or duplicate these three factories (ADR 0009).
 *
 * <p>{@link #transportFailures} reads the whole body before Feign sees the response. A body that
 * breaks off midway is an answer that never arrived, so it raises the vendor's unreachable
 * exception like a connection that never opened. Left to Feign, the read would fail as its {@code
 * FeignException.errorReading}, whose message is the full request URL, key included.
 *
 * <p>The cost: every vendor response is held whole in memory, one byte copy per call, unbounded.
 * Acceptable because {@code SpringDecoder} with Jackson already materialises the whole body to bind
 * it. A vendor streaming large or unbounded payloads needs a different decorator — a bounded read,
 * or a streaming response type — rather than this one.
 *
 * <p>A whole body {@link #decoder} cannot parse is a different fact and stays Feign's own {@code
 * DecodeException}: the vendor answered, the answer just was not one this system could read, and
 * nothing here or in an adapter branches on the difference — see ADR 0009. Its message is the
 * converter's parse error, which never names the request, so it is safe to log as it is.
 *
 * <p>A diagnostic is built from safe parts only — the HTTP method, the URL without its query
 * string, the transport exception's type, the status — and the transport exception itself is not
 * chained. A vendor key travels in the query string, and a JDK transport error can quote the full
 * URL in its message, so either would carry the key into the log line the 503 writes.
 *
 * <p>{@link #transportFailures} decorates the {@link Client} it is given rather than replacing it
 * with one built here, so a test can wrap a fake transport the same way this decorates the real
 * one.
 */
public final class OutboundClientSupport {

    private OutboundClientSupport() {
    }

    public static Decoder decoder(HttpMessageConverter<?> converter) {
        return new SpringDecoder(new FixedObjectProvider<>(new SingleConverter(converter)));
    }

    public static Client transportFailures(Client delegate, Function<String, RuntimeException> unreachable) {
        return (request, options) -> {
            Response response;
            try {
                response = delegate.execute(request, options);
            } catch (IOException e) {
                throw unreachable.apply("%s could not be reached: %s".formatted(target(request), e.getClass().getSimpleName()));
            }
            try {
                return whole(response);
            } catch (IOException e) {
                throw unreachable.apply("%s broke off mid-answer: %s".formatted(target(request), e.getClass().getSimpleName()));
            }
        };
    }

    public static ErrorDecoder errorDecoder(Function<String, RuntimeException> unreachable) {
        return (methodKey, response) -> unreachable.apply("%s refused: HTTP %d".formatted(target(response.request()), response.status()));
    }

    private static Response whole(Response response) throws IOException {
        if (response.body() == null) {
            return response;
        }
        try (Response.Body body = response.body()) {
            return response.toBuilder().body(Util.toByteArray(body.asInputStream())).build();
        }
    }

    private static String target(Request request) {
        String url = request.url();
        int query = url.indexOf('?');
        return request.httpMethod() + " " + (query < 0 ? url : url.substring(0, query));
    }
}
