from support import MigrationCase, marker, ticket


class DryRunTest(MigrationCase):
    def test_it_lists_an_issue_with_its_title_labels_and_state(self):
        self.backlog(ticket("PROJ-1", title="First thing", status="todo", type="fix", context="board"))
        out = self.migrated("--dry-run").stdout
        self.assertIn("PROJ-1", out)
        self.assertIn("First thing", out)
        self.assertIn("labels: status:todo, type:fix, context:board", out)
        self.assertIn("state: open", out)

    def test_a_draft_has_no_status_label(self):
        self.backlog(ticket("PROJ-1", status="draft"))
        out = self.migrated("--dry-run").stdout
        self.assertIn("labels: type:feature, context:board", out)
        self.assertNotIn("status:", out)

    def test_a_done_ticket_is_closed_and_has_no_status_label(self):
        self.backlog(ticket("PROJ-1", status="done"))
        out = self.migrated("--dry-run").stdout
        self.assertIn("state: closed as completed", out)
        self.assertNotIn("status:", out)

    def test_it_lists_dependencies_and_the_sub_issue_parent_of_a_decision(self):
        self.backlog(ticket("PROJ-1", type="map", status="in-progress"), ticket("PROJ-2"),
                     ticket("PROJ-3", type="decision", blocked_by=["PROJ-1", "PROJ-2"]))
        out = self.migrated("--dry-run").stdout
        decision = out[out.index("PROJ-3"):]
        self.assertIn("blocked by: PROJ-2", decision)
        self.assertIn("sub-issue of: PROJ-1", decision)

    def test_an_edge_onto_a_map_is_listed_as_dropped_not_as_a_dependency(self):
        self.backlog(ticket("PROJ-1", type="map", status="in-progress"), ticket("PROJ-2", blocked_by=["PROJ-1"]))
        out = self.migrated("--dry-run").stdout
        feature = out[out.index("PROJ-2"):]
        self.assertNotIn("blocked by", feature)
        self.assertIn("dropped edge onto map: PROJ-1", feature)
        self.assertNotIn("sub-issue of", feature)

    def test_it_writes_nothing(self):
        self.backlog(ticket("PROJ-1"), ticket("PROJ-2", status="done"))
        self.migrated("--dry-run")
        self.assertEqual(self.writes(), [])
        self.assertEqual(self.issues(), {})

    def test_an_already_migrated_ticket_is_reported_as_skipped(self):
        self.backlog(ticket("PROJ-1"), ticket("PROJ-2"))
        self.given_issue(41, "text\n\n" + marker("PROJ-1"))
        out = self.migrated("--dry-run").stdout
        self.assertIn("PROJ-1  exists as #41, skipped", out)
        self.assertIn("would create 1 issue", out)
