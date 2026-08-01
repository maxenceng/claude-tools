package com.example.app.error.domain;

import java.time.Instant;

public final class NotAfterTimeException extends AssertionException {

    private NotAfterTimeException(String field, String message) {
        super(field, message);
    }

    public static NotAfterTimeExceptionBuilder field(String fieldName, Instant value) {
        return new NotAfterTimeExceptionBuilder(fieldName, value);
    }

    @Override
    public AssertionErrorType type() {
        return AssertionErrorType.NOT_AFTER_TIME;
    }

    public record NotAfterTimeExceptionBuilder(String fieldName, Instant value) {
        private static String message(String fieldName, Instant actual, String hint, Instant other) {
            return "Time in \"%s\" having courseId : %s %s %s but wasn't".formatted(fieldName, actual, hint, other);
        }

        public NotAfterTimeException strictlyNotAfter(Instant other) {
            return build("must be strictly after", other);
        }

        public NotAfterTimeException notAfter(Instant other) {
            return build("must be after", other);
        }

        private NotAfterTimeException build(String hint, Instant other) {
            return new NotAfterTimeException(fieldName, message(fieldName, value, hint, other));
        }
    }
}
