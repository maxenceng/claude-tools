package com.example.app.training.domain;

import java.util.Optional;

/** What the training catalogue vendor can answer about a course, by title. */
public interface CourseCataloguePort {

    Optional<Popularity> lookup(Title title);
}
