from support import MigrationCase, ticket


class RefusalTest(MigrationCase):
    def test_an_in_progress_ticket_that_is_not_a_map_is_refused_with_its_file(self):
        self.backlog(ticket("PROJ-1", status="in-progress"))
        done = self.refused("--dry-run", why="docs/backlog/PROJ-1-slug.md")
        self.assertIn("in-progress", done.stderr)

    def test_an_in_review_ticket_that_is_not_a_map_is_refused(self):
        self.backlog(ticket("PROJ-1", status="in-review"))
        self.refused("--dry-run", why="in-review")

    def test_an_in_progress_map_is_accepted(self):
        self.backlog(ticket("PROJ-1", status="in-progress", type="map"))
        self.commit()
        self.assertEqual(self.run_script("--dry-run").returncode, 0, self.result.stderr)

    def test_a_refusal_also_stops_a_real_run(self):
        self.backlog(ticket("PROJ-1", status="in-review"))
        self.refused(why="in-review")

    def test_a_decision_reaching_no_map_is_refused(self):
        self.backlog(ticket("PROJ-1", type="decision", blocked_by=["PROJ-2"]), ticket("PROJ-2"))
        done = self.refused("--dry-run", why="docs/backlog/PROJ-1-slug.md")
        self.assertIn("no map", done.stderr)

    def test_a_decision_with_no_blocked_by_at_all_is_refused(self):
        self.backlog(ticket("PROJ-1", type="decision"))
        self.refused("--dry-run", why="no map")

    def test_a_decision_reaching_two_maps_is_refused(self):
        self.backlog(ticket("PROJ-1", type="map"), ticket("PROJ-2", type="map"),
                     ticket("PROJ-3", type="decision", blocked_by=["PROJ-1", "PROJ-2"]))
        done = self.refused("--dry-run", why="docs/backlog/PROJ-3-slug.md")
        self.assertIn("two maps", done.stderr)

    def test_a_decision_reaching_one_map_is_accepted(self):
        self.backlog(ticket("PROJ-1", type="map"), ticket("PROJ-3", type="decision", blocked_by=["PROJ-1"]))
        self.commit()
        self.assertEqual(self.run_script("--dry-run").returncode, 0, self.result.stderr)

    def test_a_blocked_by_naming_no_ticket_is_refused(self):
        self.backlog(ticket("PROJ-1", blocked_by=["PROJ-9"]))
        done = self.refused("--dry-run", why="PROJ-9")
        self.assertIn("docs/backlog/PROJ-1-slug.md", done.stderr)

    def test_a_file_without_frontmatter_is_unreadable(self):
        self.write("docs/backlog/PROJ-1-slug-less.md", "# Just a heading\n")
        self.refused("--dry-run", why="docs/backlog/PROJ-1-slug-less.md: unreadable: no frontmatter")

    def test_a_file_that_is_not_utf8_is_unreadable(self):
        self.write("docs/backlog/PROJ-1-binary.md", b"---\nid: PROJ-1\n\xff\xfe\n---\n")
        self.refused("--dry-run", why="docs/backlog/PROJ-1-binary.md: unreadable: not valid UTF-8")

    def test_a_ticket_without_a_heading_is_unreadable(self):
        self.write("docs/backlog/PROJ-1-slug.md", ticket("PROJ-1").replace("# A ticket", "A ticket"))
        self.refused("--dry-run", why="no `# ` heading")

    def test_an_unknown_status_is_unreadable(self):
        self.backlog(ticket("PROJ-1", status="blocked"))
        self.refused("--dry-run", why="unknown status blocked")

    def test_a_file_name_that_does_not_start_with_its_id_is_unreadable(self):
        self.write("docs/backlog/PROJ-2-slug.md", ticket("PROJ-1"))
        self.refused("--dry-run", why="id PROJ-1 is not the start of the file name")

    def test_every_refusal_is_reported_before_the_exit(self):
        self.backlog(ticket("PROJ-1", status="in-review"), ticket("PROJ-2", type="decision"))
        self.write("docs/backlog/PROJ-3-x.md", "oops")
        done = self.refused("--dry-run", why="PROJ-1-slug.md")
        self.assertIn("PROJ-2-slug.md", done.stderr)
        self.assertIn("PROJ-3-x.md", done.stderr)
        self.assertIn("3 refusal(s)", done.stderr)

    def test_the_readme_template_and_roadmap_are_not_tickets(self):
        self.backlog(ticket("PROJ-1"))
        for name in ("README", "_template", "ROADMAP"):
            self.write("docs/backlog/%s.md" % name, "# not a ticket\n")
        self.commit()
        self.assertEqual(self.run_script("--dry-run").returncode, 0, self.result.stderr)

    def test_a_roadmap_document_with_a_version_in_its_name_is_not_a_ticket(self):
        self.backlog(ticket("PROJ-1"))
        self.write("docs/backlog/ROADMAP-v1.1.md", "# Roadmap\n")
        self.commit()
        self.assertEqual(self.run_script("--dry-run").returncode, 0, self.result.stderr)

    def test_only_main_is_read_not_the_working_tree(self):
        self.backlog(ticket("PROJ-1"))
        self.commit()
        self.git("checkout", "-q", "-b", "PROJ-1-branch")
        self.backlog(ticket("PROJ-1", status="in-review"))
        self.assertEqual(self.run_script("--dry-run").returncode, 0, self.result.stderr)

    def test_a_decision_linked_from_two_map_bodies_is_refused_naming_both(self):
        self.backlog(ticket("PROJ-1", type="map", status="in-progress", body="See [d](PROJ-3-slug.md)\n"),
                     ticket("PROJ-2", type="map", status="in-progress", body="Decided: PROJ-3\n"),
                     ticket("PROJ-3", type="decision"))
        done = self.refused("--dry-run", why="docs/backlog/PROJ-3-slug.md")
        self.assertIn("two maps (PROJ-1, PROJ-2)", done.stderr)

    def test_a_decision_blocked_by_two_maps_is_refused_even_when_one_body_links_it(self):
        self.backlog(ticket("PROJ-1", type="map", status="in-progress", body="PROJ-3\n"),
                     ticket("PROJ-2", type="map", status="in-progress"),
                     ticket("PROJ-3", type="decision", blocked_by=["PROJ-1", "PROJ-2"]))
        self.refused("--dry-run", why="two maps (PROJ-1, PROJ-2)")

    def test_a_link_to_a_decision_inside_code_in_a_map_body_does_not_count(self):
        self.backlog(ticket("PROJ-1", type="map", status="in-progress", body="`PROJ-3`\n\n```\nPROJ-3\n```\n"),
                     ticket("PROJ-3", type="decision"))
        self.refused("--dry-run", why="reaches no map")
