#!/usr/bin/env python3
"""Fail on a duplicate or missing ADR number, or an ADR index that is not current.

Numbering by hand collides whenever `main` moves during a ticket: two branches each pick
the next free number, both are right when written, and only one can be right on merge.
Nothing says so until a human notices, because two files with the same number are two
valid files.

The index, docs/adr/README.md, is compared with what write-adr-index.py would write and
never edited here: a check that repairs what it checks hides the branch that forgot.
"""
import os
import sys

import adr_folder


def shown(lines, number):
    """Line `number` as written, with a missing final newline said rather than invisible."""
    if number > len(lines):
        return "(end of file)"
    line = lines[number - 1]
    return line[:-1] if line.endswith("\n") else f"{line} (no newline at end of file)"


def stale_index(numbered):
    expected, problems = adr_folder.index(numbered)
    if problems:
        return problems
    index = adr_folder.relative(adr_folder.INDEX)
    if not os.path.isfile(adr_folder.INDEX):
        return [f"{index} is missing; run make adr-index"]
    with open(adr_folder.INDEX, encoding="utf-8") as handle:
        actual = handle.read()
    if actual == expected:
        return []
    wanted = expected.splitlines(keepends=True)
    found = actual.splitlines(keepends=True)
    line = next(
        (number for number, pair in enumerate(zip(wanted, found), start=1) if pair[0] != pair[1]),
        min(len(wanted), len(found)) + 1,
    )
    return [
        f"{index} is stale at line {line}; run make adr-index",
        f"    expected: {shown(wanted, line)}",
        f"    found:    {shown(found, line)}",
    ]


def main():
    if not os.path.isdir(adr_folder.ADR_DIR):
        print(f"no ADR directory at {adr_folder.relative(adr_folder.ADR_DIR)}")
        return 1

    numbers, unnumbered = adr_folder.files()

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

    problems.extend(stale_index(numbers))

    if not problems:
        return 0

    print("The ADR folder is wrong:")
    for problem in problems:
        print(f"  {problem}")
    if numbers:
        print(f"\nNext free number is {max(numbers) + 1:04d}.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
