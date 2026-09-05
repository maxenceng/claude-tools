package com.example.app.training.domain;

import static com.example.app.training.domain.CourseFixture.course;
import static com.example.app.training.domain.CourseFixture.courseWithPopularity;
import static com.example.app.training.domain.PopularityFixture.popularity;
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import java.util.Optional;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class CourseManagerTest {

    @Mock
    private CourseCataloguePort catalogue;

    @Test
    void shouldFillPopularityWhereTheCatalogueHasOne() {
        CourseManager manager = new CourseManager(catalogue);
        when(catalogue.lookup(course().title())).thenReturn(Optional.of(popularity()));

        Course filled = manager.fillPopularity(course());

        assertThat(filled.popularity()).contains(popularity());
    }

    @Test
    void shouldLeaveThePopularityAbsentWhereTheCatalogueHasNone() {
        CourseManager manager = new CourseManager(catalogue);
        when(catalogue.lookup(course().title())).thenReturn(Optional.empty());

        Course filled = manager.fillPopularity(course());

        assertThat(filled.popularity()).isEmpty();
    }

    @Test
    void shouldNotAskTheCatalogueWhereTheCourseAlreadyHasAPopularity() {
        CourseManager manager = new CourseManager(catalogue);

        Course unchanged = manager.fillPopularity(courseWithPopularity());

        assertThat(unchanged).isEqualTo(courseWithPopularity());
        verifyNoInteractions(catalogue);
    }
}
