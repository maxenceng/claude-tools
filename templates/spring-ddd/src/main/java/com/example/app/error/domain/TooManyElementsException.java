package com.example.app.error.domain;

import static java.util.Objects.requireNonNull;

import java.util.Map;

public final class TooManyElementsException extends AssertionException {

    private final String maxSize;
    private final String currentSize;

    private TooManyElementsException(TooManyElementsExceptionBuilder builder) {
        super(requireNonNull(builder.field), builder.message());
        maxSize = String.valueOf(builder.maxSize);
        currentSize = String.valueOf(builder.size);
    }

    public static TooManyElementsExceptionBuilder builder() {
        return new TooManyElementsExceptionBuilder();
    }

    @Override
    public AssertionErrorType type() {
        return AssertionErrorType.TOO_MANY_ELEMENTS;
    }

    @Override
    public Map<String, String> parameters() {
        return Map.of("maxSize", maxSize, "currentSize", currentSize);
    }

    public static class TooManyElementsExceptionBuilder {

        private String field;
        private int maxSize;
        private int size;

        public TooManyElementsExceptionBuilder field(String field) {
            this.field = field;

            return this;
        }

        public TooManyElementsExceptionBuilder maxSize(int maxSize) {
            this.maxSize = maxSize;

            return this;
        }

        public TooManyElementsExceptionBuilder size(int size) {
            this.size = size;

            return this;
        }

        private String message() {
            return "Size of collection \"%s\" must be at most %d but was %d".formatted(field, maxSize, size);
        }

        public TooManyElementsException build() {
            return new TooManyElementsException(this);
        }
    }
}
