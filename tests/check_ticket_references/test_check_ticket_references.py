import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "..", "..", "templates", "spring-ddd", "scripts", "check-ticket-references.py")


class TheTicketReferenceCheck(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        bin_dir = os.path.join(self.root, "..", os.path.basename(self.root) + "-bin")
        os.makedirs(bin_dir)
        self.addCleanup(shutil.rmtree, bin_dir)
        self.called = os.path.join(bin_dir, "called")
        gh = os.path.join(bin_dir, "gh")
        with open(gh, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\ntouch '%s'\nexit 1\n" % self.called)
        os.chmod(gh, os.stat(gh).st_mode | stat.S_IXUSR)
        self.bin = bin_dir
        self.put("src/main/java/Thing.java", "class Thing {}\n")

    def put(self, relative, text):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def run_check(self):
        env = dict(os.environ, CHECK_ROOT=self.root, PATH=self.bin + os.pathsep + os.environ["PATH"])
        return subprocess.run([sys.executable, CHECK], cwd=self.root, env=env, capture_output=True, text=True)

    def fails_on(self, relative, text, naming):
        self.put(relative, text)
        done = self.run_check()
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("%s:1: names %s" % (relative, naming), done.stdout)

    def test_a_bare_issue_number_in_a_living_document_fails(self):
        self.fails_on("README.md", "the type #42 will share\n", "#42")

    def test_a_bare_issue_number_in_code_fails(self):
        self.fails_on("src/main/java/Other.java", "// closes #7\nclass Other {}\n", "#7")

    def test_an_issue_url_fails_whatever_the_file_type(self):
        self.fails_on("frontend/src/App.tsx", "// https://github.com/o/r/issues/12\n", "https://github.com/o/r/issues/12")

    def test_an_issue_url_fails_in_a_workflow_a_makefile_and_a_build_file(self):
        for relative in (".github/workflows/ci.yml", "Makefile", "pom.xml"):
            with self.subTest(file=relative):
                self.fails_on(relative, "# https://github.com/o/r/issues/12\n", "https://github.com/o/r/issues/12")
                os.remove(os.path.join(self.root, relative))

    def test_a_bare_number_outside_java_and_markdown_is_a_comment_not_an_issue(self):
        self.put("Makefile", "# step #2 of the release\n")
        self.put(".github/workflows/ci.yml", "# job #3\n")
        done = self.run_check()
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_a_binary_file_is_skipped_rather_than_failing_the_scan(self):
        path = os.path.join(self.root, "frontend/public/logo.png")
        os.makedirs(os.path.dirname(path))
        with open(path, "wb") as handle:
            handle.write(b"\x89PNG\r\n\x1a\n\xff\xfe")
        done = self.run_check()
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_the_check_never_asks_github_whether_the_issue_is_open_or_closed(self):
        self.put("README.md", "#42\n")
        self.run_check()
        self.assertFalse(os.path.exists(self.called), "the check called gh")

    def test_the_record_may_name_issues(self):
        for relative in ("docs/adr/0001-x.md", "docs/research/note.md", "docs/endpoints/get.md", "scripts/check-x.py"):
            self.put(relative, "see #42 and https://github.com/o/r/issues/42\n")
        done = self.run_check()
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_a_hex_colour_in_a_stylesheet_or_a_frontend_source_does_not_trip_it(self):
        self.put("frontend/src/design-system/tokens.css", ":root { --accent: #123; --ink: #000; border: 1px solid #1a2; }\n")
        self.put("frontend/src/design-system/Swatch.tsx", "export const accent = '#456';\n")
        self.put("frontend/index.html", "<meta name=\"theme-color\" content=\"#789\">\n")
        done = self.run_check()
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_a_bare_number_in_java_fails_even_when_it_looks_like_a_hex_colour(self):
        self.fails_on("src/main/java/Colour.java", "// #123\nclass Colour {}\n", "#123")

    def test_a_markdown_anchor_and_an_html_entity_are_not_issue_numbers(self):
        self.put("README.md", "[see](#12-section) and &#35; and [x](docs/a.md#3-b)\n")
        done = self.run_check()
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_a_scan_that_matches_no_file_fails(self):
        shutil.rmtree(os.path.join(self.root, "src"))
        done = self.run_check()
        self.assertEqual(done.returncode, 1)
        self.assertIn("nothing was scanned", done.stdout)

    def test_a_tree_naming_no_issue_passes(self):
        self.put("README.md", "No ticket named here.\n")
        done = self.run_check()
        self.assertEqual(done.returncode, 0)
        self.assertIn("name no issue", done.stdout)


if __name__ == "__main__":
    unittest.main()
