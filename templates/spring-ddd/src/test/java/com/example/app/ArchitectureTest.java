package com.example.app;

import static com.tngtech.archunit.core.domain.properties.HasName.Predicates.nameMatching;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.fields;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noFields;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noMethods;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Repository;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import com.example.app.error.domain.DomainException;
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaField;
import com.tngtech.archunit.core.domain.JavaModifier;
import com.tngtech.archunit.core.domain.JavaParameterizedType;
import com.tngtech.archunit.core.domain.JavaType;
import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchCondition;
import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.lang.ConditionEvents;
import com.tngtech.archunit.lang.SimpleConditionEvent;

/**
 * Executable architecture. Every rule here is one that no longer needs to be
 * described in prose, reviewed by hand, or repeated to a coding agent.
 *
 * <p>Layering within a bounded context: infrastructure -> application -> domain.
 * Dependencies always point inward.
 */
@AnalyzeClasses(
		packages = "com.example.app",
		importOptions = ImportOption.DoNotIncludeTests.class)
class ArchitectureTest {

	@ArchTest
	static final ArchRule domain_is_free_of_frameworks = noClasses()
			.that()
			.resideInAPackage("..domain..")
			.should()
			.dependOnClassesThat()
			.resideInAnyPackage("org.springframework..", "jakarta..", "com.fasterxml..", "lombok..")
			.because("the domain models the business and must not know about frameworks. Lombok is "
					+ "named here but caught by DomainIsFreeOfLombokTest: its annotations are "
					+ "SOURCE-retention, so this rule never sees them - ADR 0005");

	@ArchTest
	static final ArchRule domain_does_not_depend_on_outer_layers = noClasses()
			.that()
			.resideInAPackage("..domain..")
			.should()
			.dependOnClassesThat()
			.resideInAnyPackage("..application..", "..infrastructure..")
			.because("dependencies point inward");

	@ArchTest
	static final ArchRule application_does_not_depend_on_infrastructure = noClasses()
			.that()
			.resideInAPackage("..application..")
			.should()
			.dependOnClassesThat()
			.resideInAPackage("..infrastructure..")
			.because("use cases talk to ports, never to adapters");

	@ArchTest
	static final ArchRule primary_adapters_do_not_depend_on_secondary_adapters = noClasses()
			.that()
			.resideInAPackage("..infrastructure.primary..")
			.should()
			.dependOnClassesThat()
			.resideInAPackage("..infrastructure.secondary..")
			.because("driving adapters reach persistence through the application layer");

	@ArchTest
	static final ArchRule ports_are_interfaces_declared_by_the_domain = classes()
			.that()
			.haveSimpleNameEndingWith("Port")
			.should()
			.beInterfaces()
			.andShould()
			.resideInAPackage("..domain..")
			.because("ports are owned by the domain, implemented by adapters");

	@ArchTest
	static final ArchRule controllers_live_in_primary_adapters = classes()
			.that()
			.areAnnotatedWith(RestController.class)
			.should()
			.resideInAPackage("..infrastructure.primary..")
			.because("HTTP is a driving adapter concern");

	@ArchTest
	static final ArchRule exception_handling_is_global = classes()
			.that()
			.areAnnotatedWith(RestControllerAdvice.class)
			.should()
			.resideInAPackage("..error.infrastructure.primary..")
			.because("domain failures map to HTTP in one place, so a new context is covered without adding an advice");

	@ArchTest
	static final ArchRule domain_types_expose_no_setters = noMethods()
			.that()
			.areDeclaredInClassesThat()
			.resideInAPackage("..domain..")
			.should()
			.haveNameMatching("set[A-Z].*")
			.because("aggregates expose intent-revealing behaviour, not setters");

	// ---------------------------------------------------------------------------
	// Shape of a bounded context.
	//
	// The rules above keep dependencies pointing inward. These keep a new context
	// looking like `training`, which is the part a reviewer would otherwise have to
	// check by reading. They are what makes "copy the shape of training" enforceable
	// rather than advisory.
	// ---------------------------------------------------------------------------

