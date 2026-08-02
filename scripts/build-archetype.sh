#!/usr/bin/env bash
# Derive the Maven archetype from templates/spring-ddd.
#
# The template stays the readable, buildable source; the archetype is generated from it.
# One source of truth, so the two cannot drift — regenerate rather than hand-editing
# anything under templates/spring-ddd-archetype/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/templates/spring-ddd"
OUT="$ROOT/templates/spring-ddd-archetype"
RES="$OUT/src/main/resources/archetype-resources"

[[ -d "$SRC" ]] || { echo "missing source template: $SRC" >&2; exit 1; }

rm -rf "$OUT"
mkdir -p "$RES" "$OUT/src/main/resources/META-INF/maven"

python3 - "$SRC" "$RES" <<'PY'
import os, re, shutil, subprocess, sys

src, res = sys.argv[1], sys.argv[2]
SKIP_DIRS = {"target", "node_modules", "dist", ".git", ".idea"}
PKG = "com.example.app"
PKG_PATH = os.path.join("com", "example", "app")

# Anything git ignores is a local leftover, not part of the template. Shipping one has
# happened before — a .claude/settings.local.json full of absolute home paths reached
# every generated project — and it is invisible in CI, because a fresh clone does not
# have the file at all and the archetype simply comes out different there.
try:
    ignored = set(subprocess.run(
        ["git", "-C", src, "ls-files", "--others", "--ignored", "--exclude-standard"],
        capture_output=True, text=True, check=True).stdout.split())
except (OSError, subprocess.CalledProcessError):
    ignored = set()

def is_filtered(rel):
    """Mirror of the filtered fileSets in archetype-metadata.xml below.

    These two lists have to agree. Escaping a file the archetype does not filter ships
    the escape markers themselves into the generated project — frontend/CLAUDE.md is
    markdown but unfiltered, and got exactly that treatment on the first attempt.

    pom.xml is deliberately absent: Maven filters it implicitly, it needs ${groupId} and
    ${version} resolved as well, and it contains no '#' to protect.
    """
    rel = rel.replace(os.sep, "/")
    if rel.endswith(".java") and rel.startswith(("src/main/java/", "src/test/java/")):
        return True
    if rel.startswith(("src/main/resources/", "docs/")):
        return True
    return rel in ("CLAUDE.md", "README.md")


TOKEN = re.compile(r"(\$\{(?:package|artifactId)\})")


def velocity_safe(text):
    """Wrap everything that is not a substitution token in a Velocity literal block.

    Archetype resources are Velocity templates, and Velocity reads "##" as a line
    comment. Every markdown heading below H1 was therefore being deleted during
    generation: the ticket template arrived with no sections, CLAUDE.md with no rules.
    Escaping the whole file except the tokens removes the class rather than the symptom.
    """
    if "]]#" in text:
        raise SystemExit("cannot escape for Velocity, content contains ']]#'")
    return "".join(part if TOKEN.fullmatch(part) else "#[[" + part + "]]#"
                   for part in TOKEN.split(text) if part)


to_escape = []

for dirpath, dirnames, filenames in os.walk(src):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for name in filenames:
        abs_src = os.path.join(dirpath, name)
        rel = os.path.relpath(abs_src, src)

        if rel.replace(os.sep, "/") in ignored:
            continue

        # Java sources move out of com/example/app/ — the archetype puts them back
        # under whatever package the user chooses.
        is_java = rel.endswith(".java")
        if is_java:
            rel = rel.replace(os.path.join("java", PKG_PATH), "java")

        # maven-archetype drops .gitignore when packaging the archetype jar, so each one
        # travels without the dot and is renamed by the post-generate script. The
        # frontend has its own; without it a generated project commits node_modules/.
        if name == ".gitignore":
            rel = os.path.join(os.path.dirname(rel), "gitignore")

        abs_dst = os.path.join(res, rel)
        os.makedirs(os.path.dirname(abs_dst), exist_ok=True)

        if is_filtered(rel):
            text = open(abs_src, encoding="utf-8").read()
            text = text.replace(PKG, "${package}")
            # The template is readable as a project called "app". Only the H1 carries
            # that name — replacing "app" everywhere would also hit "application".
            text = re.sub(r"^# app$", "# ${artifactId}", text, count=1, flags=re.M)
            open(abs_dst, "w", encoding="utf-8").write(text)
            to_escape.append(abs_dst)
        else:
            shutil.copy2(abs_src, abs_dst)

# The generated project's identity comes from the archetype properties.
pom = os.path.join(res, "pom.xml")
text = open(pom, encoding="utf-8").read()
text = text.replace("<groupId>com.example</groupId>\n\t<artifactId>app</artifactId>\n\t<version>0.0.1-SNAPSHOT</version>\n\t<name>app</name>",
                    "<groupId>${groupId}</groupId>\n\t<artifactId>${artifactId}</artifactId>\n\t<version>${version}</version>\n\t<name>${artifactId}</name>")
open(pom, "w", encoding="utf-8").write(text)

props = os.path.join(res, "src/main/resources/application.properties")
text = open(props, encoding="utf-8").read()
text = re.sub(r"^spring\.application\.name=.*$", "spring.application.name=${artifactId}",
              text, count=1, flags=re.M)
open(props, "w", encoding="utf-8").write(text)

# Escaping runs last, after every rewrite above. Done inline it would have to reason
# about line anchors inside a literal block, and the properties rewrite would silently
# stop matching.
for path in to_escape:
    text = open(path, encoding="utf-8").read()
    open(path, "w", encoding="utf-8").write(velocity_safe(text))

