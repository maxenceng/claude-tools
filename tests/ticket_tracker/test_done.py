import json
import os
import unittest

from support import SECTIONS, TrackerCase, issue

REVIEW = ["status:in-review", "type:feature", "context:board"]


class Done(TrackerCase):
    def merged(self, number, **extra):
        self.given(issue(number, labels=REVIEW, branches=["%d-x" % number], **extra))
        self.update(merged_heads=["%d-x" % number])

    def notes(self, text):
        path = os.path.join(self.dir, "notes.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def calls(self, *kind):
        return [c for c in self.load()["calls"] if c[:2] == list(kind)]

    def test_done_writes_notes_clears_labels_in_one_edit_and_closes_an_issue_the_keyword_missed(self):
        self.merged(110)
        said = self.ok("done", "110", "--notes-file", self.notes("Rejected X."), "--expect-updated-at",
                       "2026-10-28T09:00:00Z")
        stored = self.load()["issues"]["110"]
        self.assertEqual(self.calls("issue", "edit").__len__(), 1)
        self.assertIn("## Notes\n\nRejected X.\n", stored["body"])
        self.assertIn("## Model decision\n\nOn the board aggregate.", stored["body"])
        self.assertEqual(stored["labels"], ["type:feature", "context:board"])
        self.assertEqual((stored["state"], stored["stateReason"]), ("CLOSED", "COMPLETED"))
        self.assertTrue(said["closedByDone"])
        self.assertIn("closing keyword", said["message"])

    def test_done_on_an_issue_the_merge_already_closed_clears_labels_and_does_not_close_again(self):
        self.merged(111, state="CLOSED", reason="COMPLETED")
        said = self.ok("done", "111")
        self.assertEqual(self.load()["issues"]["111"]["labels"], ["type:feature", "context:board"])
        self.assertEqual(self.calls("issue", "close"), [])
        self.assertFalse(said["closedByDone"])

    def test_done_on_a_tidy_closed_issue_writes_nothing(self):
        self.given(issue(112, state="CLOSED", reason="COMPLETED", labels=["type:feature", "context:board"],
                         branches=["112-x"]))
        self.update(merged_heads=["112-x"])
        self.ok("done", "112")
        self.assertEqual(self.writes(), [])

    def test_done_refuses_when_no_linked_branch_has_merged_and_writes_nothing(self):
        self.given(issue(113, labels=REVIEW, branches=["113-x"]))
        self.refused("done", "113", why="#113 is not merged")
        self.assertEqual(self.writes(), [])

    def test_done_refuses_an_issue_with_no_linked_branch(self):
        self.given(issue(114, labels=REVIEW))
        self.refused("done", "114", why="#114 is not merged")

    def test_done_refuses_notes_when_the_issue_moved_since_they_were_read(self):
        self.merged(115, updatedAt="2026-10-28T09:45:00Z")
        self.refused("done", "115", "--notes-file", self.notes("n"), "--expect-updated-at", "2026-10-28T09:00:00Z",
                     why="#115 changed since it was read")
        self.assertEqual(self.writes(), [])

    def test_done_with_notes_but_no_updated_at_is_a_usage_error(self):
        self.merged(116)
        self.refused("done", "116", "--notes-file", self.notes("n"), why="--expect-updated-at", code=2)
        self.assertEqual(self.writes(), [])

    def test_done_refuses_an_issue_closed_as_not_planned(self):
        self.merged(117, state="CLOSED", reason="NOT_PLANNED")
        self.refused("done", "117", why="#117 is unreadable: closed as not planned")


class Closing(TrackerCase):
    def test_a_decision_closes_as_completed_and_loses_its_status_label(self):
        self.given(issue(120, labels=["status:in-progress", "type:decision", "context:board"]))
        self.ok("close", "120")
        stored = self.load()["issues"]["120"]
        self.assertEqual((stored["state"], stored["stateReason"]), ("CLOSED", "COMPLETED"))
        self.assertEqual(stored["labels"], ["type:decision", "context:board"])

    def test_a_map_is_never_closed_by_the_script(self):
        self.given(issue(121, labels=["status:in-progress", "type:map", "context:board"]))
        self.refused("close", "121", why="a map is closed by hand")
        self.assertEqual(self.writes(), [])

    def test_closing_an_unreadable_ticket_is_refused(self):
        self.given(issue(122, labels=["status:in-progress", "type:decision"]))
        self.refused("close", "122", why="#122 is unreadable")


if __name__ == "__main__":
    unittest.main()
