#!/usr/bin/env bash
# Create a project from the spring-ddd archetype.
#
# Generation resolves the archetype from ~/.m2, so this works from any directory and does
# not need the claude-tools clone. Symlink it onto your PATH:
#
#   ln -s "$PWD/scripts/new-ddd-project.sh" ~/.local/bin/new-ddd-project
#
# Usage: new-ddd-project <groupId> <artifactId> [package]
#   new-ddd-project com.acme billing
#   new-ddd-project com.acme billing-service com.acme.billing
set -euo pipefail

ARCHETYPE_GROUP="dev.maxenceng"
ARCHETYPE_ARTIFACT="spring-ddd-archetype"
ARCHETYPE_VERSION="1.0.0-SNAPSHOT"

die() { echo "error: $*" >&2; exit 1; }

usage() {
	cat >&2 <<EOF
Usage: $(basename "$0") <groupId> <artifactId> [package]

  groupId     Maven group, e.g. com.acme
  artifactId  Project name, e.g. billing
  package     Java root package. Defaults to <groupId>.<artifactId> with hyphens removed,
              since hyphens are legal in an artifactId and not in a package name.
EOF
	exit 2
}

[[ $# -ge 2 && $# -le 3 ]] || usage

GROUP_ID="$1"
ARTIFACT_ID="$2"
PACKAGE="${3:-${GROUP_ID}.${ARTIFACT_ID//-/}}"
VERSION="0.1.0-SNAPSHOT"

[[ "$GROUP_ID"    =~ ^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)*$ ]] || die "groupId '$GROUP_ID' should look like com.acme"
[[ "$ARTIFACT_ID" =~ ^[a-z][a-z0-9-]*$ ]]                   || die "artifactId '$ARTIFACT_ID' should be lowercase, digits and hyphens"
[[ "$PACKAGE"     =~ ^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)*$ ]] || die "package '$PACKAGE' is not a valid Java package"

command -v mvn >/dev/null || die "mvn is not on PATH"

# Generating inside a Maven project succeeds but buries the new project in it, which is
# never what anyone wants.
[[ -f pom.xml ]] && die "refusing to generate inside a Maven project ($(pwd)/pom.xml exists). Run this from an empty or unrelated directory."

[[ -e "$ARTIFACT_ID" ]] && die "'$ARTIFACT_ID' already exists here"

INSTALLED=~/.m2/repository/${ARCHETYPE_GROUP//.//}/${ARCHETYPE_ARTIFACT}/${ARCHETYPE_VERSION}
if [[ ! -d "$INSTALLED" ]]; then
	die "archetype not installed. From a claude-tools clone:
    ./scripts/build-archetype.sh
    mvn -f templates/spring-ddd-archetype/pom.xml clean install"
fi

echo "generating $ARTIFACT_ID (package $PACKAGE)"
mvn -B -q archetype:generate \
	-DarchetypeGroupId="$ARCHETYPE_GROUP" \
	-DarchetypeArtifactId="$ARCHETYPE_ARTIFACT" \
	-DarchetypeVersion="$ARCHETYPE_VERSION" \
	-DgroupId="$GROUP_ID" \
	-DartifactId="$ARTIFACT_ID" \
	-Dversion="$VERSION" \
	-Dpackage="$PACKAGE" \
	-DinteractiveMode=false

[[ -f "$ARTIFACT_ID/pom.xml" ]] || die "generation reported success but produced no project"

cat <<EOF

created ./$ARTIFACT_ID

next:
  cd $ARTIFACT_ID
  git init
  make doctor      # toolchain
  make ci          # lint, tests, duplication
  make fe-check    # frontend typecheck and tests

All three pass on a fresh project. Once you add the first bounded context, delete
src/test/resources/archunit.properties so the architecture rules go back to strict.
EOF
