package com.example.app.training.infrastructure.secondary.client;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.assertj.core.api.Assertions.catchThrowable;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;

import org.junit.jupiter.api.Test;
import org.springframework.cloud.openfeign.support.SpringMvcContract;

import com.example.app.shared.infrastructure.secondary.OutboundClientSupport;

import feign.Client;
import feign.Feign;
import feign.Logger;
import feign.Request;
import feign.Response;
import feign.codec.DecodeException;

class CourseCatalogueClientTest {

    private static final String CATALOGUE_URL = "https://api.example/api/courses";

    private static final Function<String, RuntimeException> UNREACHABLE = CourseCatalogueUnreachableException::new;

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
                .cause()
                .hasMessageContaining("IOException");
    }

    @Test
    void shouldKeepTheQueryStringOutOfATransportFailure() {
        CourseCatalogueClient client = client((request, options) -> {
            throw new IOException("Server returned HTTP response code: 500 for URL: " + request.url() + "&key=secret");
        });

        Throwable failure = catchThrowable(() -> client.search("Introduction to Hexagonal Architecture"));

        assertThat(failure).isInstanceOf(CourseCatalogueUnreachableException.class);
        assertThat(messagesOf(failure)).noneMatch(message -> message.contains("secret") || message.contains("?"))
                .anyMatch(message -> message.contains("GET " + CATALOGUE_URL));
    }

    @Test
    void shouldKeepTheQueryStringOutOfARefusal() {
        CourseCatalogueClient client = client(respondingWith(new AtomicReference<>(), 500, "server error"));

        Throwable failure = catchThrowable(() -> client.search("secret"));

        assertThat(messagesOf(failure)).noneMatch(message -> message.contains("secret") || message.contains("?"));
    }

    @Test
    void shouldKeepTheQueryStringOutOfABodyThatBreaksOffWhileFeignLogsTheResponse() {
        CourseCatalogueClient client = client(respondingWithABodyThatBreaksOff(64), Logger.Level.HEADERS);

        Throwable failure = catchThrowable(() -> client.search("secret"));

        assertThat(failure).isInstanceOf(CourseCatalogueUnreachableException.class);
        assertThat(messagesOf(failure)).noneMatch(message -> message.contains("secret") || message.contains("?"))
                .anyMatch(message -> message.contains("GET " + CATALOGUE_URL) && message.contains("IOException"));
    }

    @Test
    void shouldKeepTheQueryStringOutOfABodyThatBreaksOffWhileDecoded() {
        CourseCatalogueClient client = client(respondingWithABodyThatBreaksOff(null));

        Throwable failure = catchThrowable(() -> client.search("secret"));

        assertThat(failure).isInstanceOf(CourseCatalogueUnreachableException.class);
        assertThat(messagesOf(failure)).noneMatch(message -> message.contains("secret") || message.contains("?"));
    }

    @Test
    void shouldKeepTheQueryStringOutOfABodyThisCannotRead() {
        CourseCatalogueClient client = client(respondingWith(new AtomicReference<>(), 200, """
                {"title": "Introduction to Hexagonal Architecture", "popularity": "not-a-number"}
                """));

        Throwable failure = catchThrowable(() -> client.search("secret"));

        assertThat(failure).isInstanceOf(DecodeException.class);
        assertThat(messagesOf(failure)).noneMatch(message -> message.contains("secret") || message.contains("?"));
    }

    @Test
    void shouldRefuseToAnswerWhenTheCatalogueRefusesTheSearch() {
        CourseCatalogueClient client = client(respondingWith(new AtomicReference<>(), 500, "server error"));

        assertThatThrownBy(() -> client.search("Introduction to Hexagonal Architecture"))
                .isInstanceOf(CourseCatalogueUnreachableException.class)
                .hasMessage("The training catalogue did not answer; try again later.")
                .cause()
                .hasMessageContaining("HTTP 500");
    }

    static List<String> messagesOf(Throwable failure) {
        List<String> messages = new ArrayList<>();
        for (Throwable link = failure; link != null; link = link.getCause()) {
            messages.add(String.valueOf(link.getMessage()));
        }
        return messages;
    }

    static CourseCatalogueClient client(Client fake) {
        return client(fake, Logger.Level.NONE);
    }

    static CourseCatalogueClient client(Client fake, Logger.Level logLevel) {
        return Feign.builder()
                .logger(new DiscardingLogger())
                .logLevel(logLevel)
                .contract(new SpringMvcContract())
                .decoder(OutboundClientSupport.decoder(CourseCatalogueJson.converter()))
                .errorDecoder(OutboundClientSupport.errorDecoder(UNREACHABLE))
                .client(OutboundClientSupport.transportFailures(fake, UNREACHABLE))
                .target(CourseCatalogueClient.class, CATALOGUE_URL);
    }

    static Client respondingWithABodyThatBreaksOff(Integer declaredLength) {
        return (request, options) -> Response.builder()
                .status(200)
                .reason("OK")
                .request(request)
                .headers(Map.of("Content-Type", List.of("application/json")))
                .body(new BreakingBody(declaredLength))
                .build();
    }

    static final class DiscardingLogger extends Logger {

        @Override
        protected void log(String configKey, String format, Object... args) {
        }
    }

    record BreakingBody(Integer length) implements Response.Body {

        @Override
        public boolean isRepeatable() {
            return false;
        }

        @Override
        public InputStream asInputStream() {
            return new InputStream() {
                @Override
                public int read() throws IOException {
                    throw new IOException("Connection reset");
                }
            };
        }

        @Override
        public Reader asReader(Charset charset) {
            return new InputStreamReader(asInputStream(), charset);
        }

        @Override
        public void close() {
        }
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
