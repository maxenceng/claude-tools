package com.example.app.error.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.math.BigDecimal;
import java.util.stream.Stream;

import org.junit.jupiter.api.Named;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.function.Executable;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;

/**
 * The zero boundary on every numeric asserter, and the wording of the errors they raise.
 *
 * <p>{@code positive()} accepts zero; {@code strictlyPositive()} does not. Both the
 * ddd-backend skill and every value object guarding a count depend on that distinction,
 * and a javadoc has already contradicted it once. Nothing else in this project exercises
 * the error kernel, so without these tests a change here reaches a domain model before
 * anyone notices.
 */
class AssertTest {

    private static final String FIELD = "quantity";

    static Stream<Named<Executable>> zero() {
        return Stream.of(
            Named.of("int", () -> Assert.field(FIELD, 0).positive()),
            Named.of("long", () -> Assert.field(FIELD, 0L).positive()),
            Named.of("float", () -> Assert.field(FIELD, 0f).positive()),
            Named.of("double", () -> Assert.field(FIELD, 0d).positive()),
            Named.of("BigDecimal", () -> Assert.field(FIELD, BigDecimal.ZERO).positive()));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("zero")
    void shouldAcceptZeroAsPositive(Executable assertion) {
        assertDoesNotThrow(assertion);
    }

    static Stream<Named<Executable>> strictlyPositiveAtZero() {
        return Stream.of(
            Named.of("int", () -> Assert.field(FIELD, 0).strictlyPositive()),
            Named.of("long", () -> Assert.field(FIELD, 0L).strictlyPositive()),
            Named.of("float", () -> Assert.field(FIELD, 0f).strictlyPositive()),
            Named.of("double", () -> Assert.field(FIELD, 0d).strictlyPositive()),
            Named.of("BigDecimal", () -> Assert.field(FIELD, BigDecimal.ZERO).strictlyPositive()));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("strictlyPositiveAtZero")
    void shouldRejectZeroAsStrictlyPositive(Executable assertion) {
        assertThrows(NumberValueTooLowException.class, assertion);
    }

    static Stream<Named<Executable>> strictlyPositiveAtOne() {
        return Stream.of(
            Named.of("int", () -> Assert.field(FIELD, 1).strictlyPositive()),
            Named.of("long", () -> Assert.field(FIELD, 1L).strictlyPositive()),
            Named.of("float", () -> Assert.field(FIELD, 1f).strictlyPositive()),
            Named.of("double", () -> Assert.field(FIELD, 1d).strictlyPositive()),
            Named.of("BigDecimal", () -> Assert.field(FIELD, BigDecimal.ONE).strictlyPositive()));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("strictlyPositiveAtOne")
    void shouldAcceptOneAsStrictlyPositive(Executable assertion) {
        assertDoesNotThrow(assertion);
    }

    static Stream<Named<Executable>> negative() {
        return Stream.of(
            Named.of("int", () -> Assert.field(FIELD, -1).positive()),
            Named.of("long", () -> Assert.field(FIELD, -1L).positive()),
            Named.of("float", () -> Assert.field(FIELD, -1f).positive()),
            Named.of("double", () -> Assert.field(FIELD, -1d).positive()),
            Named.of("BigDecimal", () -> Assert.field(FIELD, BigDecimal.valueOf(-1)).positive()));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("negative")
    void shouldRejectNegativeAsPositive(Executable assertion) {
        assertThrows(NumberValueTooLowException.class, assertion);
    }

    // The error kernel is generic and ships into every generated project. A bulk rename
    // once left a domain field name across these messages and parameter keys, so a
    // project with no courses in it reported a courseId. These two pin the vocabulary.

    @Test
    void shouldDescribeTheOffendingValueWithoutDomainVocabulary() {
        StringTooShortException error = assertThrows(
            StringTooShortException.class,
            () -> Assert.field(FIELD, "ab").minLength(5));

        assertThat(error.getMessage()).isEqualTo("The value in field \"quantity\" must be at least 5 long but was only 2");
    }

    @Test
    void shouldKeyErrorParametersGenerically() {
        NumberValueTooHighException error = assertThrows(
            NumberValueTooHighException.class,
            () -> Assert.field(FIELD, 3).max(2));

        assertThat(error.parameters()).containsOnlyKeys("max", "value");
        assertThat(error.field()).isEqualTo(FIELD);
    }
}
