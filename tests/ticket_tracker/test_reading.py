import unittest

from support import TrackerCase, issue


class ReadingATicket(TrackerCase):
    def test_an_open_issue_with_no_status_label_is_a_draft_that_may_lack_context_and_type(self):
        self.given(issue(5))
        shown = self.ok("show", "5")
        self.assertEqual(shown["status"], "draft")
        self.assertIsNone(shown["context"])
        self.assertIsNone(shown["type"])

    def test_a_todo_without_a_context_label_is_unreadable_and_show_says_why(self):
        self.given(issue(6, labels=["status:todo", "type:feature"]))
        self.refused("show", "6", why="#6 is unreadable: no context: label")

    def test_a_todo_without_a_type_label_is_unreadable(self):
        self.given(issue(7, labels=["status:todo", "context:board"]))
        self.refused("show", "7", why="#7 is unreadable: no type: label")

    def test_a_todo_with_two_context_labels_is_unreadable(self):
        self.given(issue(8, labels=["status:todo", "type:fix", "context:board", "context:session"]))
        self.refused("show", "8", why="#8 is unreadable: two context: labels")

    def test_two_status_labels_are_unreadable_even_on_a_draft_shaped_issue(self):
        self.given(issue(9, labels=["status:todo", "status:in-review", "type:fix", "context:board"]))
        self.refused("show", "9", why="#9 is unreadable: two status labels")

    def test_an_issue_closed_as_not_planned_is_unreadable(self):
        self.given(issue(10, state="CLOSED", reason="NOT_PLANNED", labels=["status:todo", "type:fix", "context:board"]))
        self.refused("show", "10", why="#10 is unreadable: closed as not planned")

    def test_an_issue_closed_as_completed_is_done_whatever_labels_it_still_carries(self):
        self.given(issue(11, state="CLOSED", reason="COMPLETED", labels=["status:in-review"]))
        self.assertEqual(self.ok("show", "11")["status"], "done")

    def test_a_readable_ticket_shows_its_sections_and_its_updated_at(self):
        self.given(issue(12, labels=["status:todo", "type:feature", "context:board"]))
        shown = self.ok("show", "12")
        self.assertEqual(shown["context"], "board")
        self.assertEqual(shown["type"], "feature")
        self.assertEqual(shown["updatedAt"], "2026-10-28T09:00:00Z")
        self.assertEqual(shown["sections"]["Model decision"], "On the board aggregate.")
        self.assertEqual(list(shown["sections"]), ["Acceptance criteria", "Model decision", "Design direction",
                                                   "Glossary impact", "Notes"])


if __name__ == "__main__":
    unittest.main()
