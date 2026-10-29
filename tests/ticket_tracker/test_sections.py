import json
import unittest

from support import SECTIONS, TrackerCase, issue

READY = ["status:todo", "type:feature", "context:board"]
READ_AT = "2026-10-28T09:00:00Z"


class WritingASection(TrackerCase):
    def put(self, number, sections, at=READ_AT):
        return self.run_tracker("write-sections", str(number), "--expect-updated-at", at, stdin=json.dumps(sections))

    def test_a_write_replaces_only_that_section_and_leaves_the_others_byte_for_byte(self):
        self.given(issue(30, labels=READY))
        done = self.put(30, {"Model decision": "On a new aggregate.\n"})
        self.assertEqual(done.returncode, 0, done.stderr)
        expected = SECTIONS.replace("On the board aggregate.", "On a new aggregate.")
        self.assertEqual(self.load()["issues"]["30"]["body"], expected)

    def test_a_write_is_one_edit(self):
        self.given(issue(31, labels=READY))
        self.put(31, {"Notes": "a", "Glossary impact": "b"})
        self.assertEqual(len(self.writes()), 1)

    def test_a_write_reports_the_updated_at_to_expect_next(self):
        self.given(issue(32, labels=READY))
        self.put(32, {"Notes": "a"})
        shown = self.ok("show", "32")
        self.assertEqual(json.loads(self.put(32, {"Notes": "b"}, at=shown["updatedAt"]).stdout)["updatedAt"],
                         self.ok("show", "32")["updatedAt"])

    def test_a_write_refuses_and_changes_nothing_when_the_issue_moved_since_it_was_read(self):
        self.given(issue(33, labels=READY, updatedAt="2026-10-28T09:30:00Z"))
        before = self.load()["issues"]["33"]["body"]
        self.refused("write-sections", "33", "--expect-updated-at", READ_AT,
                     stdin=json.dumps({"Notes": "mine"}), why="#33 changed since it was read")
        self.assertEqual(self.writes(), [])
        self.assertEqual(self.load()["issues"]["33"]["body"], before)

    def test_a_write_without_the_updated_at_it_was_read_at_is_a_usage_error(self):
        self.given(issue(34, labels=READY))
        self.refused("write-sections", "34", stdin=json.dumps({"Notes": "x"}), why="--expect-updated-at", code=2)
        self.assertEqual(self.writes(), [])

    def test_a_section_the_body_lacks_is_appended(self):
        self.given(issue(35, labels=READY, body="## Acceptance criteria\n\n- [ ] a\n"))
        self.put(35, {"Notes": "late"})
        self.assertEqual(self.load()["issues"]["35"]["body"], "## Acceptance criteria\n\n- [ ] a\n\n## Notes\n\nlate\n")

    def test_a_heading_inside_a_code_fence_is_not_a_section(self):
        body = "## Notes\n\n```\n## Notes\nnot a heading\n```\n\n## Other\n\nx\n"
        self.given(issue(36, labels=READY, body=body))
        self.put(36, {"Notes": "new"})
        self.assertEqual(self.load()["issues"]["36"]["body"], "## Notes\n\nnew\n\n## Other\n\nx\n")

    def test_a_fence_closes_only_on_its_own_marker(self):
        body = "## Notes\n\n~~~\n```\n## Notes\n```\n~~~\n\n## Other\n\nx\n"
        self.given(issue(38, labels=READY, body=body))
        self.put(38, {"Notes": "new"})
        self.assertEqual(self.load()["issues"]["38"]["body"], "## Notes\n\nnew\n\n## Other\n\nx\n")

    def test_an_unreadable_ticket_refuses_the_write(self):
        self.given(issue(37, labels=["status:todo", "type:feature"]))
        self.refused("write-sections", "37", "--expect-updated-at", READ_AT, stdin=json.dumps({"Notes": "x"}),
                     why="#37 is unreadable")
        self.assertEqual(self.writes(), [])

    def test_a_write_keeps_a_bodys_windows_line_endings(self):
        self.given(issue(38, labels=READY, body="## A\r\n\r\none\r\n\r\n## B\r\n\r\ntwo\r\n"))
        self.put(38, {"A": "uno"})
        self.assertEqual(self.load()["issues"]["38"]["body"], "## A\r\n\r\nuno\r\n\r\n## B\r\n\r\ntwo\r\n")


if __name__ == "__main__":
    unittest.main()