print(f"archetype-resources built ({len(to_escape)} filtered files escaped)")
PY

cat > "$OUT/pom.xml" <<'XML'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
	<modelVersion>4.0.0</modelVersion>

	<groupId>dev.maxenceng</groupId>
	<artifactId>spring-ddd-archetype</artifactId>
	<version>1.0.0-SNAPSHOT</version>
	<packaging>maven-archetype</packaging>

	<name>spring-ddd-archetype</name>
	<description>Spring Boot 4 / Java 25, DDD bounded contexts, hexagonal layering, enforced architecture, typed React frontend</description>

	<!-- GENERATED by scripts/build-archetype.sh from templates/spring-ddd. Do not edit. -->

	<build>
		<extensions>
			<extension>
				<groupId>org.apache.maven.archetype</groupId>
				<artifactId>archetype-packaging</artifactId>
				<version>3.2.1</version>
			</extension>
		</extensions>
	</build>
</project>
XML

cat > "$OUT/src/main/resources/META-INF/maven/archetype-metadata.xml" <<'XML'
<?xml version="1.0" encoding="UTF-8"?>
<archetype-descriptor
	xmlns="https://maven.apache.org/plugins/maven-archetype-plugin/archetype-descriptor/1.1.0"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="https://maven.apache.org/plugins/maven-archetype-plugin/archetype-descriptor/1.1.0 https://maven.apache.org/xsd/archetype-descriptor-1.1.0.xsd"
	name="spring-ddd">

	<fileSets>
		<!-- Java sources: packaged, so they land under the chosen package. -->
		<fileSet filtered="true" packaged="true" encoding="UTF-8">
			<directory>src/main/java</directory>
			<includes><include>**/*.java</include></includes>
		</fileSet>
		<fileSet filtered="true" packaged="true" encoding="UTF-8">
			<directory>src/test/java</directory>
			<includes><include>**/*.java</include></includes>
		</fileSet>

		<!-- Filtered: these name the package or the artifact. -->
		<fileSet filtered="true" encoding="UTF-8">
			<directory>src/main/resources</directory>
			<includes><include>**/*</include></includes>
		</fileSet>
		<fileSet filtered="true" encoding="UTF-8">
			<directory>docs</directory>
			<includes><include>**/*</include></includes>
		</fileSet>
		<fileSet filtered="true" encoding="UTF-8">
			<directory></directory>
			<includes>
				<include>CLAUDE.md</include>
				<include>README.md</include>
			</includes>
		</fileSet>

		<!-- Unfiltered: shell, YAML and Make all use ${...} and $(...) for their own
		     purposes, and Velocity would eat them. -->
		<fileSet encoding="UTF-8">
			<directory></directory>
			<includes>
				<include>Makefile</include>
				<include>mvnw</include>
				<include>mvnw.cmd</include>
				<include>gitignore</include>
				<include>.gitattributes</include>
			</includes>
		</fileSet>
		<fileSet encoding="UTF-8">
			<directory>.mvn</directory>
			<includes><include>**/*</include></includes>
		</fileSet>
		<fileSet encoding="UTF-8">
			<directory>.github</directory>
			<includes><include>**/*</include></includes>
		</fileSet>
		<fileSet encoding="UTF-8">
			<directory>.claude</directory>
			<includes><include>**/*</include></includes>
		</fileSet>
		<fileSet encoding="UTF-8">
			<directory>scripts</directory>
			<includes><include>**/*</include></includes>
		</fileSet>
		<fileSet encoding="UTF-8">
			<directory>src/test/resources</directory>
			<includes><include>**/*</include></includes>
		</fileSet>
		<fileSet encoding="UTF-8">
			<directory>frontend</directory>
			<includes><include>**/*</include></includes>
			<excludes>
				<exclude>node_modules/**</exclude>
				<exclude>dist/**</exclude>
			</excludes>
		</fileSet>
	</fileSets>
</archetype-descriptor>
XML

cat > "$OUT/src/main/resources/META-INF/archetype-post-generate.groovy" <<'GROOVY'
// Runs after generation, and fixes two things the archetype format cannot express.
import java.nio.file.Files
import java.nio.file.attribute.PosixFilePermission

def projectDir = new File(request.outputDirectory, request.artifactId)

// 1. maven-archetype refuses to package a file named .gitignore, so each one travels as
//    "gitignore". There is one at the root and one in frontend/; without the second, the
//    first `git add -A` commits the whole of node_modules/.
def shipped = []
projectDir.eachFileRecurse { f ->
    if (f.isFile() && f.name == "gitignore") {
        shipped << f
    }
}
shipped.each { f ->
    f.renameTo(new File(f.parentFile, ".gitignore"))
}

// 2. Archetypes do not carry the executable bit. The Makefile calls ./mvnw, so
//    without this every make target fails with "permission denied" on a fresh project.
["mvnw", "scripts/doctor.sh", "scripts/guard-generated.sh", "scripts/check-openapi.sh"].each { name ->
    def f = new File(projectDir, name)
    if (f.exists()) {
        def perms = Files.getPosixFilePermissions(f.toPath())
        perms << PosixFilePermission.OWNER_EXECUTE
        perms << PosixFilePermission.GROUP_EXECUTE
        perms << PosixFilePermission.OTHERS_EXECUTE
        Files.setPosixFilePermissions(f.toPath(), perms)
    }
}
GROOVY

echo "archetype written to $OUT"
