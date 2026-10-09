#!/usr/bin/env python3
"""Fail when an integration test reads back what it just wrote without clearing the context.

@DataJpaTest holds one transaction open, so a findById after a create is served by
Hibernate's first-level cache and issues no SELECT: the assertion compares a fixture to
itself and would pass against a table that does not exist. ADR 0014.

A project with no JPA entity yet has nothing to round-trip, and passes. One with an entity
and no @DataJpaTest integration test fails, because then the glob below has stopped
matching what it was written for rather than found nothing to check.
"""
import glob
import io
import os
import re
import sys

# CHECK_ROOT is how guard-fixtures.py points this at a fixture tree; nothing else sets it.
ROOT = os.environ.get("CHECK_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CLEAR = "entityManager.clear()"
WRITE = re.compile(r"\.(create|update|save|saveAndFlush)\(")
READ = re.compile(r"\.(findById|findAll|findBy\w+)\(")
TEST = re.compile(r"^    (?:@Test|@ParameterizedTest)\b", re.MULTILINE)
ENTITY = re.compile(r"^@Entity\b", re.MULTILINE)


def methods(source):
    starts = [match.start() for match in TEST.finditer(source)]
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(source)
        body = source[start:end]
        name = re.search(r"\bvoid\s+(\w+)\s*\(", body)
        yield (name.group(1) if name else "?"), body


def has_entities():
    for path in glob.glob(os.path.join(ROOT, "src/main/java/**/*.java"), recursive=True):
        if ENTITY.search(io.open(path, encoding="utf-8").read()):
            return True
    return False


def main():
    failures = []
    scanned = []
    paths = sorted(glob.glob(os.path.join(ROOT, "src/test/java/**/*IntegrationTest.java"), recursive=True))

    for path in paths:
        source = io.open(path, encoding="utf-8").read()
        if "@DataJpaTest" not in source:
            continue
        scanned.append(path)

        for name, body in methods(source):
            if WRITE.search(body) and READ.search(body) and CLEAR not in body:
                failures.append((os.path.relpath(path, ROOT), name))

    for path, name in failures:
        print("%s: %s reads back a write without %s" % (path, name, CLEAR))

    if failures:
        print(
            "\n%d test(s) read their own persistence context, not the database. ADR 0014."
            % len(failures)
        )
        return 1

    if not scanned:
        if has_entities():
            print("src/main has a JPA @Entity but no @DataJpaTest *IntegrationTest was found -- this check scanned nothing")
            return 1
        print("ok: no JPA entity yet, so nothing to round-trip")
        return 0

    print("ok: %d @DataJpaTest integration test(s) clear the context before reading back" % len(scanned))
    return 0


if __name__ == "__main__":
    sys.exit(main())
