#!/usr/bin/env python3
"""Fail if guard-fixtures.py stops detecting a fixture that proves nothing.

guard-fixtures.py proves every scripts/check-*, and nothing proved it: a registry entry
whose needle was edited away, or a fixture that no longer trips its guard, would leave it
green while it proved nothing. Every branch below was checked by hand exactly once, which is
the standard this project already calls untested.

The registry is mutated in memory rather than on disk -- no file is backed up, broken and
restored, so an interrupted run cannot leave the tree in the state the last case built.
Named prove-* rather than check-*, so it is not itself a guard needing a fixture; that is
where the regress stops, and ADR 0015 says why.
"""
import contextlib
import importlib.util
import io
import os
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS = os.path.join(REPO_ROOT, "scripts", "guard-fixtures.py")


def load_harness():
    spec = importlib.util.spec_from_file_location("guard_fixtures", HARNESS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(module):
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        status = module.main()
    return status, captured.getvalue()


def expect_rejected(label, module, expected):
    status, output = run(module)
    if status == 0:
        return f"{label}: the harness accepted it (exit 0)\n--- output ---\n{output}"
    if expected not in output:
        return (
            f"{label}: the harness exited {status} but without {expected!r}\n"
            f"--- output ---\n{output}"
        )
    return None


def a_message_no_branch_prints(module):
    module.discovered_guards = lambda: ["check-adr-numbers.py"]
    module.REGISTRY = {
        "check-adr-numbers.py": module.FixtureTree("adr-numbers", "NO BRANCH PRINTS THIS")
    }


def a_fixture_that_does_not_trip(module, adr_dir):
    fixture = module.FixtureTree("adr-numbers", "0001 used 2 times")
    fixture.directory = adr_dir
    module.discovered_guards = lambda: ["check-adr-numbers.py"]
    module.REGISTRY = {"check-adr-numbers.py": fixture}


def a_guard_nobody_registered(module):
    module.discovered_guards = lambda: ["check-adr-numbers.py", "check-brand-new.py"]
    module.REGISTRY = {
        "check-adr-numbers.py": module.FixtureTree(
            "adr-numbers", "0001 used 2 times: 0001-first-decision.md, 0001-second-decision.md"
        )
    }


def a_registration_whose_guard_is_gone(module):
    module.discovered_guards = lambda: []
    module.REGISTRY = {"check-deleted.py": module.FixtureTree("adr-numbers", "anything")}


def a_proof_that_is_not_there(module):
    module.discovered_guards = lambda: ["check-openapi.sh"]
    module.REGISTRY = {
        "check-openapi.sh": module.ProvenByItsOwnBoot(
            "proven by its own boot", [("scripts/deleted-proof.sh", "anything")]
        )
    }


def a_proof_that_no_longer_says_what_it_proved(module):
    module.discovered_guards = lambda: ["check-openapi.sh"]
    module.REGISTRY = {
        "check-openapi.sh": module.ProvenByItsOwnBoot(
            "proven by its own boot", [("scripts/check-openapi.sh", "A LINE NOBODY WROTE")]
        )
    }


def main():
    problems = []

    status, output = run(load_harness())
    if status != 0:
        problems.append(f"the real registry does not pass, so nothing below means anything:\n{output}")

    with tempfile.TemporaryDirectory() as passing:
        os.makedirs(os.path.join(passing, "docs", "adr"))
        with open(os.path.join(passing, "docs", "adr", "0001-only.md"), "w", encoding="utf-8") as handle:
            handle.write("# 1. Only\n")

        cases = [
            ("a message no branch prints", a_message_no_branch_prints, (), "did not contain"),
            ("a fixture that does not trip its guard", a_fixture_that_does_not_trip, (passing,), "did not fail it (exit 0)"),
            ("a guard nobody registered", a_guard_nobody_registered, (), "has no fixture registered"),
            ("a registration whose guard is gone", a_registration_whose_guard_is_gone, (), "no longer has it"),
            ("a proof that is not there", a_proof_that_is_not_there, (), "is what proves it, and is not there"),
            ("a proof that no longer says what it proved", a_proof_that_no_longer_says_what_it_proved, (), "no longer contains"),
        ]

        for label, mutate, args, expected in cases:
            module = load_harness()
            mutate(module, *args)
            failure = expect_rejected(label, module, expected)
            if failure:
                problems.append(failure)

    if problems:
        print("the guard harness does not catch what it is meant to:")
        for problem in problems:
            print(f"  {problem}")
        return 1

    print(f"ok: the guard harness rejected all {len(cases)} fixtures that would prove nothing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