	@ArchTest
	static final ArchRule use_cases_are_named_application_services = classes()
			.that()
			.areAnnotatedWith(Service.class)
			.should()
			.resideInAPackage("..application..")
			.andShould()
			.haveSimpleNameEndingWith("ApplicationService")
			.because("the entry point to a use case should be findable by name");

	@ArchTest
	static final ArchRule managers_assert_nothing = noClasses()
			.that()
			.haveSimpleNameEndingWith("Manager")
			.should()
			.dependOnClassesThat()
			.resideInAPackage("..error..")
			.because("a manager orders the rules it holds and raises its own context's exceptions; "
					+ "reaching for the error kernel is how a use case starts second guessing "
					+ "the types it was handed");

	@ArchTest
	static final ArchRule persistence_lives_in_secondary_adapters = classes()
			.that()
			.areAnnotatedWith(Repository.class)
			.should()
			.resideInAPackage("..infrastructure.secondary..")
			.because("persistence is a driven adapter, whatever it is called");

	@ArchTest
	static final ArchRule wire_shapes_live_beside_their_controller = classes()
			.that()
			.haveSimpleNameEndingWith("Request")
			.or()
			.haveSimpleNameEndingWith("Response")
			.should()
			.resideInAnyPackage("..infrastructure.primary..", "..infrastructure.secondary.client..")
			.because("a request or response is the shape of a protocol, not of the domain — this system's own, "
					+ "answered beside the controller, or a vendor's, answered beside the client that speaks it "
					+ "- ADR 0009");

	@ArchTest
	static final ArchRule outbound_client_helpers_stay_package_private = classes()
			.that()
			.resideInAPackage("..infrastructure.secondary.client..")
			.and()
			.haveSimpleNameNotEndingWith("Client")
			.and()
			.haveSimpleNameNotEndingWith("Request")
			.and()
			.haveSimpleNameNotEndingWith("Response")
			.and()
			.haveSimpleNameNotEndingWith("Builder")
			.and()
			.areNotAssignableTo(Throwable.class)
			.should()
			.bePackagePrivate()
			.because("a client interface, the wire shapes it maps and the failure it raises are the "
					+ "package's contract with its caller; anything else in there - Lombok's generated "
					+ "builder included - is a helper that belongs beside them, not made public to reach "
					+ "it from outside");

	@ArchTest
	static final ArchRule business_failures_extend_domain_exception = classes()
			.that()
			.resideInAPackage("..domain..")
			.and()
			.resideOutsideOfPackage("..error..")
			.and()
			.haveSimpleNameEndingWith("Exception")
			.should()
			.beAssignableTo(DomainException.class)
			.because("the global handler answers on DomainException; anything else leaves as a 500");

	@ArchTest
	static final ArchRule domain_state_is_final = fields()
			.that()
			.areDeclaredInClassesThat()
			.resideInAPackage("..domain..")
			.and()
			.areDeclaredInClassesThat()
			.haveSimpleNameNotEndingWith("Builder")
			.should()
			.beFinal()
			.because("a domain object that can be mutated after construction cannot hold an invariant");

	@ArchTest
	static final ArchRule dependencies_are_injected_through_constructors = noFields()
			.should()
			.beAnnotatedWith(Autowired.class)
			.because("field injection hides a dependency and cannot be set in a plain unit test");

	/**
	 * A port is a dependency the domain declares and a domain service holds. An adapter that
	 * holds one is a second place deciding what a missing row or a failed call means, and the
	 * manager stops being the only entry to the use case.
	 *
	 * <p>Adapters still <em>implement</em> ports. This constrains what they hold, not what
	 * they satisfy.
	 */
	@ArchTest
	static final ArchRule ports_are_held_only_by_the_domain = fields()
			.that()
			.haveRawType(nameMatching(".*Port"))
			.should()
			.beDeclaredInClassesThat()
			.resideInAPackage("..domain..")
			.because("a port is held by the domain service that needs it, not by an adapter");

