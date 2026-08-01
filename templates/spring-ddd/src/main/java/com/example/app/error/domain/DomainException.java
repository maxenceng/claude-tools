package com.example.app.error.domain;

/**
 * Base type for violations of a business rule.
 *
 * <p>Every subclass declares a {@link DomainErrorStatus} so the global handler can
 * answer with the right protocol response without knowing the subclass. Choosing that
 * status is a modelling decision and belongs with the rule, not with the adapter.
 */
public abstract class DomainException extends RuntimeException {

    private final DomainErrorStatus status;

    protected DomainException(DomainErrorStatus status, String message) {
        super(message);
        this.status = status;
    }

    public DomainErrorStatus status() {
        return status;
    }
}
