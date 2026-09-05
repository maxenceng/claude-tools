package com.example.app.training.infrastructure.secondary.client;

import feign.RequestInterceptor;
import feign.RequestTemplate;

/**
 * Every request {@link CourseCatalogueClient} makes carries the vendor's API key, taken as a
 * query parameter. One interceptor is one place to get it right, instead of a credential named
 * as a parameter on every method the client ever grows.
 *
 * <p>Not a {@code @Component}: a bean collected by type — {@link RequestInterceptor} included —
 * is collected from every Feign client's context, this vendor's key included on a call to any
 * other. Built instead inside {@link CourseCatalogueFeignConfiguration}'s own bean method, which
 * only {@link CourseCatalogueClient} is wired to.
 */
final class CourseCatalogueApiKeyParameter implements RequestInterceptor {

    private final String apiKey;

    CourseCatalogueApiKeyParameter(String apiKey) {
        this.apiKey = apiKey;
    }

    @Override
    public void apply(RequestTemplate template) {
        template.query("key", apiKey);
    }
}
