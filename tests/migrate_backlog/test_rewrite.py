from support import MigrationCase, ticket

BLOB = "https://github.com/o/r/blob/main/"


class RewriteTest(MigrationCase):
    def body_after(self, text, extra=()):
        self.backlog(ticket("PROJ-1", body=text), ticket("PROJ-2"), ticket("PROJ-10"), *extra)
        self.write("docs/adr/0001-x.md", "# adr\n")
        self.write("docs/guide/index.md", "# guide\n")
        self.write("src/Main.java", "class Main {}\n")
        self.migrated()
        return self.by_old_id("PROJ-1")["body"]

    def number(self, id):
        return self.by_old_id(id)["number"]

    def test_a_link_whose_text_is_the_id_becomes_a_bare_reference(self):
        body = self.body_after("see [PROJ-2](PROJ-2-slug.md) now\n")
        self.assertIn("see #%d now" % self.number("PROJ-2"), body)

    def test_a_link_with_other_text_keeps_the_text_and_adds_the_reference(self):
        body = self.body_after("see [the map](../backlog/PROJ-2-slug.md#notes) now\n")
        self.assertIn("see the map (#%d) now" % self.number("PROJ-2"), body)

    def test_a_bare_id_becomes_a_reference(self):
        body = self.body_after("blocked by PROJ-2, and PROJ-2.\n")
        n = self.number("PROJ-2")
        self.assertIn("blocked by #%d, and #%d." % (n, n), body)

    def test_an_id_that_only_starts_another_id_is_not_rewritten(self):
        body = self.body_after("PROJ-10 and PROJ-1 and XPROJ-2 and PROJ-2x and PROJ-99\n")
        self.assertIn("#%d and #%d and XPROJ-2 and PROJ-2x and PROJ-99" % (self.number("PROJ-10"), self.number("PROJ-1")), body)

    def test_ids_in_inline_code_are_left_alone(self):
        body = self.body_after("run `PROJ-2` and ``PROJ-2 `x` [a](PROJ-2-slug.md)`` then PROJ-2\n")
        self.assertIn("run `PROJ-2` and ``PROJ-2 `x` [a](PROJ-2-slug.md)`` then #%d" % self.number("PROJ-2"), body)

    def test_ids_and_links_in_a_fenced_block_are_left_alone(self):
        text = "before PROJ-2\n\n```\nPROJ-2 [a](PROJ-2-slug.md)\n```\n\n~~~md\nPROJ-2\n~~~\n\nafter PROJ-2\n"
        body = self.body_after(text)
        n = self.number("PROJ-2")
        self.assertIn("before #%d\n\n```\nPROJ-2 [a](PROJ-2-slug.md)\n```\n\n~~~md\nPROJ-2\n~~~\n\nafter #%d" % (n, n), body)

    def test_a_link_into_the_repository_becomes_a_blob_url_on_main(self):
        body = self.body_after("[adr](../adr/0001-x.md#why) and [code](../../src/Main.java)\n")
        self.assertIn("[adr](%sdocs/adr/0001-x.md#why)" % BLOB, body)
        self.assertIn("[code](%ssrc/Main.java)" % BLOB, body)

    def test_a_link_to_a_directory_becomes_a_tree_url_on_main(self):
        body = self.body_after("[guide](../guide/)\n")
        self.assertIn("[guide](https://github.com/o/r/tree/main/docs/guide)", body)

    def test_a_link_to_a_file_that_is_not_a_ticket_in_the_backlog_becomes_a_blob_url(self):
        self.write("docs/backlog/README.md", "# readme\n")
        body = self.body_after("[readme](README.md)\n")
        self.assertIn("[readme](%sdocs/backlog/README.md)" % BLOB, body)

    def test_external_anchor_and_dangling_links_are_left_alone(self):
        text = "[a](https://example.com/PROJ-2) [b](#top) [c](../nowhere.md) [d](mailto:x@y.z)\n"
        self.assertIn(text, self.body_after(text))

    def test_a_reference_style_definition_is_rewritten_too(self):
        body = self.body_after("see [adr][1]\n\n[1]: ../adr/0001-x.md\n[2]: PROJ-2-slug.md\n")
        self.assertIn("[1]: %sdocs/adr/0001-x.md" % BLOB, body)
        self.assertIn("[2]: https://github.com/o/r/issues/%d" % self.number("PROJ-2"), body)

    def test_the_marker_line_survives_the_rewrite_as_the_last_line(self):
        body = self.body_after("see PROJ-2\n")
        self.assertEqual(body.splitlines()[-1], "Migrated from PROJ-1, created 2026-10-01.")

    def test_the_title_is_not_rewritten(self):
        self.backlog(ticket("PROJ-1", title="After PROJ-2"), ticket("PROJ-2"))
        self.migrated()
        self.assertEqual(self.by_old_id("PROJ-1")["title"], "After PROJ-2")

    def test_a_second_run_edits_no_body(self):
        self.body_after("see [PROJ-2](PROJ-2-slug.md) and [adr](../adr/0001-x.md)\n")
        before = len(self.load()["calls"])
        self.migrated()
        edits = [c for c in self.load()["calls"][before:] if c[:2] == ["issue", "edit"]]
        self.assertEqual(edits, [])
