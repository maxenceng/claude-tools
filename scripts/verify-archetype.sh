#!/usr/bin/env bash
# Prove that a project generated from the archetype actually builds.
#
# This is the check that matters. The template building tells you the source is fine; it
# says nothing about whether the archetype descriptor still copies every file, filters the
# right ones, or restores the executable bit. Those break silently and you find out when
# starting a new project, which is the worst moment to be debugging scaffolding.
#
# CI runs exactly this. Run it locally before pushing anything under templates/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

GROUP_ID="com.acme"
ARTIFACT_ID="billing"
PACKAGE="com.acme.billing"

step() { printf '\n=== %s\n' "$1"; }

step "Regenerate the archetype from the template"
"$ROOT/scripts/build-archetype.sh"

step "Install the archetype"
# clean, not just install: maven-resources-plugin copies resources into target/ but never
# removes ones deleted from source, so a stale target/ can keep a file in the jar that is
# no longer in the archetype. That masks exactly the regressions the guards below check.
mvn -B -q -f "$ROOT/templates/spring-ddd-archetype/pom.xml" clean install

step "Generate a project"
cd "$WORK"
mvn -B -q archetype:generate \
	-DarchetypeGroupId=dev.maxenceng \
	-DarchetypeArtifactId=spring-ddd-archetype \
	-DarchetypeVersion=1.0.0-SNAPSHOT \
	-DgroupId="$GROUP_ID" \
	-DartifactId="$ARTIFACT_ID" \
	-Dversion=0.1.0-SNAPSHOT \
	-Dpackage="$PACKAGE" \
	-DinteractiveMode=false

cd "$WORK/$ARTIFACT_ID"

step "Check what the archetype format cannot express"
# Each of these has been wrong at least once. A generated project that builds but has no
# .gitignore commits target/ on the first add, and one without +x on mvnw cannot run make
# at all.
[[ -f .gitignore ]] || { echo "FAIL: .gitignore missing — archetype dropped it again" >&2; exit 1; }
[[ -x mvnw ]]       || { echo "FAIL: mvnw is not executable — post-generate hook did not run" >&2; exit 1; }
[[ ! -e .claude/settings.local.json ]] || { echo "FAIL: machine-specific settings.local.json leaked into the template" >&2; exit 1; }
echo "ok: .gitignore, mvnw +x, no leaked local settings"

step "Check nothing kept the template's identity"
if grep -rn "com\.example\.app" . --exclude-dir=target --exclude-dir=node_modules; then
	echo "FAIL: generated project still references the template package" >&2
	exit 1
fi
grep -qx "# $ARTIFACT_ID" README.md  || { echo "FAIL: README title not substituted" >&2; exit 1; }
grep -qx "# $ARTIFACT_ID" CLAUDE.md  || { echo "FAIL: CLAUDE.md title not substituted" >&2; exit 1; }
grep -q "packages = \"$PACKAGE\""  src/test/java/${PACKAGE//.//}/ArchitectureTest.java \
	|| { echo "FAIL: ArchitectureTest does not scan the generated package" >&2; exit 1; }
echo "ok: package, titles and scanned package all substituted"

step "Build the generated project"
make ci

step "Build the generated frontend"
(cd frontend && npm ci --no-audit --no-fund >/dev/null)
make fe-check

step "Generate again through the convenience wrapper"
# new-ddd-project.sh is what a human actually types. It duplicates the coordinates above,
# so without exercising it here it can drift from the archetype and nobody would notice
# until someone tried to start a project.
WRAPPER_DIR="$WORK/wrapper"
mkdir -p "$WRAPPER_DIR"
cd "$WRAPPER_DIR"
"$ROOT/scripts/new-ddd-project.sh" com.acme orders >/dev/null
[[ -f orders/pom.xml ]] || { echo "FAIL: wrapper produced no project" >&2; exit 1; }
grep -q "<artifactId>orders</artifactId>" orders/pom.xml || { echo "FAIL: wrapper produced wrong coordinates" >&2; exit 1; }
[[ -d orders/src/main/java/com/acme/orders ]] || { echo "FAIL: wrapper defaulted the package wrongly" >&2; exit 1; }
echo "ok: wrapper generates a project with the expected coordinates and package"

printf '\n=== generated project builds clean\n'
