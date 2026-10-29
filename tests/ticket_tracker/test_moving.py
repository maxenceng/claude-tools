import unittest

from support import TrackerCase, issue

READY = ["status:todo", "type:feature", "context:board"]


class MovingAStatus(TrackerCase):
    def test_a_move_is_one_edit_adding_the_new_label_and_removing_the_old(self):
        self.given(issue(20, labels=READY), labels=["status:in-progress"])
        self.ok("move", "20", "in-progress")
        edits = [c for c in self.load()["calls"] if c[:2] == ["issue", "edit"]]
        self.assertEqual(edits, [["issue", "edit", "20", "--add-label", "status:in-progress",
                                  "--remove-label", "status:todo"]])
        self.assertEqual(self.writes(), edits)

    def test_a_move_changes_the_status_label_and_nothing_else(self):
        self.given(issue(21, labels=READY), labels=["status:in-progress"])
        self.ok("move", "21", "in-progress")
        self.assertEqual(sorted(self.load()["issues"]["21"]["labels"]),
                         ["context:board", "status:in-progress", "type:feature"])

    def test_a_draft_without_a_status_label_has_nothing_to_remove(self):
        self.given(issue(22, labels=["type:feature", "context:board"]), labels=["status:todo"])
        self.ok("move", "22", "todo")
        edits = [c for c in self.load()["calls"] if c[:2] == ["issue", "edit"]]
        self.assertEqual(edits, [["issue", "edit", "22", "--add-label", "status:todo"]])

    def test_a_missing_status_label_is_created_before_it_is_applied(self):
        self.given(issue(23, labels=READY))
        self.ok("move", "23", "in-review")
        writes = self.writes()
        self.assertEqual(writes[0][:3], ["label", "create", "status:in-review"])
        self.assertEqual(writes[1][:2], ["issue", "edit"])
        self.assertEqual(len(writes), 2)

    def test_a_status_label_that_exists_is_not_created_again(self):
        self.given(issue(24, labels=READY), labels=["status:in-review"])
        self.ok("move", "24", "in-review")
        self.assertEqual([c for c in self.writes() if c[0] == "label"], [])

    def test_an_unreadable_ticket_refuses_the_move_and_writes_nothing(self):
        self.given(issue(25, labels=["status:todo", "type:feature"]), labels=["status:in-progress"])
        self.refused("move", "25", "in-progress", why="#25 is unreadable: no context: label")
        self.assertEqual(self.writes(), [])

    def test_done_is_not_a_status_to_move_to(self):
        self.given(issue(26, labels=READY))
        self.refused("move", "26", "done", why="done is closed as completed")
        self.assertEqual(self.writes(), [])

    def test_a_done_ticket_cannot_be_moved(self):
        self.given(issue(27, state="CLOSED", reason="COMPLETED", labels=["status:in-review"]))
        self.refused("move", "27", "todo", why="#27 is done")
        self.assertEqual(self.writes(), [])

    def test_a_move_that_would_leave_the_ticket_unreadable_is_refused_and_writes_nothing(self):
        self.given(issue(28, labels=["type:feature"]), labels=["status:todo"])
        self.refused("move", "28", "todo", why="#28 is unreadable: no context: label, and a todo needs one")
        self.assertEqual(self.writes(), [])


if __name__ == "__main__":
    unittest.main()
