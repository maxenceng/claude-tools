package com.example.app;

import static com.tngtech.archunit.base.DescribedPredicate.not;
import static com.tngtech.archunit.core.domain.properties.HasModifiers.Predicates.modifier;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noMethods;

import com.tngtech.archunit.base.DescribedPredicate;
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaModifier;
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;

/**
 * Conventions about the tests themselves, so they are enforced rather than remembered.
 *
 * <p>Separate from {@code ArchitectureTest} because that one imports with
 * {@code DoNotIncludeTests} and therefore cannot see any of this.
 */
@AnalyzeClasses(packages = "com.example.app")
class TestConventionsTest {

	/**
	 * A private method in a unit test is a fixture only that class can reach. The second test
	 * needing the same value retypes it with a different literal, and the two boundaries
	 * drift apart without anything failing. Move it to the {@code <Type>Fixture} beside the
	 * type and name it for the state it represents.
	 *
	 * <p>Two kinds of class are out of scope. A test that boots a Spring context builds a
	 * call to a running application rather than a domain value, and a fixture is the wrong
	 * home for it; those are recognised by their annotation rather than by importing the
	 * slices, so this rule needs no test dependency a project has not added yet. ArchUnit
	 * rule holders are exempt too — their private methods are conditions, not fixtures.
	 * Synthetic methods are excluded because every lambda in a test compiles to one.
	 */
	@ArchTest
	static final ArchRule unit_tests_hold_only_tests = noMethods()
			.that()
			.areDeclaredInClassesThat()
			.haveSimpleNameEndingWith("Test")
			.and()
			.areDeclaredInClassesThat(not(bootASpringContextOrHoldArchitectureRules()))
			.and(not(modifier(JavaModifier.SYNTHETIC)))
			.should()
			.bePrivate()
			.because("a helper only one unit test can reach is a fixture in the wrong place");

	private static DescribedPredicate<JavaClass> bootASpringContextOrHoldArchitectureRules() {
		return DescribedPredicate.describe(
				"boot a Spring context or hold architecture rules",
				type -> type.isAnnotatedWith(AnalyzeClasses.class)
						|| type.getAnnotations().stream().anyMatch(annotation -> annotation.getRawType().getSimpleName().endsWith("Test")));
	}
}
