package com.example.app.error.domain;

/**
 * What kind of failure a {@link DomainException} represents, in business terms.
 *
 * <p>This exists so that one handler can map every domain exception to a protocol
 * response without importing any context's internals. A handler that switched on
 * {@code CourseNotFoundException} would have to import {@code training.domain}, which
 * the module boundaries forbid — and would need editing every time a context adds an
 * exception.
 *
 * <p>These are deliberately not HTTP status codes. The domain must stay free of
 * frameworks, and the same failure maps to different codes over different protocols.
 * The translation lives in {@code error.infrastructure.primary}.
 */
public enum DomainErrorStatus {
    /** The thing referred to does not exist. */
    NOT_FOUND,

    /** The request is well formed, but the current state does not allow it. */
    CONFLICT,

    /** The request itself is not valid, whatever the current state is. */
    INVALID,
}
