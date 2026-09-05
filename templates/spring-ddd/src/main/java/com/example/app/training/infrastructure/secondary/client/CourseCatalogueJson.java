package com.example.app.training.infrastructure.secondary.client;

import org.springframework.http.converter.json.JacksonJsonHttpMessageConverter;

import tools.jackson.databind.DeserializationFeature;
import tools.jackson.databind.json.JsonMapper;

/**
 * The training catalogue vendor's own JSON shape: an unknown field ignored rather than
 * refused, since a vendor answers with more than the one field this system maps.
 */
final class CourseCatalogueJson {

    private static final JsonMapper MAPPER = JsonMapper.builder()
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)
            .build();

    private CourseCatalogueJson() {
    }

    static JacksonJsonHttpMessageConverter converter() {
        return new JacksonJsonHttpMessageConverter(MAPPER);
    }
}
