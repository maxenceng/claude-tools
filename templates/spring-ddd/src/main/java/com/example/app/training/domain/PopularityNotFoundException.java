package com.example.app.training.domain;

import com.example.app.error.domain.DomainErrorStatus;
import com.example.app.error.domain.DomainException;

/** The catalogue vendor has no popularity for this title — yet; it may supply one later. */
public class PopularityNotFoundException extends DomainException {

    public PopularityNotFoundException(Title title) {
        super(DomainErrorStatus.NOT_FOUND, "No popularity for \"" + title.value() + "\" yet");
    }
}
