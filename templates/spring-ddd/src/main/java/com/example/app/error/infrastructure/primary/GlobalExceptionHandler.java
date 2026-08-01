package com.example.app.error.infrastructure.primary;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import com.example.app.error.domain.AssertionException;
import com.example.app.error.domain.DomainErrorStatus;
import com.example.app.error.domain.DomainException;

/**
 * Turns domain failures into HTTP responses, for every context at once.
 *
 * <p>There is one of these for the whole application rather than one per context. A
 * per-context advice has to be remembered when a context is added, and until it is,
 * that context's failures leak out as 500s. This handler covers a new context the
 * moment its exceptions extend {@link DomainException}, and {@code ArchitectureTest}
 * fails the build if second advice appears.
 *
 * <p>It maps {@link DomainErrorStatus} rather than exception types, so it needs no
 * import from any context — which is what lets it live outside all of them.
 */
@RestControllerAdvice
class GlobalExceptionHandler {

    @ExceptionHandler(DomainException.class)
    ProblemDetail handleDomainException(DomainException exception) {
        return ProblemDetail.forStatusAndDetail(statusOf(exception.status()), exception.getMessage());
    }

    /**
     * {@link AssertionException} means a value object was handed something invalid, so
     * the caller sent bad input. It is a separate hierarchy from {@link DomainException}
     * because it guards types rather than business rules, but over HTTP both are the
     * client's problem.
     */
    @ExceptionHandler(AssertionException.class)
    ProblemDetail handleAssertionException(AssertionException exception) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, exception.getMessage());
    }

    private static HttpStatus statusOf(DomainErrorStatus status) {
        return switch (status) {
            case NOT_FOUND -> HttpStatus.NOT_FOUND;
            case CONFLICT -> HttpStatus.CONFLICT;
            case INVALID -> HttpStatus.BAD_REQUEST;
        };
    }
}
