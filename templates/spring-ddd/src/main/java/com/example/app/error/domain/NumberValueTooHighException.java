package com.example.app.error.domain;

import static java.util.Objects.requireNonNull;

import java.util.Map;

public final class NumberValueTooHighException extends AssertionException {

    private final String max;
    private final String value;

    private NumberValueTooHighException(NumberValueTooHighExceptionBuilder builder) {
        super(requireNonNull(builder.field), builder.message());
        Assert.notNull("max", builder.maxValue);
        Assert.notNull("courseId", builder.value);
        max = builder.maxValue;
        value = builder.value;
    }

    public static NumberValueTooHighExceptionBuilder builder() {
        return new NumberValueTooHighExceptionBuilder();
    }

    @Override
    public AssertionErrorType type() {
        return AssertionErrorType.NUMBER_VALUE_TOO_HIGH;
    }

    @Override
    public Map<String, String> parameters() {
        return Map.of("max", max, "courseId", value);
    }

    public static class NumberValueTooHighExceptionBuilder {

        private String field;
        private String maxValue;
        private String value;

        public NumberValueTooHighExceptionBuilder field(String field) {
            this.field = field;

            return this;
        }

        public NumberValueTooHighExceptionBuilder maxValue(String maxValue) {
            this.maxValue = maxValue;

            return this;
        }

        public NumberValueTooHighExceptionBuilder value(String value) {
            this.value = value;

            return this;
        }

        public String message() {
            return "Value of field \"%s\" must be at most %s but was %s".formatted(field, maxValue, value);
        }

        public NumberValueTooHighException build() {
            return new NumberValueTooHighException(this);
        }
    }
}
