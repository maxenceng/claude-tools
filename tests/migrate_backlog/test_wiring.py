from support import MigrationCase, ticket


class WiringTest(MigrationCase):
    def number(self, id):
        return self.by_old_id(id)["number"]

    def test_a_blocked_by_becomes_a_native_dependency(self):
        self.backlog(ticket("PROJ-1"), ticket("PROJ-2", blocked_by=["PROJ-1"]))
        self.migrated()
        self.assertEqual(self.by_old_id("PROJ-2")["blocked_by"], [self.number("PROJ-1")])
        self.assertNotIn("blocked_by", self.by_old_id("PROJ-1"))

    def test_an_edge_onto_a_map_is_not_a_dependency_and_makes_no_sub_issue(self):
        self.backlog(ticket("PROJ-1", type="map", status="in-progress"), ticket("PROJ-2", blocked_by=["PROJ-1"]))
        self.migrated()
        self.assertNotIn("blocked_by", self.by_old_id("PROJ-2"))
        self.assertNotIn("sub_issues", self.by_old_id("PROJ-1"))

    def test_a_decision_becomes_a_sub_issue_of_its_map_and_keeps_its_other_edges(self):
        self.backlog(ticket("PROJ-1", type="map", status="in-progress"), ticket("PROJ-2"),
                     ticket("PROJ-3", type="decision", blocked_by=["PROJ-1", "PROJ-2"]))
        self.migrated()
        self.assertEqual(self.by_old_id("PROJ-1")["sub_issues"], [self.number("PROJ-3")])
        decision = self.by_old_id("PROJ-3")
        self.assertEqual(decision["blocked_by"], [self.number("PROJ-2")])

    def test_a_done_issue_is_closed_as_completed(self):
        self.backlog(ticket("PROJ-1", status="done"), ticket("PROJ-2", status="todo"))
        self.migrated()
        self.assertEqual((self.by_old_id("PROJ-1")["state"], self.by_old_id("PROJ-1")["stateReason"]),
                         ("CLOSED", "COMPLETED"))
        self.assertEqual(self.by_old_id("PROJ-2")["state"], "OPEN")

    def test_a_dependency_onto_a_done_ticket_is_wired(self):
        self.backlog(ticket("PROJ-1", status="done"), ticket("PROJ-2", blocked_by=["PROJ-1"]))
        self.migrated()
        self.assertEqual(self.by_old_id("PROJ-2")["blocked_by"], [self.number("PROJ-1")])

    def test_a_second_run_writes_nothing_at_all(self):
        self.backlog(ticket("PROJ-1", type="map", status="in-progress"), ticket("PROJ-2", status="done"),
                     ticket("PROJ-3", type="decision", blocked_by=["PROJ-1", "PROJ-2"]),
                     ticket("PROJ-4", body="see PROJ-2\n", blocked_by=["PROJ-2"]))
        self.migrated()
        before = len(self.load()["calls"])
        self.migrated()
        self.assertEqual([c for c in self.load()["calls"][before:] if c[:2] in (["issue", "create"], ["issue", "edit"], ["issue", "close"], ["label", "create"]) or "-X" in c], [])

    def test_a_rerun_after_pass_two_failed_wires_only_what_is_missing(self):
        self.backlog(ticket("PROJ-1"), ticket("PROJ-2", blocked_by=["PROJ-1"]), ticket("PROJ-3", blocked_by=["PROJ-1"]))
        self.migrated()
        three = self.load()
        three["issues"][str(self.number("PROJ-3"))].pop("blocked_by")
        self.state = three
        self.save()
        before = len(three["calls"])
        self.migrated()
        posts = [c for c in self.load()["calls"][before:] if "-X" in c]
        self.assertEqual(len(posts), 1)
        self.assertEqual(self.by_old_id("PROJ-3")["blocked_by"], [self.number("PROJ-1")])
        self.assertEqual(self.by_old_id("PROJ-2")["blocked_by"], [self.number("PROJ-1")])

    def test_a_decision_linked_only_from_its_map_body_is_wired_as_a_sub_issue(self):
        self.backlog(ticket("PROJ-1", type="map", status="in-progress", body="- [d](PROJ-3-slug.md)\n"),
                     ticket("PROJ-2", type="map", status="in-progress"), ticket("PROJ-3", type="decision"))
        self.migrated()
        self.assertEqual(self.by_old_id("PROJ-1")["sub_issues"], [self.number("PROJ-3")])

    def test_a_feature_linked_from_a_map_body_gets_no_sub_issue_wiring(self):
        self.backlog(ticket("PROJ-1", type="map", status="in-progress", body="PROJ-2\n"), ticket("PROJ-2"))
        self.migrated()
        self.assertNotIn("sub_issues", self.by_old_id("PROJ-1"))
