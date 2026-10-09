#!/usr/bin/env python3
"""Fail if a scripts/check-* guard has no fixture proven to trip it.

A guard is written against the failure it exists for, watched to fail once, and then
never made to fail again. A glob that stops matching, a branch that stops being reached or
a message that drifts all leave it green while it checks nothing -- ADR 0015.

This is a check on the checks: it globs scripts/check-*, and for each one either runs it
against the fixture tree registered for it below and asserts the exit code *and* message of
the branch it targets, or -- for a guard whose failure case is a running application --
checks that what proves it is still in the tree. A `scripts/check-*` with neither is the
defect this file exists to catch.

A guard runs with its working directory *and* CHECK_ROOT set to the fixture tree: some
glob from the working directory, the rest anchor to the repo through CHECK_ROOT's default.
"""
import glob
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(REPO_ROOT, "scripts", "fixtures")


def surefire_report_with_a_skip(fixture_dir):
    reports = os.path.join(fixture_dir, "target", "surefire-reports")
    os.makedirs(reports, exist_ok=True)
    with open(os.path.join(reports, "TEST-com.example.FixtureTest.xml"), "w", encoding="utf-8") as handle:
        handle.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<testsuite name="com.example.FixtureTest" tests="3" skipped="1" '
            'failures="0" errors="0" time="0.010">\n'
            "</testsuite>\n"
        )


class FixtureTree:
    def __init__(self, directory, message, synthesize=None):
        self.directory = os.path.join(FIXTURES, directory)
        self.message = message
        self.synthesize = synthesize


class ProvenByItsOwnBoot:
    """A guard whose failure case is a running application, so no fixture directory trips it.

    What proves it is named here and checked to still be there. A stored sentence nothing
    reads is the hand-kept list this file exists to remove, one level up.
    """

    def __init__(self, reason, requires):
        self.reason = reason
        self.requires = requires


REGISTRY = {
    "check-adr-numbers.py": FixtureTree(
        "adr-numbers",
        "0001 used 2 times: 0001-first-decision.md, 0001-second-decision.md",
    ),
    "check-config-comments.py": FixtureTree(
        "config-comments",
        "Makefile:1: comment runs 3 lines, limit is 2",
    ),
    "check-no-skipped-tests.py": FixtureTree(
        "no-skipped-tests",
        "1 test(s) skipped",
        synthesize=surefire_report_with_a_skip,
    ),
    "check-round-trip-tests.py": FixtureTree(
        "round-trip-tests",
        "reads back a write without entityManager.clear()",
    ),
    "check-test-comments.py": FixtureTree(
        "test-comments",
        "ThingTest.java:7: comment in a test",
    ),
    "check-ticket-references.py": FixtureTree(
        "ticket-references",
        "reference(s) to a landed ticket",
    ),
    "check-openapi.sh": ProvenByItsOwnBoot(
        "compares a mutated copy of the committed schema inside the boot it already does -- see ADR 0015",
        [
            ("scripts/check-openapi.sh", "schema_matches"),
            ("scripts/check-openapi.sh", "ok: the drift check detects a mutated schema"),
        ],
    ),
}


def discovered_guards():
    return sorted(
        os.path.basename(path)
        for path in glob.glob(os.path.join(REPO_ROOT, "scripts", "check-*"))
        if os.path.isfile(path)
    )


def missing_proof(name, case):
    problems = []
    for relative_path, needle in case.requires:
        path = os.path.join(REPO_ROOT, relative_path)
        if not os.path.isfile(path):
            problems.append(f"{name}: {relative_path} is what proves it, and is not there")
        elif needle not in open(path, encoding="utf-8").read():
            problems.append(
                f"{name}: {relative_path} no longer contains {needle!r}, which is what proved it"
            )
    return problems


def run_fixture(name, fixture):
    if fixture.synthesize:
        fixture.synthesize(fixture.directory)

    result = subprocess.run(
        ["python3", os.path.join(REPO_ROOT, "scripts", name)],
        cwd=fixture.directory,
        env={**os.environ, "CHECK_ROOT": fixture.directory},
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    if result.returncode == 0:
        return f"{name}: its fixture at {fixture.directory} did not fail it (exit 0)"
    if fixture.message not in output:
        return (
            f"{name}: its fixture exited {result.returncode} but the output did not contain "
            f"{fixture.message!r} -- it may have tripped a different branch than the one "
            f"registered\n--- actual output ---\n{output}"
        )
    return None


def main():
    guards = discovered_guards()
    problems = []

    for name in guards:
        case = REGISTRY.get(name)
        if case is None:
            problems.append(f"{name} has no fixture registered in scripts/guard-fixtures.py")
        elif isinstance(case, FixtureTree):
            failure = run_fixture(name, case)
            if failure:
                problems.append(failure)
        else:
            problems.extend(missing_proof(name, case))

    for name in REGISTRY:
        if name not in guards:
            problems.append(f"{name} is registered in scripts/guard-fixtures.py but scripts/check-* no longer has it")

    if problems:
        print("guard fixtures are wrong:")
        for problem in problems:
            print(f"  {problem}")
        return 1

    fixtures = sum(1 for case in REGISTRY.values() if isinstance(case, FixtureTree))
    boots = sum(1 for case in REGISTRY.values() if isinstance(case, ProvenByItsOwnBoot))
    print(f"ok: {fixtures} guard(s) tripped by their fixture, {boots} proven by their own boot")
    return 0


if __name__ == "__main__":
    sys.exit(main())
