package com.example.app.shared.infrastructure.secondary;

import java.io.IOException;
import java.util.function.BiFunction;

import org.springframework.cloud.openfeign.support.SpringDecoder;
import org.springframework.http.converter.HttpMessageConverter;

import feign.Client;
import feign.codec.Decoder;
import feign.codec.ErrorDecoder;

/**
 * What every vendor's Feign configuration needs, built once here instead of once per vendor: a
 * decoder bound to that vendor's own JSON shape, and the two places a call gives back nothing
 * usable at all — a transport that never got a response, and a response whose status refused it —
 * brought back into the one exception each vendor's repository would otherwise have to catch for.
 * Whichever raises it, the caller is given no way to tell the two apart, because it never could.
 *
 * <p>Lives here rather than beside a vendor's own configuration classes: nothing in it names a
 * vendor, and a second context writing its own {@code @FeignClient} would otherwise have to reach
 * into another context's package or duplicate these three factories (ADR 0009).
 *
 * <p>A body {@link #decoder} cannot parse is a different fact and stays Feign's own {@code
 * DecodeException}: the vendor answered, the answer just was not one this system could read,
 * which is not the same claim as the vendor being unreachable, and nothing here or in an adapter
 * branches on the difference — see ADR 0009.
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

    public static Client transportFailures(Client delegate, BiFunction<String, Throwable, RuntimeException> unreachable) {
        return (request, options) -> {
            try {
                return delegate.execute(request, options);
            } catch (IOException e) {
                throw unreachable.apply("could not be reached: " + e.getMessage(), e);
            }
        };
    }

    public static ErrorDecoder errorDecoder(BiFunction<String, Throwable, RuntimeException> unreachable) {
        return (methodKey, response) -> unreachable.apply("refused %s: HTTP %d".formatted(methodKey, response.status()), null);
    }
}
