"""The ADR folder as check-adr-numbers.py and write-adr-index.py both read it.

One reading, so the index lists exactly the files the numbering check reads as numbered: two
copies of the file-name rule would drift. Duplicates and gaps are listed too; the check, not
the index, says whether the numbering is clean.
"""
import glob
import os
import re

# Anchored to the repo rather than to the working directory. Globbed relative to wherever
# it was invoked, this found no ADRs and reported success -- a check that passes when it
# cannot see its input is worse than no check.
# CHECK_ROOT is how guard-fixtures.py points this at a fixture tree; nothing else sets it.
ROOT = os.environ.get("CHECK_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ADR_DIR = os.path.join(ROOT, "docs", "adr")

INDEX_NAME = "README.md"

INDEX = os.path.join(ADR_DIR, INDEX_NAME)

NUMBERED = re.compile(r"^(\d{4})-[a-z0-9-]+\.md$")

HEADING = re.compile(r"^# (\d+)\. (.+)$")

# A sentence opens a line or follows a full stop: `Accepted` on one line and
# `Superseded by ADR 0003.` on the next is still superseded.
SUPERSEDED = re.compile(r"(?:^|\. )Superseded by ADR (\d{4})", re.MULTILINE)

STATUS_WORDS = ("Proposed", "Accepted", "Rejected", "Deprecated")

STATUS_WORD = re.compile(rf"^({'|'.join(STATUS_WORDS)})\b")

INDEX_HEADER = (
    "# Decisions\n"
    "\n"
    "<!-- Written by `make adr-index`; `make adr-check` fails when it is stale. -->\n"
    "\n"
)


class Adr:
    def __init__(self, number, name, title, status):
        self.number = number
        self.name = name
        self.title = title
        self.status = status


def relative(path):
    return os.path.relpath(path, ROOT)


def files():
    """Every Markdown file in the folder but the index: (numbered by number, unnumbered names)."""
    numbered = {}
    unnumbered = []
    for path in sorted(glob.glob(os.path.join(ADR_DIR, "*.md"))):
        name = os.path.basename(path)
        if name == INDEX_NAME:
            continue
        match = NUMBERED.match(name)
        if match:
            numbered.setdefault(int(match.group(1)), []).append(name)
        else:
            unnumbered.append(name)
    return numbered, unnumbered


def status_section(lines):
    start = lines.index("## Status") + 1 if "## Status" in lines else None
    if start is None:
        return None
    rest = lines[start:]
    end = next((offset for offset, line in enumerate(rest) if line.startswith("## ")), len(rest))
    return "\n".join(line.strip() for line in rest[:end] if line.strip())


def derived_status(paragraph):
    """`Superseded by NNNN.` when a sentence opens with it, else the paragraph's first word."""
    superseded = SUPERSEDED.search(paragraph)
    if superseded:
        return f"Superseded by {superseded.group(1)}."
    word = STATUS_WORD.match(paragraph)
    return f"{word.group(1)}." if word else None


def read(number, name):
    """The ADR in `name`, or the reason the index cannot list it."""
    try:
        with open(os.path.join(ADR_DIR, name), encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except (OSError, UnicodeDecodeError) as error:
        return None, f"{name}: cannot be read ({error})"
    heading = HEADING.match(lines[0]) if lines else None
    if not heading:
        return None, f"{name}: its first line is not `# {number}. Title`"
    if int(heading.group(1)) != number:
        return None, f"{name}: its heading says {heading.group(1)}, its file name {number:04d}"
    paragraph = status_section(lines)
    if not paragraph:
        return None, f"{name}: no `## Status` section, or an empty one"
    status = derived_status(paragraph)
    if not status:
        return None, f"{name}: its status opens with none of {', '.join(STATUS_WORDS)}"
    return Adr(number, name, heading.group(2), status), None


def index(numbered):
    """The index `numbered` makes, or the reasons it cannot be written."""
    adrs = []
    problems = []
    for number, names in sorted(numbered.items()):
        for name in sorted(names):
            adr, problem = read(number, name)
            if problem:
                problems.append(problem)
            else:
                adrs.append(adr)
    if problems:
        return None, problems
    lines = [f"- {adr.number:04d} [{adr.title}]({adr.name}) — {adr.status}\n" for adr in adrs]
    return INDEX_HEADER + "".join(lines), []
