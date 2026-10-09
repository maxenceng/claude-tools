#!/usr/bin/env python3
"""Fail when code or a living document still names a ticket that has landed.

A ticket id is a scheduling artifact. While the work is open it is a useful pointer --
"the type this ticket will share" says something no other word does. The moment the
ticket is done the pointer is a claim about the past that nothing keeps true, and it
reads as future work to whoever finds it next.

The rule is not about tense. "when X-4 declares them" can be caught by a grep for the
future; "and from X-4 a show" cannot be told from the past by any pattern. So a done
ticket is not named here at all. ADR 0016.

docs/backlog/, docs/adr/, docs/endpoints/, docs/research/ and scripts/ are exempt. A ticket
names itself and its neighbours, an ADR is a dated record of what was decided, an endpoint's
`tickets:` is the list of tickets that shaped it, a research note says when and for which
ticket it was researched, and a check script's docstring names the incident that made the
rule -- all of them are meant to read as history.

Any `PREFIX-n` is a candidate; only an id that a done ticket in docs/backlog/ carries fails.
A fixed list of context prefixes misses every context added after it was written.
"""
import glob
import io
import os
import re
import sys

# CHECK_ROOT is how guard-fixtures.py points this at a fixture tree; nothing else sets it.
ROOT = os.environ.get("CHECK_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TICKET = re.compile(r"\b[A-Z]+-[0-9]+\b")
STATUS = re.compile(r"^status:\s*(\S+)\s*$", re.MULTILINE)
ID = re.compile(r"^id:\s*(\S+)\s*$", re.MULTILINE)
EXEMPT = ("docs/backlog/", "docs/adr/", "docs/endpoints/", "docs/research/", "scripts/")


def done_tickets():
    done = set()
    for path in sorted(glob.glob(os.path.join(ROOT, "docs/backlog/*.md"))):
        source = io.open(path, encoding="utf-8").read()
        identifier, status = ID.search(source), STATUS.search(source)
        if identifier and status and status.group(1) == "done":
            done.add(identifier.group(1))
    return done


def scanned():
    for pattern in ("src/**/*.java", "docs/**/*.md", "*.md"):
        for path in sorted(glob.glob(os.path.join(ROOT, pattern), recursive=True)):
            relative = os.path.relpath(path, ROOT)
            if not relative.startswith(EXEMPT):
                yield relative


def main():
    paths = list(scanned())
    if not paths:
        print("nothing was scanned -- the globs match no file")
        return 1

    done = done_tickets()
    if not done:
        print("ok: no ticket in docs/backlog/ is done yet, so none can be named stale")
        return 0

    failures = []
    for path in paths:
        for number, line in enumerate(io.open(os.path.join(ROOT, path), encoding="utf-8"), start=1):
            for ticket in TICKET.findall(line):
                if ticket in done:
                    failures.append((path, number, ticket, line.strip()))

    for path, number, ticket, line in failures:
        print("%s:%d: names %s, which is done" % (path, number, ticket))
        print("    %s" % line)

    if failures:
        print(
            "\n%d reference(s) to a landed ticket. Name the behaviour, not the ticket that"
            " added it -- git and docs/adr/ are what remember which one did." % len(failures)
        )
        return 1

    print("ok: %d file(s) name no landed ticket" % len(paths))
    return 0


if __name__ == "__main__":
    sys.exit(main())
