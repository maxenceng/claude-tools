package com.example.app.shared.infrastructure.secondary;

import org.springframework.beans.factory.ObjectProvider;

/**
 * Every method {@link ObjectProvider} declares is a default in this Spring version, which is
 * exactly why it cannot be a lambda: there is no single abstract method left to implement one
 * against. {@code SpringDecoder} and {@code FeignHttpMessageConverters} both take one only to
 * read a value handed to them once at construction, never to look one up from a context, so this
 * answers every accessor with the same fixed value rather than resolving anything.
 */
final class FixedObjectProvider<T> implements ObjectProvider<T> {

    private final T value;

    FixedObjectProvider(T value) {
        this.value = value;
    }

    @Override
    public T getObject() {
        return value;
    }

    @Override
    public T getIfAvailable() {
        return value;
    }

    @Override
    public T getIfUnique() {
        return value;
    }
}
