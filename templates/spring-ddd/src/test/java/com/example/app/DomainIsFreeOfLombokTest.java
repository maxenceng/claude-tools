package com.example.app;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;

class DomainIsFreeOfLombokTest {

	private static final Path SOURCE_ROOT = Path.of("src/main/java");

	private static final Pattern LOMBOK_REFERENCE = Pattern.compile("\\blombok\\b");

	private static final List<Path> DOMAIN_SOURCES;

	static {
		try (Stream<Path> tree = Files.walk(SOURCE_ROOT)) {
			DOMAIN_SOURCES = tree.filter(Files::isRegularFile)
					.filter(source -> source.getFileName().toString().endsWith(".java"))
					.filter(source -> source.getParent().endsWith("domain"))
					.toList();
		} catch (IOException e) {
			throw new UncheckedIOException(e);
		}
	}

	@Test
	void shouldFindEveryDomainPackage() {
		assertThat(DOMAIN_SOURCES).isNotEmpty();
	}

	@Test
	void shouldKeepLombokOutOfEveryDomainPackage() throws IOException {
		List<String> references = new ArrayList<>();

		for (Path source : DOMAIN_SOURCES) {
			List<String> lines = Files.readAllLines(source);

			for (int line = 0; line < lines.size(); line++) {
				if (LOMBOK_REFERENCE.matcher(lines.get(line)).find()) {
					references.add("%s:%d %s".formatted(source, line + 1, lines.get(line).strip()));
				}
			}
		}

		assertThat(references)
				.as("a domain type is written out rather than generated, and ArchUnit cannot see this "
						+ "because Lombok's annotations do not survive into bytecode - ADR 0005")
				.isEmpty();
	}
}
