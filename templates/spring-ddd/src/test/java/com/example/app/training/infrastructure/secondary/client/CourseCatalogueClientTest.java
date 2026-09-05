package com.example.app.training.infrastructure.secondary.client;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.BiFunction;

import org.junit.jupiter.api.Test;
import org.springframework.cloud.openfeign.support.SpringMvcContract;

import com.example.app.shared.infrastructure.secondary.OutboundClientSupport;

import feign.Client;
import feign.Feign;
import feign.Request;
import feign.Response;
import feign.codec.DecodeException;

class CourseCatalogueClientTest {

    private static final String CATALOGUE_URL = "https://api.example/api/courses";

    private static final BiFunction<String, Throwable, RuntimeException> UNREACHABLE =
            (detail, cause) -> new CourseCatalogueUnreachableException("training catalogue " + detail, cause);

    @Test
    void shouldSearchByTitleAndDeserialiseTheAnswer() {
        AtomicReference<Request> sent = new AtomicReference<>();
        CourseCatalogueClient client = client(respondingWith(sent, 200, """
                {"title": "Introduction to Hexagonal Architecture", "popularity": 73, "language": "en"}
                """));

        CourseCatalogueResponse answered = client.search("Introduction to Hexagonal Architecture");

        assertThat(sent.get().url()).contains("title=Introduction%20to%20Hexagonal%20Architecture");
        assertThat(answered.title()).isEqualTo("Introduction to Hexagonal Architecture");
        assertThat(answered.popularity()).isEqualTo(73);
    }

    @Test
    void shouldAnswerNoPopularityWhereTheBodyCarriesNone() {
        CourseCatalogueClient client = client(respondingWith(new AtomicReference<>(), 200, """
                {"title": "Introduction to Hexagonal Architecture"}
                """));

        CourseCatalogueResponse answered = client.search("Introduction to Hexagonal Architecture");

        assertThat(answered.toPopularity()).isEmpty();
    }

    @Test
    void shouldFailToDeserialiseABodyThisCannotRead() {
        CourseCatalogueClient client = client(respondingWith(new AtomicReference<>(), 200, """
                {"title": "Introduction to Hexagonal Architecture", "popularity": "not-a-number"}
                """));

        assertThatThrownBy(() -> client.search("Introduction to Hexagonal Architecture")).isInstanceOf(DecodeException.class);
    }

    @Test
    void shouldRefuseToAnswerWhenTheCatalogueCannotBeReached() {
        CourseCatalogueClient client = client((request, options) -> {
            throw new IOException("connection refused");
        });

        assertThatThrownBy(() -> client.search("Introduction to Hexagonal Architecture"))
                .isInstanceOf(CourseCatalogueUnreachableException.class)
                .hasRootCauseInstanceOf(IOException.class);
    }

    @Test
    void shouldRefuseToAnswerWhenTheCatalogueRefusesTheSearch() {
        CourseCatalogueClient client = client(respondingWith(new AtomicReference<>(), 500, "server error"));

        assertThatThrownBy(() -> client.search("Introduction to Hexagonal Architecture"))
                .isInstanceOf(CourseCatalogueUnreachableException.class);
    }

    static CourseCatalogueClient client(Client fake) {
        return Feign.builder()
                .contract(new SpringMvcContract())
                .decoder(OutboundClientSupport.decoder(CourseCatalogueJson.converter()))
                .errorDecoder(OutboundClientSupport.errorDecoder(UNREACHABLE))
                .client(OutboundClientSupport.transportFailures(fake, UNREACHABLE))
                .target(CourseCatalogueClient.class, CATALOGUE_URL);
    }

    static Client respondingWith(AtomicReference<Request> sent, int status, String body) {
        return (request, options) -> {
            sent.set(request);

            return Response.builder()
                    .status(status)
                    .reason(status == 200 ? "OK" : "Error")
                    .request(request)
                    .headers(Map.of("Content-Type", List.of("application/json")))
                    .body(body, StandardCharsets.UTF_8)
                    .build();
        };
    }
}
