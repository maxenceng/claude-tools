import contextlib
import io
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE_GH = os.path.join(HERE, "..", "ticket_tracker", "fake_gh.py")
SCRIPTS = os.path.join(HERE, "..", "..", "plugins", "memory-sync", "scripts")

os.environ.update(QDRANT_URL="http://q", QDRANT_API_KEY="k", EMBEDDINGS_URL="http://e")
sys.path.insert(0, SCRIPTS)
import sync_docs  # noqa: E402


def issue(number, title, body, state="OPEN", reason=None, labels=()):
    return {"number": number, "id": number, "title": title, "body": body, "labels": list(labels), "state": state,
            "stateReason": reason, "updatedAt": "2026-10-28T09:00:00Z", "branches": []}


class IndexingIssues(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        self.project = os.path.join(self.dir, "project")
        os.makedirs(os.path.join(self.project, "docs", "backlog"))
        with open(os.path.join(self.project, "docs", "backlog", "OLD-1.md"), "w", encoding="utf-8") as handle:
            handle.write("# old ticket file\n")
        os.makedirs(os.path.join(self.dir, "bin"))
        gh = os.path.join(self.dir, "bin", "gh")
        shutil.copy(FAKE_GH, gh)
        os.chmod(gh, os.stat(gh).st_mode | stat.S_IXUSR)
        self.state = os.path.join(self.dir, "state.json")
        self.addCleanup(os.environ.pop, "FAKE_GH_STATE", None)
        os.environ["FAKE_GH_STATE"] = self.state
        self.old_path = os.environ["PATH"]
        self.addCleanup(os.environ.__setitem__, "PATH", self.old_path)
        os.environ["PATH"] = os.path.join(self.dir, "bin") + os.pathsep + self.old_path

    def given(self, issues, offline=False):
        state = {"issues": {str(i["number"]): i for i in issues}, "labels": [], "calls": [], "next": 100,
                 "clock": 0, "prs": [], "replies": [], "merged_heads": [], "graphql": {}, "offline": offline}
        with open(self.state, "w", encoding="utf-8") as handle:
            json.dump(state, handle)

    def test_open_and_closed_issues_are_indexed_with_their_number_title_state_labels_and_body(self):
        self.given([issue(4, "Open one", "## Notes\n\nopen body", labels=["status:todo"]),
                    issue(5, "Closed one", "closed body", state="CLOSED", reason="COMPLETED")])
        found = {path: (kind, text) for path, kind, text, _ in sync_docs.issue_documents(self.project)}
        self.assertEqual(sorted(found), ["issues/4", "issues/5"])
        self.assertEqual(found["issues/4"][0], "ticket")
        self.assertIn("# #4 Open one", found["issues/4"][1])
        self.assertIn("status:todo", found["issues/4"][1])
        self.assertIn("open body", found["issues/4"][1])
        self.assertIn("closed", found["issues/5"][1].lower())

    def test_the_docs_backlog_folder_is_no_longer_read(self):
        self.given([])
        paths = [path for path, _ in sync_docs.find_files(self.project)]
        self.assertEqual([p for p in paths if "backlog" in p], [])

    def test_an_unreachable_github_skips_the_issues_and_says_so_without_failing(self):
        self.given([issue(4, "x", "y")], offline=True)
        with contextlib.redirect_stderr(io.StringIO()) as said:
            found = list(sync_docs.issue_documents(self.project))
        self.assertEqual(found, [])
        self.assertIn("tickets skipped", said.getvalue())


if __name__ == "__main__":
    unittest.main()
