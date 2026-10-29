import unittest

from support import TrackerCase, issue

READY = ["status:todo", "type:feature", "context:board"]


class SettingContextAndType(TrackerCase):
    def edits(self):
        return [c for c in self.load()["calls"] if c[:2] == ["issue", "edit"]]

    def test_a_context_move_is_one_edit_swapping_the_context_label(self):
        self.given(issue(60, labels=READY), labels=["context:session"])
        self.ok("label", "60", "--context", "session")
        self.assertEqual(self.edits(), [["issue", "edit", "60", "--add-label", "context:session",
                                         "--remove-label", "context:board"]])

    def test_a_context_the_map_names_but_github_lacks_is_created_as_it_is_applied(self):
        self.given(issue(61, labels=READY))
        self.ok("label", "61", "--context", "session")
        self.assertEqual(self.writes()[0][:3], ["label", "create", "context:session"])

    def test_a_context_the_map_does_not_name_is_refused_and_nothing_is_written(self):
        self.given(issue(62, labels=READY))
        self.refused("label", "62", "--context", "billing", why="context:billing is not named in docs/context-map.md")
        self.assertEqual(self.writes(), [])

    def test_a_name_in_the_map_s_second_table_is_not_a_context(self):
        self.given(issue(63, labels=READY))
        self.refused("label", "63", "--context", "shell", why="context:shell is not named in docs/context-map.md")

    def test_cross_context_is_accepted_by_every_project_without_being_named(self):
        self.given(issue(64, labels=READY))
        self.ok("label", "64", "--context", "cross-context")
        self.assertIn("context:cross-context", self.load()["issues"]["64"]["labels"])

    def test_a_missing_context_map_refuses_every_context_but_cross_context(self):
        import os
        os.remove(os.path.join(self.project, "docs", "context-map.md"))
        self.given(issue(65, labels=READY))
        self.refused("label", "65", "--context", "board", why="docs/context-map.md")
        self.assertEqual(self.writes(), [])

    def test_a_type_label_is_swapped_and_created_when_missing(self):
        self.given(issue(66, labels=READY))
        self.ok("label", "66", "--type", "fix")
        self.assertEqual(self.writes()[0][:3], ["label", "create", "type:fix"])
        self.assertEqual(sorted(self.load()["issues"]["66"]["labels"]), ["context:board", "status:todo", "type:fix"])

    def test_a_type_outside_the_vocabulary_is_refused(self):
        self.given(issue(67, labels=READY))
        self.refused("label", "67", "--type", "epic", why="type is one of", code=2)
        self.assertEqual(self.writes(), [])

    def test_a_draft_gains_its_context_without_losing_anything(self):
        self.given(issue(68, labels=["status:draft"]), labels=["context:board", "type:feature"])
        self.ok("label", "68", "--context", "board", "--type", "feature")
        self.assertEqual(self.edits(), [["issue", "edit", "68", "--add-label", "context:board,type:feature"]])


if __name__ == "__main__":
    unittest.main()
