package com.example.app.training.infrastructure.secondary.client;

/**
 * The training catalogue vendor did not answer something this adapter could use.
 *
 * <p>Not a {@code DomainException} (ADR 0009): no business rule was broken, and this worked
 * example has no controller and no Temporal workflow waiting on the answer to decide what a
 * failure means — see `ddd-backend`'s references/outbound-clients.md for both shapes. Left to
 * propagate here rather than caught, since nothing in `training` is the right place to decide
 * what a caller should do about it; a real caller — a controller, a scheduled workflow — is
 * where that decision belongs.
 *
 * <p>Public: {@code CourseCatalogueRepository} throws it from outside this package.
 */
public class CourseCatalogueUnreachableException extends RuntimeException {

    public CourseCatalogueUnreachableException(String message, Throwable cause) {
        super(message, cause);
    }
}
