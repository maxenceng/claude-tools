#!/usr/bin/env python3
"""Fail when the last test run skipped anything.

Testcontainers tests carry `disabledWithoutDocker = true`, so with the daemon down they
skip and the run still reports BUILD SUCCESS. A green run then says nothing about the
paths only a real database reaches, which is where the defects that survive unit tests
live. Wired into `verify` rather than `ci`, so a contributor without Docker can still
run the unit suite.

Read with a regex rather than an XML parser: the input is our own build output, and the
attributes wanted sit on one known element, so a parser would add a dependency and an
entity-expansion surface for nothing.
"""
import glob
import re
import sys

REPORTS = "target/surefire-reports/*.xml"

SUITE = re.compile(
    r"<testsuite\b[^>]*\bname=\"(?P<name>[^\"]*)\"[^>]*", re.DOTALL)
ATTR = r'\b{}="(\d+)"'


def main():
    reports = glob.glob(REPORTS)
    if not reports:
        print(f"no surefire reports under {REPORTS} — run the tests first")
        return 1

    skipped = []
    for report in reports:
        with open(report, encoding="utf-8", errors="replace") as handle:
            head = handle.read(4096)

        suite = SUITE.search(head)
        if not suite:
            continue

        counts = {}
        for attribute in ("skipped", "tests"):
            found = re.search(ATTR.format(attribute), suite.group(0))
            counts[attribute] = int(found.group(1)) if found else 0

        if counts["skipped"]:
            skipped.append((suite.group("name"), counts["skipped"], counts["tests"]))

    if not skipped:
        return 0

    total = sum(count for _, count, _ in skipped)
    print(f"{total} test(s) skipped — the suite did not prove what it looks like it proved:")
    for name, count, tests in sorted(skipped):
        print(f"  {name}: {count} of {tests}")
    print("\nIf these are Testcontainers tests, Docker is not running. Start it and run again.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
