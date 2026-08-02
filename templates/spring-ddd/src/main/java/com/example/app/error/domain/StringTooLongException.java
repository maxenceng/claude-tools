package com.example.app.error.domain;

import static java.util.Objects.requireNonNull;

import java.util.Map;

public final class StringTooLongException extends AssertionException {

    private final String maxLength;
    private final String currentLength;

    private StringTooLongException(StringTooLongExceptionBuilder builder) {
        super(requireNonNull(builder.field), message(builder));
        Assert.notNull("value", builder.value);
        Assert.notNull("maxLength", builder.maxLength);
        maxLength = String.valueOf(builder.maxLength);
        currentLength = String.valueOf(builder.value.length());
    }

    public static StringTooLongExceptionBuilder builder() {
        return new StringTooLongExceptionBuilder();
    }

    private static String message(StringTooLongExceptionBuilder builder) {
        Assert.notNull("value", builder.value);

        return "The value in field \"%s\" must be at most %d long but was %d".formatted(builder.field, builder.maxLength, builder.value.length());
    }

    @Override
    public AssertionErrorType type() {
        return AssertionErrorType.STRING_TOO_LONG;
    }

    @Override
    public Map<String, String> parameters() {
        return Map.of("maxLength", maxLength, "currentLength", currentLength);
    }

    public static final class StringTooLongExceptionBuilder {

        private String value;
        private int maxLength;
        private String field;

        private StringTooLongExceptionBuilder() {
        }

        StringTooLongExceptionBuilder field(String field) {
            this.field = field;

            return this;
        }

        StringTooLongExceptionBuilder value(String value) {
            this.value = value;

            return this;
        }

        StringTooLongExceptionBuilder maxLength(int maxLength) {
            this.maxLength = maxLength;

            return this;
        }

        public StringTooLongException build() {
            return new StringTooLongException(this);
        }
    }
}
