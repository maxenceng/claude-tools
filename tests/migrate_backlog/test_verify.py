from support import MigrationCase, marker, ticket


class VerifyTest(MigrationCase):
    def setUp(self):
        super().setUp()
        self.backlog(ticket("PROJ-1", type="map", status="in-progress"), ticket("PROJ-2", status="done"),
                     ticket("PROJ-3", type="decision", blocked_by=["PROJ-1", "PROJ-2"]),
                     ticket("PROJ-4", status="draft", blocked_by=["PROJ-2"]))
        self.migrated()

    def number(self, id):
        return self.by_old_id(id)["number"]

    def tamper(self, id, change):
        state = self.load()
        change(state["issues"][str(self.number(id))], state)
        self.state = state
        self.save()

    def failing(self, *needles):
        done = self.run_script("verify")
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        for needle in needles:
            self.assertIn(needle, done.stdout)
        return done

    def test_a_faithful_migration_passes_and_says_so(self):
        done = self.run_script("verify")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("verify: ok, 4 tickets match 4 issues", done.stdout)

    def test_it_writes_nothing(self):
        before = len(self.load()["calls"])
        self.run_script("verify")
        self.assertEqual([c for c in self.load()["calls"][before:] if c[:2] in (["issue", "create"], ["issue", "edit"], ["issue", "close"], ["label", "create"]) or "-X" in c], [])

    def test_an_old_id_with_no_issue_is_named(self):
        state = self.load()
        del state["issues"][str(self.number("PROJ-4"))]
        self.state = state
        self.save()
        self.failing("FAIL PROJ-4: no issue carries 'Migrated from PROJ-4'")

    def test_an_old_id_with_several_issues_is_named(self):
        original = self.number("PROJ-4")
        self.given_issue(900, "dup\n\n" + marker("PROJ-4"))
        self.failing("FAIL PROJ-4: several issues carry its marker (#%d, #900)" % original)

    def test_a_done_ticket_whose_issue_is_open_is_named(self):
        self.tamper("PROJ-2", lambda i, s: i.update(state="OPEN", stateReason=None))
        self.failing("FAIL PROJ-2 (#%d): the file is done but the issue is open" % self.number("PROJ-2"))

    def test_a_done_ticket_closed_as_not_planned_is_named(self):
        self.tamper("PROJ-2", lambda i, s: i.update(stateReason="NOT_PLANNED"))
        self.failing("FAIL PROJ-2", "closed as NOT_PLANNED, not completed")

    def test_an_open_ticket_whose_issue_is_closed_is_named(self):
        self.tamper("PROJ-4", lambda i, s: i.update(state="CLOSED", stateReason="COMPLETED"))
        self.failing("FAIL PROJ-4 (#%d): the file is draft but the issue is closed" % self.number("PROJ-4"))

    def test_a_missing_label_is_named(self):
        self.tamper("PROJ-1", lambda i, s: i["labels"].remove("type:map"))
        self.failing("FAIL PROJ-1 (#%d): label type:map is missing" % self.number("PROJ-1"))

    def test_a_wrong_status_label_is_named_both_ways(self):
        self.tamper("PROJ-1", lambda i, s: i["labels"].__setitem__(i["labels"].index("status:in-progress"), "status:todo"))
        self.failing("label status:in-progress is missing", "label status:todo is extra")

    def test_a_status_label_on_a_draft_is_extra(self):
        self.tamper("PROJ-4", lambda i, s: i["labels"].append("status:todo"))
        self.failing("FAIL PROJ-4", "label status:todo is extra")

    def test_a_wrong_context_label_is_named(self):
        self.tamper("PROJ-2", lambda i, s: i["labels"].__setitem__(i["labels"].index("context:board"), "context:shell"))
        self.failing("FAIL PROJ-2", "label context:board is missing", "label context:shell is extra")

    def test_a_missing_dependency_is_named_with_both_tickets(self):
        self.tamper("PROJ-4", lambda i, s: i.pop("blocked_by"))
        self.failing("FAIL PROJ-4 (#%d): dependency on PROJ-2 (#%d) is missing" % (self.number("PROJ-4"), self.number("PROJ-2")))

    def test_an_extra_dependency_is_named(self):
        self.tamper("PROJ-4", lambda i, s: i["blocked_by"].append(self.number("PROJ-1")))
        self.failing("FAIL PROJ-4", "dependency on PROJ-1 (#%d) is extra" % self.number("PROJ-1"))

    def test_a_dependency_onto_a_map_is_extra_because_migration_drops_those(self):
        self.tamper("PROJ-3", lambda i, s: i["blocked_by"].append(self.number("PROJ-1")))
        self.failing("FAIL PROJ-3", "dependency on PROJ-1")

    def test_a_missing_sub_issue_is_named(self):
        self.tamper("PROJ-1", lambda i, s: i.pop("sub_issues"))
        self.failing("FAIL PROJ-1 (#%d): sub-issue PROJ-3 (#%d) is missing" % (self.number("PROJ-1"), self.number("PROJ-3")))

    def test_an_extra_sub_issue_is_named(self):
        self.tamper("PROJ-1", lambda i, s: i["sub_issues"].append(self.number("PROJ-4")))
        self.failing("FAIL PROJ-1", "sub-issue PROJ-4 (#%d) is extra" % self.number("PROJ-4"))

    def test_a_marked_issue_with_no_file_is_named(self):
        self.given_issue(901, "orphan\n\n" + marker("PROJ-77"))
        self.failing("FAIL #901: carries 'Migrated from PROJ-77' but docs/backlog has no file for PROJ-77")

    def test_every_problem_is_reported_with_a_count(self):
        self.tamper("PROJ-4", lambda i, s: i.pop("blocked_by"))
        self.tamper("PROJ-2", lambda i, s: i.update(state="OPEN", stateReason=None))
        done = self.failing("FAIL PROJ-4", "FAIL PROJ-2")
        self.assertIn("verify: FAILED, 2 problems", done.stdout)

    def test_a_file_that_cannot_be_read_fails_verify_too(self):
        self.write("docs/backlog/PROJ-9-bad.md", "no frontmatter")
        self.commit()
        done = self.run_script("verify")
        self.assertEqual(done.returncode, 1)
        self.assertIn("PROJ-9-bad.md: unreadable", done.stderr)

    def test_dry_run_with_verify_is_a_usage_error(self):
        self.assertEqual(self.run_script("verify", "--dry-run").returncode, 2)

    def test_a_sub_issue_derived_from_a_map_body_is_checked_too(self):
        self.write("docs/backlog/PROJ-5-slug.md", ticket("PROJ-5", type="decision"))
        self.write("docs/backlog/PROJ-1-slug.md", ticket("PROJ-1", type="map", status="in-progress", body="PROJ-5\n"))
        self.commit()
        self.run_script()
        self.assertEqual(self.run_script("verify").returncode, 0, self.result.stdout)
        state = self.load()
        state["issues"][str(self.number("PROJ-1"))].pop("sub_issues")
        self.state = state
        self.save()
        self.failing("sub-issue PROJ-5")
