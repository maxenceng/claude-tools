#!/usr/bin/env python3
"""Write docs/adr/README.md, the index of every ADR, from the ADRs themselves.

A hand-kept index goes stale the first time a branch adds an ADR and forgets it, and the
site shows it as complete. check-adr-numbers.py fails when this file is not what this
script would write, so the index is regenerated rather than edited.
"""
import os
import sys

import adr_folder


def main():
    if not os.path.isdir(adr_folder.ADR_DIR):
        print(f"no ADR directory at {adr_folder.relative(adr_folder.ADR_DIR)}")
        return 1
    numbered, _ = adr_folder.files()
    content, problems = adr_folder.index(numbered)
    if problems:
        print("cannot write the ADR index:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    with open(adr_folder.INDEX, "w", encoding="utf-8") as handle:
        handle.write(content)
    print(f"wrote {adr_folder.relative(adr_folder.INDEX)}: {sum(len(names) for names in numbered.values())} ADR(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
