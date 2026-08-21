#!/usr/bin/env python3
"""Fail on a comment anywhere under src/test/java.

A test name is the explanation. A comment beside it is a second description of the
behaviour that nothing keeps in step -- no compiler checks it, no assertion fails when it
goes stale -- so it rots while the test stays green and misleads the next reader with the
half that still looks authoritative.

Architecture rule holders are exempt, and only they. Their rules are declarative fields
rather than named test methods, so there is no name for the reasoning to live in - ADR
0007.

Neither ArchUnit nor the compiler can see this: comments do not survive into bytecode,
which is the same reason DomainIsFreeOfLombokTest reads source (ADR 0005).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE_ROOT = os.path.join(ROOT, "src", "test", "java")

# A file whose job is to *be* the architecture description. ArchUnit rule holders carry
# @AnalyzeClasses; the Spring Modulith one builds ApplicationModules.
RULE_HOLDER_MARKERS = ("@AnalyzeClasses", "ApplicationModules")


def comment_lines(text):
    """Line numbers of every comment, ignoring anything inside a literal.

    A '//' inside a string or a text block is not a comment, and flagging one would make
    this rule cry wolf -- which is how a guard stops being read.
    """
    hits = []
    in_block_comment = False
    in_text_block = False

    for number, line in enumerate(text.split("\n"), 1):
        index = 0
        while index < len(line):
            rest = line[index:]

            if in_block_comment:
                end = rest.find("*/")
                if end == -1:
                    break
                in_block_comment = False
                index += end + 2
            elif in_text_block:
                end = rest.find('"""')
                if end == -1:
                    break
                in_text_block = False
                index += end + 3
            elif rest.startswith('"""'):
                in_text_block = True
                index += 3
            elif rest[0] in "\"'":
                quote, offset = rest[0], 1
                while offset < len(rest) and rest[offset] != quote:
                    offset += 2 if rest[offset] == "\\" else 1
                index += offset + 1
            elif rest.startswith("//"):
                hits.append(number)
                break
            elif rest.startswith("/*"):
                hits.append(number)
                in_block_comment = True
                index += 2
            else:
                index += 1

    return hits


def main():
    if not os.path.isdir(SOURCE_ROOT):
        print(f"no test sources at {SOURCE_ROOT} - run this from a generated project")
        return 1

    scanned, exempt, failures = [], [], []

    for dirpath, _, filenames in os.walk(SOURCE_ROOT):
        for name in sorted(filenames):
            if not name.endswith(".java"):
                continue
            path = os.path.join(dirpath, name)
            text = open(path, encoding="utf-8").read()
            if any(marker in text for marker in RULE_HOLDER_MARKERS):
                exempt.append(path)
                continue
            scanned.append(path)
            for line in comment_lines(text):
                failures.append((os.path.relpath(path, ROOT), line))

    # A rule that checked nothing has silently stopped applying, and reports success while
    # doing it. Say so rather than passing.
    if not scanned:
        print(f"every test under {os.path.relpath(SOURCE_ROOT, ROOT)} is exempt - "
              f"this rule is checking nothing, which is not the same as passing")
        return 1

    for path, line in failures:
        print(f"{path}:{line}: comment in a test")

    if failures:
        print(f"\n{len(failures)} comment(s) under src/test/java. The test name is the "
              f"explanation; why the behaviour is what it is belongs in the ADR or the "
              f"ticket - ADR 0007.")
        return 1

    print(f"ok: {len(scanned)} test source(s) carry no comments "
          f"({len(exempt)} architecture rule holder(s) exempt)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
