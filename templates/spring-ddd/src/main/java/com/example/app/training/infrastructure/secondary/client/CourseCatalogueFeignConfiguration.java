package com.example.app.training.infrastructure.secondary.client;

import java.util.function.BiFunction;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;

import com.example.app.shared.infrastructure.secondary.OutboundClientSupport;

import feign.Client;
import feign.RequestInterceptor;
import feign.codec.Decoder;
import feign.codec.ErrorDecoder;

/**
 * {@link CourseCatalogueClient}'s Feign configuration: the vendor's own JSON shape, its key on
 * every request, and every way a call can fail brought back to one
 * {@link CourseCatalogueUnreachableException} (ADR 0009).
 *
 * <p>Not a {@code @Configuration}: a Feign client's configuration class is registered into that
 * client's own child context by {@code @FeignClient} itself, and annotating it besides would
 * also hand it to the application's own component scan, which is the one place a bean here must
 * never be seen from — see {@link CourseCatalogueApiKeyParameter}.
 *
 * <p>No shared base class here the way next-suggestions' {@code BaseFeignConfiguration}
 * abstracts this for two vendors — this template has one, and an abstraction with a single
 * user is indirection with no benefit yet (see `ddd-backend`'s Frequent mistakes section).
 */
class CourseCatalogueFeignConfiguration {

    private static final BiFunction<String, Throwable, RuntimeException> UNREACHABLE =
            (detail, cause) -> new CourseCatalogueUnreachableException("training catalogue " + detail, cause);

    @Bean
    Decoder decoder() {
        return OutboundClientSupport.decoder(CourseCatalogueJson.converter());
    }

    @Bean
    Client transportFailures() {
        return OutboundClientSupport.transportFailures(new Client.Default(null, null), UNREACHABLE);
    }

    @Bean
    ErrorDecoder errorDecoder() {
        return OutboundClientSupport.errorDecoder(UNREACHABLE);
    }

    @Bean
    RequestInterceptor apiKeyParameter(@Value("${training.catalogue.api-key}") String apiKey) {
        return new CourseCatalogueApiKeyParameter(apiKey);
    }
}
