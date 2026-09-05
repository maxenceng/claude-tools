package com.example.app.training.infrastructure.secondary;

import java.util.Optional;

import org.springframework.stereotype.Repository;

import com.example.app.training.domain.CourseCataloguePort;
import com.example.app.training.domain.Popularity;
import com.example.app.training.domain.Title;
import com.example.app.training.infrastructure.secondary.client.CourseCatalogueClient;
import com.example.app.training.infrastructure.secondary.client.CourseCatalogueResponse;

/**
 * Looks a course up on the training catalogue vendor, named for the port it satisfies rather
 * than for the vendor behind it.
 *
 * <p>{@code catalogue.search} is what raises on failure: its Feign configuration turns every way
 * the call can fail into {@code CourseCatalogueUnreachableException} (ADR 0009), so this adapter
 * is left reading the answer, not the failure.
 */
@Repository
class CourseCatalogueRepository implements CourseCataloguePort {

    private final CourseCatalogueClient catalogue;

    CourseCatalogueRepository(CourseCatalogueClient catalogue) {
        this.catalogue = catalogue;
    }

    @Override
    public Optional<Popularity> lookup(Title title) {
        CourseCatalogueResponse answered = catalogue.search(title.value());

        return answered != null ? answered.toPopularity() : Optional.empty();
    }
}
