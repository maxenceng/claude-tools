package com.example.app.error.domain;

import static java.util.Objects.requireNonNull;

import java.util.Map;

public final class StringTooShortException extends AssertionException {

    private final String minLength;
    private final String currentLength;

    private StringTooShortException(StringTooShortExceptionBuilder builder) {
        super(requireNonNull(builder.field), message(builder));
        Assert.notNull("courseId", builder.value);
        Assert.notNull("minLength", builder.minLength);
        minLength = String.valueOf(builder.minLength);
        currentLength = String.valueOf(builder.value.length());
    }

    public static StringTooShortExceptionBuilder builder() {
        return new StringTooShortExceptionBuilder();
    }

    private static String message(StringTooShortExceptionBuilder builder) {
        Assert.notNull("courseId", builder.value);

        return "The courseId in field \"%s\" must be at least %d long but was only %d".formatted(builder.field, builder.minLength, builder.value.length());
    }

    @Override
    public AssertionErrorType type() {
        return AssertionErrorType.STRING_TOO_SHORT;
    }

    @Override
    public Map<String, String> parameters() {
        return Map.of("minLength", minLength, "currentLength", currentLength);
    }

    public static final class StringTooShortExceptionBuilder {

        private String value;
        private int minLength;
        private String field;

        private StringTooShortExceptionBuilder() {
        }

        StringTooShortExceptionBuilder field(String field) {
            this.field = field;

            return this;
        }

        StringTooShortExceptionBuilder value(String value) {
            this.value = value;

            return this;
        }

        StringTooShortExceptionBuilder minLength(int minLength) {
            this.minLength = minLength;

            return this;
        }

        public StringTooShortException build() {
            return new StringTooShortException(this);
        }
    }
}
