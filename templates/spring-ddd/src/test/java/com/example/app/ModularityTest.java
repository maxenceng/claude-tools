package com.example.app;

import org.junit.jupiter.api.Test;
import org.springframework.modulith.core.ApplicationModules;
import org.springframework.modulith.docs.Documenter;

/**
 * Verifies bounded context boundaries and regenerates architecture documentation.
 *
 * <p>Each direct subpackage of the application package is a module. Its nested packages are
 * internal unless one carries {@code @NamedInterface} - a {@code published} package, or an
 * {@code infrastructure.query} or {@code infrastructure.command} one (ADR 0012) - so
 * {@code training.domain} is unreachable from another context by construction.
 *
 * <p>The doc task writes PlantUML diagrams and module canvases to
 * {@code target/spring-modulith-docs} — architecture documentation that cannot drift
 * from the code, because it is derived from it.
 */
class ModularityTest {

	static final ApplicationModules modules = ApplicationModules.of(Application.class);

	@Test
	void shouldRespectBoundedContextBoundaries() {
		modules.verify();
	}

	@Test
	void shouldGenerateArchitectureDocumentation() {
		new Documenter(modules)
				.writeModulesAsPlantUml()
				.writeIndividualModulesAsPlantUml()
				.writeModuleCanvases();
	}
}
