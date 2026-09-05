package com.example.app.training.infrastructure.secondary.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * The one call {@code CourseCatalogueRepository} makes: a course looked up by its title.
 *
 * <p>The API key is not a parameter here — a request interceptor configured below appends it
 * to every call, which is what keeps the credential inside this package instead of on the
 * adapter that asks the question.
 */
@FeignClient(name = "course-catalogue", url = "${training.catalogue.url}", configuration = CourseCatalogueFeignConfiguration.class)
public interface CourseCatalogueClient {

    @GetMapping
    CourseCatalogueResponse search(@RequestParam("title") String title);
}
