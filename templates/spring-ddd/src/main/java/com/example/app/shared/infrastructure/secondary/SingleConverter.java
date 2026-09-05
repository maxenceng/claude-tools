package com.example.app.shared.infrastructure.secondary;

import java.util.List;

import org.springframework.cloud.openfeign.support.FeignHttpMessageConverters;
import org.springframework.http.converter.HttpMessageConverter;

/**
 * The vendor's own converter, standing in for the customiser-built list {@code
 * FeignHttpMessageConverters} otherwise assembles from the Feign child context — the same reason
 * a vendor's own JSON config class replaces the whole converter list rather than adding to it:
 * two vendors agreeing on a shape today is not a reason for one of them to decide the other's
 * deserialisation.
 *
 * <p>The two customiser providers the constructor still asks for are never read, since {@link
 * #getConverters()} answers directly instead of the inherited default that would consult them —
 * they exist only so this can call that constructor at all.
 */
final class SingleConverter extends FeignHttpMessageConverters {

    private final HttpMessageConverter<?> converter;

    SingleConverter(HttpMessageConverter<?> converter) {
        super(new FixedObjectProvider<>(null), new FixedObjectProvider<>(null));
        this.converter = converter;
    }

    @Override
    public List<HttpMessageConverter<?>> getConverters() {
        return List.of(converter);
    }
}
