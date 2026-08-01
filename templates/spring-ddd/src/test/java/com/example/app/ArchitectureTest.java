package com.example.app;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.fields;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noFields;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noMethods;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Repository;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import com.example.app.error.domain.DomainException;
import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;

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
			.resideInAnyPackage("org.springframework..", "jakarta..", "com.fasterxml..")
			.because("the domain models the business and must not know about frameworks");

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
			.resideInAPackage("..infrastructure.primary..")
			.because("a request or response is the shape of a protocol, not of the domain");

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
}
