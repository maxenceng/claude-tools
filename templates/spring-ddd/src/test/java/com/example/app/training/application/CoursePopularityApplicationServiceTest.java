package com.example.app.training.application;

import static com.example.app.training.domain.PopularityFixture.popularity;
import static com.example.app.training.domain.TitleFixture.title;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

import java.util.Optional;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.example.app.training.domain.CourseCataloguePort;
import com.example.app.training.domain.PopularityNotFoundException;

@ExtendWith(MockitoExtension.class)
class CoursePopularityApplicationServiceTest {

    @Mock
    private CourseCataloguePort catalogue;

    @InjectMocks
    private CoursePopularityApplicationService service;

    @Test
    void shouldAnswerThePopularityTheCatalogueHas() {
        when(catalogue.lookup(title())).thenReturn(Optional.of(popularity()));

        assertThat(service.popularityOf(title())).isEqualTo(popularity());
    }

    @Test
    void shouldThrowPopularityNotFoundExceptionWhereTheCatalogueHasNone() {
        when(catalogue.lookup(title())).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.popularityOf(title())).isExactlyInstanceOf(PopularityNotFoundException.class);
    }
}
