from support import MigrationCase, marker, ticket


class CreateTest(MigrationCase):
    def test_the_title_is_the_heading_and_the_body_the_rest_ending_in_the_marker(self):
        self.backlog(ticket("PROJ-1", title="First thing", created="2026-09-30", body="## Notes\n\nplain\n"))
        self.migrated()
        made = self.by_old_id("PROJ-1")
        self.assertEqual(made["title"], "First thing")
        self.assertEqual(made["body"], "## Notes\n\nplain\n\nMigrated from PROJ-1, created 2026-09-30.\n")

    def test_the_frontmatter_and_tracker_id_are_not_in_the_body(self):
        self.backlog(ticket("PROJ-1", tracker_id="107"))
        self.migrated()
        body = self.by_old_id("PROJ-1")["body"]
        self.assertNotIn("tracker_id", body)
        self.assertNotIn("blocked_by", body)
        self.assertNotIn("---", body)

    def test_labels_follow_the_frontmatter(self):
        self.backlog(ticket("PROJ-1", status="in-progress", type="map", context="session"), ticket("PROJ-2", status="draft"))
        self.migrated()
        self.assertEqual(self.by_old_id("PROJ-1")["labels"], ["status:in-progress", "type:map", "context:session"])
        self.assertEqual(self.by_old_id("PROJ-2")["labels"], ["type:feature", "context:board"])

    def test_a_missing_label_is_created_with_the_colour_ticket_tracker_gives_it(self):
        self.backlog(ticket("PROJ-1"))
        self.migrated()
        self.assertEqual(self.load()["label_colours"],
                         {"status:todo": "ededed", "type:feature": "c5def5", "context:board": "bfd4f2"})

    def test_an_existing_label_is_not_created_again(self):
        self.backlog(ticket("PROJ-1"), ticket("PROJ-2"))
        self.update(labels=["type:feature"])
        self.migrated()
        created = [c[2] for c in self.load()["calls"] if c[:2] == ["label", "create"]]
        self.assertEqual(sorted(created), ["context:board", "status:todo"])

    def test_a_rerun_after_a_failure_partway_creates_no_duplicate(self):
        self.backlog(ticket("PROJ-1"), ticket("PROJ-2"), ticket("PROJ-3"))
        self.update(fail_create_at=2)
        self.commit()
        self.assertEqual(self.run_script().returncode, 1)
        self.assertEqual(len(self.issues()), 1)
        self.update(fail_create_at=None)
        self.assertEqual(self.run_script().returncode, 0, self.result.stderr)
        self.assertEqual(sorted(i["body"].splitlines()[-1] for i in self.issues().values()),
                         [marker("PROJ-1"), marker("PROJ-2"), marker("PROJ-3")])

    def test_a_finished_migration_rerun_creates_nothing(self):
        self.backlog(ticket("PROJ-1"), ticket("PROJ-2"))
        self.migrated()
        before = self.load()["calls"]
        self.migrated()
        creates = [c for c in self.load()["calls"][len(before):] if c[:2] == ["issue", "create"]]
        self.assertEqual(creates, [])

    def test_a_closed_issue_counts_as_already_migrated(self):
        self.backlog(ticket("PROJ-1", status="done"))
        self.given_issue(41, "old\n\n" + marker("PROJ-1"), state="CLOSED", reason="COMPLETED")
        self.migrated()
        self.assertEqual(len(self.issues()), 1)

    def test_an_old_id_carried_by_two_issues_is_refused_before_any_write(self):
        self.backlog(ticket("PROJ-1"))
        self.given_issue(41, "a\n\n" + marker("PROJ-1"))
        self.given_issue(42, "b\n\n" + marker("PROJ-1"))
        self.refused(why="PROJ-1 is carried by several issues (#41, #42)")

    def test_a_marker_quoted_mid_body_is_not_an_old_id(self):
        self.backlog(ticket("PROJ-1"))
        self.given_issue(41, marker("PROJ-1") + "\n\nand more text after it")
        self.migrated()
        self.assertEqual(len(self.issues()), 2)
