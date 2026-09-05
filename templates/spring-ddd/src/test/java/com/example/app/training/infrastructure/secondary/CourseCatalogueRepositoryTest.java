package com.example.app.training.infrastructure.secondary;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

import java.util.Optional;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.example.app.training.domain.Popularity;
import com.example.app.training.domain.Title;
import com.example.app.training.infrastructure.secondary.client.CourseCatalogueClient;
import com.example.app.training.infrastructure.secondary.client.CourseCatalogueResponse;

@ExtendWith(MockitoExtension.class)
class CourseCatalogueRepositoryTest {

    @Mock
    private CourseCatalogueClient catalogue;

    @InjectMocks
    private CourseCatalogueRepository repository;

    @Test
    void shouldAnswerThePopularityTheCatalogueAnswers() {
        Title title = new Title("Introduction to Hexagonal Architecture");
        when(catalogue.search(title.value())).thenReturn(CourseCatalogueResponse.builder().title(title.value()).popularity(73).build());

        Optional<Popularity> answered = repository.lookup(title);

        assertThat(answered).contains(new Popularity(73));
    }

    @Test
    void shouldAnswerNoPopularityWhereTheCatalogueHasNone() {
        Title title = new Title("Introduction to Hexagonal Architecture");
        when(catalogue.search(title.value())).thenReturn(CourseCatalogueResponse.builder().title(title.value()).build());

        Optional<Popularity> answered = repository.lookup(title);

        assertThat(answered).isEmpty();
    }
}
