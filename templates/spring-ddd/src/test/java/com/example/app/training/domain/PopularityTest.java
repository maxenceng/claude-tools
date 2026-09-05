package com.example.app.training.domain;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

import com.example.app.error.domain.NumberValueTooHighException;
import com.example.app.error.domain.NumberValueTooLowException;

class PopularityTest {

    @Test
    void shouldBuild() {
        assertThatCode(PopularityFixture::popularity).doesNotThrowAnyException();
    }

    @Test
    void shouldBuildAtZero() {
        assertThatCode(() -> new Popularity(0)).doesNotThrowAnyException();
    }

    @Test
    void shouldBuildAtOneHundred() {
        assertThatCode(() -> new Popularity(100)).doesNotThrowAnyException();
    }

    @Test
    void shouldNotBuildIfValueIsNegative() {
        assertThatThrownBy(() -> new Popularity(-1))
                .isExactlyInstanceOf(NumberValueTooLowException.class)
                .hasMessageContaining("popularity");
    }

    @Test
    void shouldNotBuildIfValueIsOverOneHundred() {
        assertThatThrownBy(() -> new Popularity(101))
                .isExactlyInstanceOf(NumberValueTooHighException.class)
                .hasMessageContaining("popularity");
    }
}
