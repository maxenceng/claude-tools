import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "..", "plugins", "ddd-workflow", "scripts", "ticket-tracker")

CONTEXT_MAP = """# Context map

## Contexts

| Context | Responsibility |
|---|---|
| `board` | The backlog |
| `session` | Sessions |

Not contexts:

| Package | Role |
|---|---|
| `shell` | The TUI |
"""

TEMPLATE = """---
name: Ticket
about: A unit of work
---

## Acceptance criteria

_Not analysed yet — `/ticket refine`._

## Model decision

_Not analysed yet — `/ticket refine`._

## Design direction

_Not analysed yet — `/ticket refine`._

## Glossary impact

_Not analysed yet._

## Notes

"""

SECTIONS = """## Acceptance criteria

- [ ] it works

## Model decision

On the board aggregate.

## Design direction

n/a

## Glossary impact

none

## Notes

kept
"""


def issue(number, title="A ticket", labels=(), state="OPEN", reason=None, body=SECTIONS, **extra):
    base = {"number": number, "id": 9000 + number, "title": title, "body": body,
            "labels": list(labels), "state": state, "stateReason": reason,
            "updatedAt": "2026-10-28T09:00:00Z", "branches": []}
    base.update(extra)
    return base


class TrackerCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        self.project = os.path.join(self.dir, "project")
        os.makedirs(os.path.join(self.project, "docs"))
        os.makedirs(os.path.join(self.project, ".github", "ISSUE_TEMPLATE"))
        self.write("docs/context-map.md", CONTEXT_MAP)
        for name in ("ticket", "map", "decision"):
            self.write(".github/ISSUE_TEMPLATE/%s.md" % name, TEMPLATE)
        bin_dir = os.path.join(self.dir, "bin")
        os.makedirs(bin_dir)
        gh = os.path.join(bin_dir, "gh")
        shutil.copy(os.path.join(HERE, "fake_gh.py"), gh)
        os.chmod(gh, os.stat(gh).st_mode | stat.S_IXUSR)
        self.bin = bin_dir
        self.state_path = os.path.join(self.dir, "state.json")
        self.state = {"issues": {}, "labels": [], "calls": [], "next": 100, "clock": 0,
                      "prs": [], "replies": [], "merged_heads": [], "graphql": {}, "offline": False}
        self.save()

    def write(self, relative, text):
        path = os.path.join(self.project, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def given(self, *issues, labels=()):
        for one in issues:
            self.state["issues"][str(one["number"])] = one
        self.state["labels"] = sorted(set(self.state["labels"]) | set(labels)
                                      | {n for one in issues for n in one["labels"]})
        self.save()

    def save(self):
        with open(self.state_path, "w", encoding="utf-8") as handle:
            json.dump(self.state, handle)

    def load(self):
        with open(self.state_path, encoding="utf-8") as handle:
            return json.load(handle)

    def update(self, **values):
        self.state = self.load()
        self.state.update(values)
        self.save()

    def run_tracker(self, *args, stdin="", env_path=None):
        path = env_path or self.bin + os.pathsep + os.environ["PATH"]
        env = dict(os.environ, PATH=path, FAKE_GH_STATE=self.state_path)
        done = subprocess.run([sys.executable, os.path.abspath(SCRIPT), *args], cwd=self.project, env=env,
                              input=stdin, capture_output=True, text=True)
        self.result = done
        return done

    def ok(self, *args, stdin=""):
        done = self.run_tracker(*args, stdin=stdin)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout) if done.stdout.strip() else None

    def refused(self, *args, why, stdin="", code=1):
        done = self.run_tracker(*args, stdin=stdin)
        self.assertEqual(done.returncode, code, "expected a refusal: " + done.stdout + done.stderr)
        self.assertIn(why, done.stderr)
        return done

    def writes(self):
        verbs = {("issue", "edit"), ("issue", "create"), ("issue", "close"), ("issue", "develop"),
                 ("label", "create"), ("pr", "create")}
        return [c for c in self.load()["calls"]
                if tuple(c[:2]) in verbs and "--list" not in c
                or c[:1] == ["api"] and "-X" in c]
