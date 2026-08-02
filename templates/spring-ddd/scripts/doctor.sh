#!/usr/bin/env bash
# Reports toolchain and project-setup problems as actionable instructions rather than as
# build failures. Nothing here fails a fresh project — a scaffold that greets you with a
# red build gets deleted rather than fixed.
set -uo pipefail

status=0

report() { printf '  %-8s %s\n' "$1" "$2"; }

echo "Toolchain"

# Same search order as the Makefile: an already-correct JAVA_HOME, then ~/.jdks, then
# the system path, then whatever is on PATH.
javac_bin=""
if [[ -n "${JAVA_HOME:-}" && -x "${JAVA_HOME}/bin/javac" ]]; then
	javac_bin="${JAVA_HOME}/bin/javac"
else
	for candidate in "${HOME}"/.jdks/jdk-25* /usr/lib/jvm/*25*; do
		if [[ -x "${candidate}/bin/javac" ]]; then
			javac_bin="${candidate}/bin/javac"
			break
		fi
	done
fi
if [[ -z "${javac_bin}" ]] && command -v javac >/dev/null 2>&1; then
	javac_bin="$(command -v javac)"
fi

install_hint="install a JDK 25 into ~/.jdks (Adoptium Temurin) or run: sudo apt install -y openjdk-25-jdk"

if [[ -z "${javac_bin}" ]]; then
	report "javac" "MISSING — ${install_hint}"
	status=1
else
	javac_version="$("${javac_bin}" -version 2>&1 | awk '{print $2}')"
	if [[ "${javac_version}" == 25.* ]]; then
		report "javac" "${javac_version} (${javac_bin})"
	else
		report "javac" "${javac_version} — need 25. ${install_hint}"
		status=1
	fi
fi

report "JAVA_HOME" "${JAVA_HOME:-<unset, falling back to PATH>}"

if command -v node >/dev/null 2>&1; then
	node_version="$(node --version)"
	if [[ "${node_version}" == v24.* ]]; then
		report "node" "${node_version}"
	else
		report "node" "${node_version} — frontend expects 24. Run: nvm use"
	fi
else
	report "node" "not on PATH"
fi

for tool in docker gh; do
	if command -v "${tool}" >/dev/null 2>&1; then
		report "${tool}" "$("${tool}" --version 2>&1 | head -1)"
	else
		report "${tool}" "not installed"
	fi
done

echo
echo "Project"

# The brief in CLAUDE.md is the only thing telling an agent what it is building. Left
# unwritten it is worse than absent: four paragraphs of prompts are read on every request
# and say nothing. Deliberately a warning — a fresh project is meant to pass everything.
if [[ -f CLAUDE.md ]] && grep -q "REPLACE-ME" CLAUDE.md; then
	report "brief" "CLAUDE.md still has the placeholder — agents know how to build this, not what it is"
else
	report "brief" "written"
fi

exit "${status}"
