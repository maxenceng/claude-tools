package com.example.app.training.domain;

import static com.example.app.training.domain.CourseFixture.course;
import static com.example.app.training.domain.CourseFixture.courseBuilder;
import static com.example.app.training.domain.CourseFixture.courseWithPopularity;
import static com.example.app.training.domain.PopularityFixture.popularity;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

import com.example.app.error.domain.MissingMandatoryValueException;

class CourseTest {

    @Test
    void shouldBuild() {
        assertThatCode(CourseFixture::course).doesNotThrowAnyException();
    }

    @Test
    void shouldNotBuildIfIdIsNull() {
        assertThatThrownBy(() -> courseBuilder().id(null).build())
                .isExactlyInstanceOf(MissingMandatoryValueException.class)
                .hasMessageContaining("id");
    }

    @Test
    void shouldNotBuildIfTitleIsNull() {
        assertThatThrownBy(() -> courseBuilder().title(null).build())
                .isExactlyInstanceOf(MissingMandatoryValueException.class)
                .hasMessageContaining("title");
    }

    @Test
    void shouldAnswerNoPopularityUntilOneIsFilled() {
        assertThat(course().popularity()).isEmpty();
    }

    @Test
    void shouldAnswerThePopularityItWasBuiltWith() {
        assertThat(courseWithPopularity().popularity()).contains(popularity());
    }

    @Test
    void shouldFillPopularityLeavingEveryOtherFieldAlone() {
        Course filled = course().withPopularity(popularity());

        assertThat(filled.id()).isEqualTo(course().id());
        assertThat(filled.title()).isEqualTo(course().title());
        assertThat(filled.popularity()).contains(popularity());
    }

    @Test
    void shouldNotFillANullPopularity() {
        assertThatThrownBy(() -> course().withPopularity(null))
                .isExactlyInstanceOf(MissingMandatoryValueException.class)
                .hasMessageContaining("popularity");
    }
}
