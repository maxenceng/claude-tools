package com.example.app.training.domain;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

import com.example.app.error.domain.MissingMandatoryValueException;

class TitleTest {

    @Test
    void shouldBuild() {
        assertThatCode(TitleFixture::title).doesNotThrowAnyException();
    }

    @Test
    void shouldNotBuildIfValueIsBlank() {
        assertThatThrownBy(() -> new Title(" "))
                .isExactlyInstanceOf(MissingMandatoryValueException.class)
                .hasMessageContaining("title");
    }
}
