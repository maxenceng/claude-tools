package com.example.app.training.infrastructure.secondary.client;

import com.example.app.error.domain.DomainErrorStatus;
import com.example.app.error.domain.DomainException;

/**
 * The training catalogue vendor did not answer something this adapter could use.
 *
 * <p>A {@code DomainException} with {@code UNAVAILABLE} because a controller now calls this lookup
 * and the caller must be told to retry, not that its input was wrong (ADR 0009, ADR 0010); see
 * `ddd-backend`'s references/outbound-clients.md. Left to propagate rather than caught, since
 * nothing in {@code training} is the right place to decide what a caller should do about it.
 *
 * <p>Public: {@code CourseCatalogueRepository} throws it from outside this package.
 */
public class CourseCatalogueUnreachableException extends DomainException {

    public CourseCatalogueUnreachableException(String message, Throwable cause) {
        super(DomainErrorStatus.UNAVAILABLE, message, cause);
    }
}
