package com.example.app.training.domain;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

import com.example.app.error.domain.MissingMandatoryValueException;

class CourseIdTest {

    @Test
    void shouldBuild() {
        assertThatCode(CourseIdFixture::courseId).doesNotThrowAnyException();
    }

    @Test
    void shouldNotBuildIfValueIsNull() {
        assertThatThrownBy(() -> new CourseId(null))
                .isExactlyInstanceOf(MissingMandatoryValueException.class)
                .hasMessageContaining("courseId");
    }
}
