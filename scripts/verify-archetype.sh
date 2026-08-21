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
[[ -f frontend/.gitignore ]] || { echo "FAIL: frontend/.gitignore missing — the first 'git add -A' commits node_modules/" >&2; exit 1; }
[[ -x mvnw ]]       || { echo "FAIL: mvnw is not executable — post-generate hook did not run" >&2; exit 1; }
[[ ! -e .claude/settings.local.json ]] || { echo "FAIL: machine-specific settings.local.json leaked into the template" >&2; exit 1; }
[[ ! -e HELP.md ]] || { echo "FAIL: HELP.md is git-ignored in the template but shipped anyway" >&2; exit 1; }
echo "ok: both .gitignore files, mvnw +x, no git-ignored file leaked"

step "Check Velocity filtering did not eat the markdown"
# "##" opens a comment in Velocity, so every heading below H1 was being deleted during
# generation — the ticket template arrived with no sections at all. A build cannot see
# this; only someone opening the file can, which is why it survived so long.
while IFS= read -r f; do
	want=$(grep -c '^#\{1,6\} ' "$ROOT/templates/spring-ddd/$f" || true)
	got=$(grep -c '^#\{1,6\} ' "$f" || true)
	[[ "$want" == "$got" ]] || { echo "FAIL: $f kept $got of the template's $want headings" >&2; exit 1; }
done < <(cd "$ROOT/templates/spring-ddd" && git ls-files '*.md')
echo "ok: every markdown file kept all of its headings"

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

step "Check the project brief survives generation and is detectable"
# The brief is the only thing in a generated project that says what is being built. The
# marker and the check that reads it live in different files, so assert them end to end
# rather than assuming they still agree.
grep -q "^## What this is" CLAUDE.md || { echo "FAIL: generated CLAUDE.md has no brief section" >&2; exit 1; }
grep -q "REPLACE-ME" CLAUDE.md       || { echo "FAIL: brief placeholder marker missing, so doctor cannot detect an unwritten brief" >&2; exit 1; }
doctor_output="$(./scripts/doctor.sh || true)"
grep -q "still has the placeholder" <<<"$doctor_output" \
	|| { echo "FAIL: doctor does not flag the unwritten brief" >&2; exit 1; }
echo "ok: brief ships with prompts, and doctor reports it as unwritten"

step "Run the generated project's own pipeline"
# `make verify` rather than `make ci`: verify is defined to run exactly what the template's
# workflow runs, so this proves a generated project passes the pipeline it ships with --
# including the schema capture, which boots the application and which nothing else
# exercises inside a *generated* project.
(cd frontend && npm ci --no-audit --no-fund >/dev/null)
make verify

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
