import json
import os
import unittest

from support import TrackerCase, issue

READY = ["status:todo", "type:feature", "context:board"]
SECTION = json.dumps({"Notes": "x"})
AT = "2026-10-28T09:00:00Z"

VERBS = {
    "show": (["show", "50"], ""),
    "move": (["move", "50", "in-progress"], ""),
    "write-sections": (["write-sections", "50", "--expect-updated-at", AT], SECTION),
    "label": (["label", "50", "--context", "board"], ""),
    "create": (["create", "--title", "x", "--context", "board"], ""),
    "ready": (["ready", "50", "start"], ""),
    "develop": (["develop", "50"], ""),
    "pr-create": (["pr-create", "--title", "t", "--body-file", "BODY", "--closes", "50"], ""),
    "pr-feedback": (["pr-feedback", "7"], ""),
    "pr-reply": (["pr-reply", "7", "11", "--body-file", "BODY"], ""),
    "done": (["done", "50"], ""),
    "close": (["close", "50"], ""),
    "board": (["board"], ""),
    "notes": (["notes"], ""),
    "frontier": (["frontier", "50"], ""),
    "add-sub-issue": (["add-sub-issue", "50", "51"], ""),
    "add-blocker": (["add-blocker", "50", "51"], ""),
}


class WithoutTheNetwork(TrackerCase):
    def test_every_verb_refuses_with_that_reason_and_writes_nothing(self):
        body = os.path.join(self.dir, "body.md")
        with open(body, "w", encoding="utf-8") as handle:
            handle.write("x")
        for name, (args, stdin) in VERBS.items():
            args = [body if a == "BODY" else a for a in args]
            with self.subTest(verb=name):
                self.given(issue(50, labels=READY), labels=["status:in-progress"])
                self.update(offline=True)
                before = self.load()
                before.pop("calls")
                done = self.run_tracker(*args, stdin=stdin)
                self.assertEqual(done.returncode, 3, done.stdout + done.stderr)
                self.assertIn("GitHub is unreachable", done.stderr)
                self.assertIn("nothing was written", done.stderr)
                after = self.load()
                after.pop("calls")
                self.assertEqual(after, before, "GitHub's state changed while it was unreachable")
                self.update(offline=False, calls=[])

    def test_a_machine_without_gh_refuses_rather_than_failing_obscurely(self):
        os.remove(os.path.join(self.bin, "gh"))
        done = self.run_tracker("board", env_path=self.bin)
        self.assertEqual(done.returncode, 1)
        self.assertIn("gh is not installed", done.stderr)


if __name__ == "__main__":
    unittest.main()
