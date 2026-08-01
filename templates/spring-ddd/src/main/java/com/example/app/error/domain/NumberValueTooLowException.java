package com.example.app.error.domain;

import static java.util.Objects.requireNonNull;

import java.util.Map;

public final class NumberValueTooLowException extends AssertionException {

    private final String min;
    private final String value;

    private NumberValueTooLowException(NumberValueTooLowExceptionBuilder builder) {
        super(requireNonNull(builder.field), builder.message());
        Assert.notNull("max", builder.minValue);
        Assert.notNull("courseId", builder.value);
        min = builder.minValue;
        value = builder.value;
    }

    public static NumberValueTooLowExceptionBuilder builder() {
        return new NumberValueTooLowExceptionBuilder();
    }

    @Override
    public AssertionErrorType type() {
        return AssertionErrorType.NUMBER_VALUE_TOO_LOW;
    }

    @Override
    public Map<String, String> parameters() {
        return Map.of("min", min, "courseId", value);
    }

    public static class NumberValueTooLowExceptionBuilder {

        private String field;
        private String minValue;
        private String value;

        public NumberValueTooLowExceptionBuilder field(String field) {
            this.field = field;

            return this;
        }

        public NumberValueTooLowExceptionBuilder minValue(String minValue) {
            this.minValue = minValue;

            return this;
        }

        public NumberValueTooLowExceptionBuilder value(String value) {
            this.value = value;

            return this;
        }

        public String message() {
            return "Value of field \"%s\" must be at least %s but was %s".formatted(field, minValue, value);
        }

        public NumberValueTooLowException build() {
            return new NumberValueTooLowException(this);
        }
    }
}
