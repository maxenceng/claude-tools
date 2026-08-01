package com.example.app.shared.infrastructure.primary;

import java.util.List;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.servers.Server;

/**
 * Describes the API that {@code docs/openapi.json} is captured from.
 *
 * <p>This is not cosmetic. The captured schema is committed and the frontend's client is
 * generated from it, so everything here ends up in another codebase's build output.
 *
 * <p>A bean rather than {@code @OpenAPIDefinition} on a class: the values are ordinary
 * Java, so they can come from configuration later without rewriting annotations.
 */
@Configuration(proxyBeanMethods = false)
class OpenApiConfiguration {

    /**
     * The version of the HTTP contract, which is not the version of the build. Bumping
     * the Maven version does not change what a client may rely on; a breaking change to
     * a route does. Only the second belongs here.
     */
    private static final String API_VERSION = "v1";

    @Bean
    OpenAPI applicationApi() {
        return new OpenAPI()
                .info(new Info()
                        .title("app API")
                        .description("""
                                Describe what this API is for, in the language of the domain. \
                                This text reaches the frontend's generated client and anyone reading \
                                Swagger UI, so it is worth a sentence rather than a placeholder.

                                Failure responses are RFC 7807 problem details, produced centrally by \
                                GlobalExceptionHandler: 404 for something that does not exist, 409 for \
                                a request the current state does not allow, 400 for one that was never \
                                valid.""")
                        .version(API_VERSION)
                        .license(new License().name("Unlicensed")))
                // Relative, so the schema does not pin the machine that captured it.
                // springdoc otherwise writes an absolute http://localhost:8080, which
                // would appear as a diff every time it is captured elsewhere.
                .servers(List.of(new Server()
                        .url("/")
                        .description("Same origin as the caller")));
    }
}