	/**
	 * Driven adapters are called by the domain through a port; they do not call inward
	 * themselves. Reaching for an application service from {@code secondary} inverts the
	 * direction everything else points.
	 */
	@ArchTest
	static final ArchRule driven_adapters_do_not_call_the_application_layer = noClasses()
			.that()
			.resideInAPackage("..infrastructure.secondary..")
			.should()
			.dependOnClassesThat()
			.resideInAPackage("..application..")
			.because("what is in secondary stays in secondary");

	/**
	 * A value object wraps one thing. A domain record holding several holds value objects,
	 * not raw values — so a primitive or a JDK type appears in exactly one place, the type
	 * that gives it a name and a rule. {@code boolean} is the exception: there is nothing to
	 * validate and no name worth inventing.
	 *
	 * <p>The payoff is not tidiness. Every rule belonging to the raw value — a format, a
	 * bound, a {@code toString} that must not print it — then has one home, and each type
	 * holding it inherits that rule instead of remembering it.
	 */
	@ArchTest
	static final ArchRule composite_domain_types_hold_value_objects = classes()
			.that()
			.resideInAPackage("..domain..")
			.and()
			.resideOutsideOfPackage("..error..")
			.and()
			.areNotEnums()
			.and()
			.areNotAssignableTo(Throwable.class)
			.and()
			.haveSimpleNameNotEndingWith("Builder")
			.should(holdOnlyDomainTypesWhenTheyHoldMoreThanOne())
			.because("a raw value belongs in the value object that names it, not spread across the types that use it");

	/**
	 * The three carriers a composite may hold raw, because naming them names nothing: a list, a map
	 * and a pair are shapes rather than values, and what they carry is already a domain type. Pair
	 * is matched by simple name so that whichever one a project adopts is covered.
	 */
	private static final Set<String> CARRIERS_WITH_NOTHING_TO_NAME = Set.of(List.class.getName(), Map.class.getName());

	private static ArchCondition<JavaClass> holdOnlyDomainTypesWhenTheyHoldMoreThanOne() {
		return new ArchCondition<>("hold only domain types when they hold more than one") {

			@Override
			public void check(JavaClass record, ConditionEvents events) {
				List<JavaField> components = record.getFields().stream()
						.filter(field -> !field.getModifiers().contains(JavaModifier.STATIC))
						.toList();
				if (components.size() < 2) {
					return;
				}

				components.forEach(component -> check(record, component, events));
			}

			private static void check(JavaClass owner, JavaField component, ConditionEvents events) {
				if (isCarrier(component.getRawType())) {
					carriedTypes(component)
							.filter(carried -> isRawValue(carried))
							.forEach(carried -> events.add(SimpleConditionEvent.violated(
									component,
									"%s holds %s<%s>; the carrier is fine, what it carries is a raw value".formatted(
											owner.getSimpleName(), component.getRawType().getSimpleName(), carried.getSimpleName()))));
					return;
				}

				if (isRawValue(component.getRawType())) {
					events.add(SimpleConditionEvent.violated(
							component,
							"%s holds %s directly; wrap it in a value object".formatted(owner.getSimpleName(), component.getRawType().getSimpleName())));
				}
			}

			private static Stream<JavaClass> carriedTypes(JavaField component) {
				if (component.getType() instanceof JavaParameterizedType parameterized) {
					return parameterized.getActualTypeArguments().stream().map(JavaType::toErasure);
				}

				return Stream.empty();
			}

			private static boolean isCarrier(JavaClass type) {
				return CARRIERS_WITH_NOTHING_TO_NAME.contains(type.getName()) || type.getSimpleName().equals("Pair");
			}

			private static boolean isRawValue(JavaClass type) {
				if (type.getName().equals(boolean.class.getName())) {
					return false;
				}

				return type.isPrimitive() || type.getPackageName().startsWith("java.");
			}
		};
	}
}
