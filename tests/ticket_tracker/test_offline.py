import json
import unittest

from support import TrackerCase, issue

READY = ["status:todo", "type:feature", "context:board"]
SECTION = json.dumps({"Notes": "x"})
AT = "2026-10-28T09:00:00Z"

VERBS = {
    "show": (["show", "50"], ""),
    "move": (["move", "50", "in-progress"], ""),
    "write-sections": (["write-sections", "50", "--expect-updated-at", AT], SECTION),
}


class WithoutTheNetwork(TrackerCase):
    def test_every_verb_refuses_with_that_reason_and_writes_nothing(self):
        for name, (args, stdin) in VERBS.items():
            with self.subTest(verb=name):
                self.given(issue(50, labels=READY), labels=["status:in-progress"])
                self.update(offline=True)
                done = self.run_tracker(*args, stdin=stdin)
                self.assertEqual(done.returncode, 3, done.stdout + done.stderr)
                self.assertIn("GitHub is unreachable", done.stderr)
                self.assertIn("nothing was written", done.stderr)
                self.assertEqual(self.writes(), [])
                self.assertEqual(self.load()["issues"]["50"]["body"], issue(50)["body"])
                self.update(offline=False, calls=[])


if __name__ == "__main__":
    unittest.main()
