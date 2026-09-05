package com.example.app.training.infrastructure.secondary.client;

import java.util.Optional;

import com.example.app.training.domain.Popularity;

import lombok.Builder;

/**
 * A course as the training catalogue vendor answers it. Two fields of however many it actually
 * sends — this system asked for one, and the vendor's own name for a course travels along only
 * so a caller can tell whether the answer is about the course it asked for.
 */
@Builder
public record CourseCatalogueResponse(String title, Integer popularity) {

    /** Empty where the vendor has not scored this course. Never null. */
    public Optional<Popularity> toPopularity() {
        return popularity != null ? Optional.of(new Popularity(popularity)) : Optional.empty();
    }
}
