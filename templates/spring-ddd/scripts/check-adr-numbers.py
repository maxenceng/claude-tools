#!/usr/bin/env python3
"""Fail on a duplicate or missing ADR number.

Numbering by hand collides whenever `main` moves during a ticket: two branches each pick
the next free number, both are right when written, and only one can be right on merge.
Nothing says so until a human notices, because two files with the same number are two
valid files.
"""
import glob
import os
import re
import sys

ADRS = "docs/adr/*.md"

NUMBERED = re.compile(r"^(\d{4})-[a-z0-9-]+\.md$")


def main():
    numbers = {}
    unnumbered = []

    for path in sorted(glob.glob(ADRS)):
        name = os.path.basename(path)
        match = NUMBERED.match(name)
        if not match:
            unnumbered.append(name)
            continue
        numbers.setdefault(int(match.group(1)), []).append(name)

    problems = []

    for name in unnumbered:
        problems.append(f"{name} is not named NNNN-kebab-case-title.md")

    for number, names in sorted(numbers.items()):
        if len(names) > 1:
            problems.append(f"{number:04d} used {len(names)} times: {', '.join(sorted(names))}")

    if numbers:
        expected = set(range(1, max(numbers) + 1))
        for missing in sorted(expected - set(numbers)):
            problems.append(f"{missing:04d} is missing — numbers are a sequence, not an id space")

    if not problems:
        return 0

    print("ADR numbering is wrong:")
    for problem in problems:
        print(f"  {problem}")
    if numbers:
        print(f"\nNext free number is {max(numbers) + 1:04d}.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
