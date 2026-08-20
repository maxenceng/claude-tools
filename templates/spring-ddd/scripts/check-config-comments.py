#!/usr/bin/env python3
"""Fail when a comment in a config file runs past one wrapped sentence.

Config files describe decisions, not tooling. A note saying why this project chose
something is worth the line; a paragraph explaining what a dependency contains or how
Docker works is what this catches, because that one comes back every few PRs.
"""
import glob
import io
import os
import re
import sys

MAX_LINES = 2

TARGETS = [
    "pom.xml",
    "Makefile",
    "frontend/Makefile",
    "src/main/resources/application.properties",
]
TARGETS += sorted(glob.glob(".github/workflows/*.yml"))
TARGETS += sorted(glob.glob("src/main/resources/db/changelog/**/*.yaml", recursive=True))


def blocks(path, lines):
    xml = path.endswith(".xml")
    block, open_xml = [], False
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if xml:
            if stripped.startswith("<!--"):
                open_xml = "-->" not in stripped
                block.append(number)
                if not open_xml:
                    yield block
                    block = []
                continue
            if open_xml:
                block.append(number)
                if "-->" in stripped:
                    open_xml = False
                    yield block
                    block = []
                continue
        elif stripped.startswith("#") and not stripped.startswith("#!"):
            block.append(number)
            continue
        if block:
            yield block
            block = []
    if block:
        yield block


def main():
    failures = []
    for path in TARGETS:
        if not os.path.exists(path):
            continue
        lines = io.open(path, encoding="utf-8").read().split("\n")
        for block in blocks(path, lines):
            if len(block) > MAX_LINES:
                failures.append((path, block[0], len(block), lines[block[0] - 1].strip()[:60]))
    for path, start, size, preview in failures:
        print("%s:%d: comment runs %d lines, limit is %d -- %s" % (path, start, size, MAX_LINES, preview))
    if failures:
        print("\n%d comment(s) over the limit. Say why the choice was made, not what the tool does." % len(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
