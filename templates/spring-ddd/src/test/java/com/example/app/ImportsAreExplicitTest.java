package com.example.app;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;

class ImportsAreExplicitTest {

	private static final List<Path> SOURCE_ROOTS = List.of(Path.of("src/main/java"), Path.of("src/test/java"));

	private static final Pattern WILDCARD_IMPORT = Pattern.compile("^\\s*import\\s+(?:static\\s+)?[\\w.]+\\.\\*\\s*;");

	@Test
	void shouldScanEverySourceRoot() {
		assertThat(SOURCE_ROOTS).allMatch(Files::isDirectory);
	}

	@Test
	void shouldNameEveryImportedType() throws IOException {
		List<String> wildcards = new ArrayList<>();

		for (Path root : SOURCE_ROOTS) {
			List<Path> sources;
			try (Stream<Path> tree = Files.walk(root)) {
				sources = tree.filter(Files::isRegularFile)
						.filter(source -> source.getFileName().toString().endsWith(".java"))
						.toList();
			}

			for (Path source : sources) {
				List<String> lines = Files.readAllLines(source);

				for (int line = 0; line < lines.size(); line++) {
					if (WILDCARD_IMPORT.matcher(lines.get(line)).find()) {
						wildcards.add("%s:%d %s".formatted(source, line + 1, lines.get(line).strip()));
					}
				}
			}
		}

		assertThat(wildcards)
				.as("every imported type is named, so what a file depends on is readable from its head - ADR 0004")
				.isEmpty();
	}
}
