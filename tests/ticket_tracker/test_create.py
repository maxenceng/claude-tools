import unittest

from support import TEMPLATE, TrackerCase


def body_of(template):
    return template.split("---\n", 2)[2].lstrip("\n")


class CreatingATicket(TrackerCase):
    def test_a_capture_is_one_draft_issue_with_the_template_body_and_no_frontmatter(self):
        made = self.ok("create", "--title", "Show sessions", "--context", "session")
        stored = self.load()["issues"][str(made["number"])]
        self.assertEqual(stored["title"], "Show sessions")
        self.assertEqual(stored["body"], body_of(TEMPLATE))
        self.assertEqual(sorted(stored["labels"]), ["context:session", "status:draft", "type:feature"])

    def test_a_capture_is_a_single_create_call(self):
        self.ok("create", "--title", "One", "--context", "board")
        creates = [c for c in self.writes() if c[:2] == ["issue", "create"]]
        self.assertEqual(len(creates), 1)

    def test_a_line_that_fits_no_context_is_captured_without_a_context_label(self):
        made = self.ok("create", "--title", "Something odd")
        labels = self.load()["issues"][str(made["number"])]["labels"]
        self.assertEqual([n for n in labels if n.startswith("context:")], [])
        self.assertEqual(made["context"], None)

    def test_a_context_the_map_does_not_name_is_refused_before_anything_is_written(self):
        self.refused("create", "--title", "x", "--context", "billing", why="context:billing is not named")
        self.assertEqual(self.writes(), [])

    def test_missing_status_and_type_labels_are_created_as_they_are_applied(self):
        self.ok("create", "--title", "x", "--context", "board")
        created = sorted(c[2] for c in self.writes() if c[:2] == ["label", "create"])
        self.assertEqual(created, ["context:board", "status:draft", "type:feature"])

    def test_a_type_is_taken_from_the_line_when_it_plainly_says_so(self):
        made = self.ok("create", "--title", "Fix the crash", "--type", "fix")
        self.assertIn("type:fix", self.load()["issues"][str(made["number"])]["labels"])

    def test_the_map_template_makes_a_map_in_progress(self):
        made = self.ok("create", "--template", "map", "--title", "Find the way", "--context", "cross-context")
        labels = self.load()["issues"][str(made["number"])]["labels"]
        self.assertEqual(sorted(labels), ["context:cross-context", "status:in-progress", "type:map"])

    def test_the_decision_template_makes_a_decision_that_is_already_todo(self):
        made = self.ok("create", "--template", "decision", "--title", "Which store?", "--context", "board")
        labels = self.load()["issues"][str(made["number"])]["labels"]
        self.assertEqual(sorted(labels), ["context:board", "status:todo", "type:decision"])

    def test_a_missing_template_is_refused_and_nothing_is_written(self):
        import os
        os.remove(os.path.join(self.project, ".github", "ISSUE_TEMPLATE", "ticket.md"))
        self.refused("create", "--title", "x", why=".github/ISSUE_TEMPLATE/ticket.md")
        self.assertEqual(self.writes(), [])

    def test_a_map_or_decision_without_a_context_is_refused_since_it_starts_past_draft(self):
        self.refused("create", "--template", "decision", "--title", "x", why="a todo needs a context")
        self.assertEqual(self.writes(), [])


if __name__ == "__main__":
    unittest.main()
