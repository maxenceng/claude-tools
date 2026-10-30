import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "..", "scripts", "migrate-backlog-to-issues.py")
REPO_URL = "https://github.com/o/r"


def ticket(id, title="A ticket", status="todo", type="feature", context="board", blocked_by=(),
           created="2026-10-01", body="## Notes\n\nplain\n", tracker_id="7"):
    lines = ["---", "id: " + id, "status: " + status, "context: " + context, "type: " + type]
    if tracker_id:
        lines.append("tracker_id: " + tracker_id)
    lines.append("created: " + created)
    if blocked_by:
        lines.append("blocked_by: [%s]" % ", ".join(blocked_by))
    return "\n".join(lines + ["---", "", "# " + title, "", body])


def marker(id, created="2026-10-01"):
    return "Migrated from %s, created %s." % (id, created)


class MigrationCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        self.project = os.path.join(self.dir, "project")
        os.makedirs(self.project)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "T")
        bin_dir = os.path.join(self.dir, "bin")
        os.makedirs(bin_dir)
        gh = os.path.join(bin_dir, "gh")
        shutil.copy(os.path.join(HERE, "fake_gh.py"), gh)
        os.chmod(gh, os.stat(gh).st_mode | stat.S_IXUSR)
        self.bin = bin_dir
        self.state_path = os.path.join(self.dir, "state.json")
        self.state = {"issues": {}, "labels": [], "calls": [], "next": 100, "url": REPO_URL}
        self.save()

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.project, check=True, capture_output=True)

    def write(self, relative, content):
        path = os.path.join(self.project, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(path, mode, **({} if mode == "wb" else {"encoding": "utf-8"})) as handle:
            handle.write(content)

    def backlog(self, *tickets):
        for text in tickets:
            id = text.split("id: ")[1].split("\n")[0]
            self.write("docs/backlog/%s-slug.md" % id, text)

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "state")

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

    def given_issue(self, number, body, title="x", labels=(), state="OPEN", reason=None):
        self.state = self.load()
        self.state["issues"][str(number)] = {"number": number, "id": 9000 + number, "title": title, "body": body,
                                             "labels": list(labels), "state": state, "stateReason": reason}
        self.state["labels"] = sorted(set(self.state["labels"]) | set(labels))
        self.state["next"] = max(self.state["next"], number + 1)
        self.save()

    def run_script(self, *args):
        env = dict(os.environ, PATH=self.bin + os.pathsep + os.environ["PATH"], FAKE_GH_STATE=self.state_path)
        self.result = subprocess.run([sys.executable, os.path.abspath(SCRIPT), *args], cwd=self.project, env=env,
                                     capture_output=True, text=True)
        return self.result

    def migrated(self, *args):
        self.commit()
        done = self.run_script(*args)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done

    def refused(self, *args, why):
        self.commit()
        done = self.run_script(*args)
        self.assertEqual(done.returncode, 1, "expected a refusal: " + done.stdout + done.stderr)
        self.assertIn(why, done.stderr)
        self.assertEqual(self.writes(), [], "a refusal must come before any write")
        return done

    def writes(self):
        verbs = {("issue", "create"), ("issue", "edit"), ("issue", "close"), ("label", "create")}
        return [c for c in self.load()["calls"]
                if tuple(c[:2]) in verbs or (c[:1] == ["api"] and "-X" in c)]

    def issues(self):
        return self.load()["issues"]

    def by_old_id(self, id):
        found = [i for i in self.issues().values() if ("Migrated from %s," % id) in i["body"]]
        self.assertEqual(len(found), 1, "issues for %s: %s" % (id, found))
        return found[0]
