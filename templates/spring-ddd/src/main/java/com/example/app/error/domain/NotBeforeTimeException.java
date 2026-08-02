package com.example.app.error.domain;

import java.time.Instant;

public final class NotBeforeTimeException extends AssertionException {

    private NotBeforeTimeException(String field, String message) {
        super(field, message);
    }

    public static NotBeforeTimeException.NotBeforeTimeExceptionBuilder field(String fieldName, Instant value) {
        return new NotBeforeTimeException.NotBeforeTimeExceptionBuilder(fieldName, value);
    }

    @Override
    public AssertionErrorType type() {
        return AssertionErrorType.NOT_BEFORE_TIME;
    }

    public record NotBeforeTimeExceptionBuilder(String fieldName, Instant value) {
        private static String message(String fieldName, Instant actual, String hint, Instant other) {
            return "Time in \"%s\" having value : %s %s %s but wasn't".formatted(fieldName, actual, hint, other);
        }

        public NotBeforeTimeException strictlyNotBefore(Instant other) {
            return build("must be strictly before", other);
        }

        public NotBeforeTimeException notBefore(Instant other) {
            return build("must be before", other);
        }

        private NotBeforeTimeException build(String hint, Instant other) {
            return new NotBeforeTimeException(fieldName, message(fieldName, value, hint, other));
        }
    }
}
