#!/usr/bin/env python3
"""Fail when code or a living document names a GitHub issue.

A ticket is an issue, and the pull request that merges it closes it. A reference to `#42` in
`src/` is green on the branch and a claim about the past the day it merges, and whether it is
open or closed is a question only GitHub can answer. So no issue is named here at all, with no
lookup: this check never calls GitHub, and `make verify` needs no network. ADR 0018.

docs/adr/, docs/research/, docs/endpoints/ and scripts/ are exempt. An ADR is a dated record of
what was decided, a research note says for which issue it was researched, an endpoint's
`tickets:` lists the issues that shaped it, and a check script's docstring names the incident
that made the rule -- all of them are meant to read as history.

An issue URL fails in any text file. A bare `#n` fails only in Java and Markdown: in a stylesheet
or a frontend source it is a colour, and in a workflow, a Makefile or a script it is a comment.
"""
import io
import os
import re
import sys

# CHECK_ROOT is how guard-fixtures.py points this at a fixture tree; nothing else sets it.
ROOT = os.environ.get("CHECK_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ISSUE_URL = re.compile(r"https?://github\.com/[^/\s]+/[^/\s]+/issues/[0-9]+")
BARE_NUMBER = re.compile(r"(?<![\w/&#-])#[0-9]+(?![\w-])")
EXEMPT = ("docs/adr/", "docs/research/", "docs/endpoints/", "scripts/")
SKIPPED_DIRECTORIES = {"node_modules", "target", "dist", "site", ".cache", ".git", ".mvn", ".idea"}
CHECKED_FOR_BARE_NUMBERS = (".java", ".md")


def scanned():
    for directory, directories, files in os.walk(ROOT):
        directories[:] = sorted(d for d in directories if d not in SKIPPED_DIRECTORIES)
        for name in sorted(files):
            relative = os.path.relpath(os.path.join(directory, name), ROOT).replace(os.sep, "/")
            if not relative.startswith(EXEMPT):
                yield relative


def named(relative, line):
    found = ISSUE_URL.findall(line)
    if relative.endswith(CHECKED_FOR_BARE_NUMBERS):
        found += BARE_NUMBER.findall(line)
    return found


def main():
    paths = list(scanned())
    if not paths:
        print("nothing was scanned -- the walk matches no file")
        return 1

    failures = []
    for relative in paths:
        try:
            with io.open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
                lines = handle.readlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, start=1):
            for reference in named(relative, line):
                failures.append((relative, number, reference, line.strip()))

    for relative, number, reference, line in failures:
        print("%s:%d: names %s, an issue outside the record" % (relative, number, reference))
        print("    %s" % line)

    if failures:
        print(
            "\n%d reference(s) to an issue outside the record. Name the behaviour, not the issue"
            " that added it -- git and docs/adr/ are what remember which one did." % len(failures)
        )
        return 1

    print("ok: %d file(s) name no issue" % len(paths))
    return 0


if __name__ == "__main__":
    sys.exit(main())
