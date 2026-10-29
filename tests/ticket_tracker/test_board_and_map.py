import unittest

from support import SECTIONS, TrackerCase, issue

DECISION = ["status:todo", "type:decision", "context:board"]
MAP = ["status:in-progress", "type:map", "context:board"]


class Board(TrackerCase):
    def test_the_board_groups_open_tickets_by_status_and_leaves_done_out(self):
        self.given(issue(130, title="a", labels=["status:todo", "type:fix", "context:board"]),
                   issue(131, title="b"),
                   issue(132, title="c", labels=["status:in-progress", "type:feature", "context:session"]),
                   issue(133, state="CLOSED", reason="COMPLETED"))
        board = self.ok("board")
        self.assertEqual({k: [t["number"] for t in v] for k, v in board["tickets"].items()},
                         {"draft": [131], "todo": [130], "in-progress": [132], "in-review": []})
        self.assertEqual(board["tickets"]["todo"][0]["context"], "board")

    def test_an_unreadable_ticket_is_listed_with_its_reason_instead_of_hiding_the_board(self):
        self.given(issue(134, labels=["status:todo", "type:fix"]), issue(135))
        board = self.ok("board")
        self.assertEqual(board["unreadable"], [{"number": 134, "title": "A ticket",
                                                "reason": "#134 is unreadable: no context: label, and a todo needs one"}])
        self.assertEqual([t["number"] for t in board["tickets"]["draft"]], [135])

    def test_an_issue_closed_as_not_planned_is_not_on_the_board_at_all(self):
        self.given(issue(136, state="CLOSED", reason="NOT_PLANNED"))
        board = self.ok("board")
        self.assertEqual(board["unreadable"], [])


class Notes(TrackerCase):
    def test_notes_come_from_open_and_closed_issues_and_skip_empty_ones(self):
        self.given(issue(140, body=SECTIONS),
                   issue(141, state="CLOSED", reason="COMPLETED", body=SECTIONS.replace("kept", "Chose a ceiling.")),
                   issue(142, body="## Notes\n\n\n"),
                   issue(143, body="## Notes\n\n_Not analysed yet._\n"),
                   issue(144, state="CLOSED", reason="NOT_PLANNED", body=SECTIONS))
        self.assertEqual([(n["number"], n["state"], n["notes"]) for n in self.ok("notes")],
                         [(140, "OPEN", "kept"), (141, "CLOSED", "Chose a ceiling.")])


class Frontier(TrackerCase):
    def test_the_frontier_is_the_maps_open_todo_sub_issues_whose_blockers_are_all_closed(self):
        self.given(issue(150, labels=MAP, sub_issues=[151, 152, 153, 154, 155]),
                   issue(151, title="free", labels=DECISION),
                   issue(152, title="blocked by open", labels=DECISION, blocked_by=[156]),
                   issue(153, title="claimed", labels=["status:in-progress", "type:decision", "context:board"]),
                   issue(154, title="done", state="CLOSED", reason="COMPLETED", labels=DECISION),
                   issue(155, title="blocked by closed", labels=DECISION, blocked_by=[154]),
                   issue(156, title="open blocker", labels=DECISION))
        self.assertEqual([t["number"] for t in self.ok("frontier", "150")["frontier"]], [151, 155])

    def test_a_feature_ticket_that_is_not_a_sub_issue_is_not_on_the_frontier(self):
        self.given(issue(157, labels=MAP, sub_issues=[158]), issue(158, labels=DECISION),
                   issue(159, labels=["status:todo", "type:feature", "context:board"]))
        self.assertEqual([t["number"] for t in self.ok("frontier", "157")["frontier"]], [158])

    def test_a_sub_issue_that_is_unreadable_is_reported_and_kept_off_the_frontier(self):
        self.given(issue(160, labels=MAP, sub_issues=[161]), issue(161, labels=["status:todo", "type:decision"]))
        got = self.ok("frontier", "160")
        self.assertEqual(got["frontier"], [])
        self.assertEqual(got["unreadable"][0]["number"], 161)

    def test_the_frontier_of_something_that_is_not_a_map_is_refused(self):
        self.given(issue(162, labels=DECISION))
        self.refused("frontier", "162", why="#162 is a decision, not a map")

    def test_claiming_a_frontier_ticket_adds_in_progress_and_removes_todo(self):
        self.given(issue(163, labels=DECISION), labels=["status:in-progress"])
        self.ok("move", "163", "in-progress")
        self.assertEqual(sorted(self.load()["issues"]["163"]["labels"]),
                         ["context:board", "status:in-progress", "type:decision"])

    def test_the_frontier_reads_every_page_of_sub_issues(self):
        decisions = [issue(n, labels=DECISION) for n in range(181, 186)]
        self.given(issue(180, labels=MAP, sub_issues=[d["number"] for d in decisions]), *decisions)
        self.update(page_size=2)
        self.assertEqual([t["number"] for t in self.ok("frontier", "180")["frontier"]], list(range(181, 186)))

    def test_a_blocker_closed_as_not_planned_still_blocks(self):
        self.given(issue(187, labels=MAP, sub_issues=[188]),
                   issue(188, labels=DECISION, blocked_by=[189]),
                   issue(189, state="CLOSED", reason="NOT_PLANNED", labels=DECISION))
        self.assertEqual(self.ok("frontier", "187")["frontier"], [])

    def test_the_frontier_reads_status_through_the_ticket_rules(self):
        self.given(issue(190, labels=MAP, sub_issues=[191]),
                   issue(191, labels=["status:todo", "status:in-progress", "type:decision", "context:board"]))
        got = self.ok("frontier", "190")
        self.assertEqual(got["frontier"], [])
        self.assertEqual(got["unreadable"][0]["reason"], "#191 is unreadable: two status labels (todo, in-progress)")


class Wiring(TrackerCase):
    def test_a_decision_becomes_a_sub_issue_of_its_map(self):
        self.given(issue(170, labels=MAP), issue(171, labels=DECISION))
        self.ok("add-sub-issue", "170", "171")
        self.assertEqual(self.load()["issues"]["170"]["sub_issues"], [171])

    def test_a_feature_ticket_is_never_a_sub_issue(self):
        self.given(issue(172, labels=MAP), issue(173, labels=["status:todo", "type:feature", "context:board"]))
        self.refused("add-sub-issue", "172", "173", why="#173 is a feature; only decision tickets are a map's sub-issues")
        self.assertEqual(self.writes(), [])

    def test_a_sub_issue_needs_a_map_to_hold_it(self):
        self.given(issue(174, labels=DECISION), issue(175, labels=DECISION))
        self.refused("add-sub-issue", "174", "175", why="#174 is a decision, not a map")

    def test_a_blocker_is_a_native_dependency(self):
        self.given(issue(176, labels=DECISION), issue(177, labels=DECISION))
        self.ok("add-blocker", "177", "176")
        self.assertEqual(self.load()["issues"]["177"]["blocked_by"], [176])


if __name__ == "__main__":
    unittest.main()
