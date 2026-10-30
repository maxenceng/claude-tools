import json
import os
import unittest

from support import TrackerCase, issue

TODO = ["status:in-progress", "type:feature", "context:board"]
READ_AT = "2026-10-28T09:00:00Z"


class Branching(TrackerCase):
    def test_start_branches_with_gh_issue_develop_and_returns_the_branch(self):
        self.given(issue(90, title="Show the board", labels=TODO))
        made = self.ok("develop", "90")
        self.assertEqual(made["branch"], "90-show-the-board")
        self.assertEqual(self.writes(), [["issue", "develop", "90"]])

    def test_checkout_is_passed_through(self):
        self.given(issue(91, title="x", labels=TODO))
        self.ok("develop", "91", "--checkout")
        self.assertEqual(self.writes(), [["issue", "develop", "91", "--checkout"]])

    def test_a_branch_gh_already_linked_is_returned_and_no_second_one_is_made(self):
        self.given(issue(92, labels=TODO, branches=["92-old"]))
        made = self.ok("develop", "92")
        self.assertEqual(made["branch"], "92-old")
        self.assertEqual(made["existing"], True)
        self.assertEqual(self.writes(), [])

    def test_a_branch_that_already_existed_says_it_was_not_checked_out(self):
        self.given(issue(89, labels=TODO, branches=["89-old"]))
        made = self.ok("develop", "89", "--checkout")
        self.assertEqual((made["existing"], made["checkedOut"]), (True, False))

    def test_a_new_branch_says_whether_it_was_checked_out(self):
        self.given(issue(88, title="x", labels=TODO))
        self.assertEqual(self.ok("develop", "88", "--checkout")["checkedOut"], True)

    def test_an_unreadable_ticket_gets_no_branch(self):
        self.given(issue(93, labels=["status:todo"]))
        self.refused("develop", "93", why="#93 is unreadable")
        self.assertEqual(self.writes(), [])


class OpeningAPullRequest(TrackerCase):
    def body(self, text):
        path = os.path.join(self.dir, "body.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def test_a_review_pr_closes_its_issue_with_a_keyword_in_the_body(self):
        self.given(issue(94, labels=TODO))
        self.ok("pr-create", "--title", "Show the board", "--body-file", self.body("Summary"), "--closes", "94")
        pr = self.load()["prs"][0]
        self.assertTrue(pr["body"].rstrip().endswith("Closes #94"), pr["body"])
        self.assertEqual(pr["title"], "Show the board")

    def test_a_body_that_already_closes_the_issue_gains_no_second_keyword(self):
        self.given(issue(95, labels=TODO))
        self.ok("pr-create", "--title", "t", "--body-file", self.body("Summary\n\nCloses #95\n"), "--closes", "95")
        self.assertEqual(self.load()["prs"][0]["body"].count("Closes #95"), 1)

    def test_a_close_out_pr_refs_the_issue_and_closes_nothing(self):
        self.given(issue(96, state="CLOSED", reason="COMPLETED"))
        self.ok("pr-create", "--title", "t", "--body-file", self.body("Atlas"), "--refs", "96")
        body = self.load()["prs"][0]["body"]
        self.assertIn("Refs #96", body)
        self.assertNotIn("Closes", body)

    def test_a_close_out_body_that_closes_by_issue_url_is_refused(self):
        self.given(issue(87, state="CLOSED", reason="COMPLETED"))
        body = self.body("Fixes https://github.com/o/r/issues/12\n")
        self.refused("pr-create", "--title", "t", "--body-file", body, "--refs", "87", why="carries a closing keyword")
        self.assertEqual(self.writes(), [])

    def test_a_keyword_closing_a_longer_number_does_not_stand_in_for_this_one(self):
        self.given(issue(5, labels=TODO))
        self.ok("pr-create", "--title", "t", "--body-file", self.body("Summary\n\nCloses #50\n"), "--closes", "5")
        self.assertRegex(self.load()["prs"][0]["body"], r"(?m)^Closes #5$")

    def test_a_close_out_body_that_carries_a_closing_keyword_is_refused(self):
        self.given(issue(97, state="CLOSED", reason="COMPLETED"))
        self.refused("pr-create", "--title", "t", "--body-file", self.body("Closes #97"), "--refs", "97",
                     why="closes nothing")
        self.assertEqual(self.load()["prs"], [])

    def test_a_pr_must_say_whether_it_closes_or_refs(self):
        self.given(issue(98, labels=TODO))
        self.refused("pr-create", "--title", "t", "--body-file", self.body("x"), why="--closes", code=2)

    def test_a_pr_never_closes_a_map(self):
        self.given(issue(99, labels=["status:in-progress", "type:map", "context:cross-context"]))
        self.refused("pr-create", "--title", "t", "--body-file", self.body("x"), "--closes", "99",
                     why="a map is closed by hand")
        self.assertEqual(self.load()["prs"], [])

    def test_a_pr_for_an_unreadable_ticket_is_refused(self):
        self.given(issue(100, labels=["status:todo"]))
        self.refused("pr-create", "--title", "t", "--body-file", self.body("x"), "--closes", "100",
                     why="#100 is unreadable")


class Feedback(TrackerCase):
    GRAPHQL = {"data": {"repository": {"pullRequest": {
        "body": "Summary",
        "reviewThreads": {"nodes": [
            {"isResolved": False, "path": "a.py", "line": 3, "comments": {"nodes": [
                {"databaseId": 11, "author": {"login": "rev"}, "body": "rename",
                 "diffHunk": "@@ -1 +1 @@\n context\n+added"}]}},
            {"isResolved": True, "path": "b.py", "line": 4, "comments": {"nodes": [
                {"databaseId": 12, "author": {"login": "rev"}, "body": "done", "diffHunk": "x"}]}}]},
        "comments": {"nodes": [{"author": {"login": "rev"}, "body": "top level"}]},
        "reviews": {"nodes": [{"author": {"login": "rev"}, "state": "COMMENTED", "body": ""},
                              {"author": {"login": "rev"}, "state": "COMMENTED", "body": "summary"}]},
        "commits": {"nodes": [{"commit": {"statusCheckRollup": {"state": "FAILURE"}}}]}}}}}

    def test_feedback_keeps_unresolved_threads_non_empty_reviews_and_the_ci_state(self):
        self.update(graphql=self.GRAPHQL)
        got = self.ok("pr-feedback", "7")
        self.assertEqual(got["ci"], "FAILURE")
        self.assertEqual([t["path"] for t in got["threads"]], ["a.py"])
        self.assertEqual(got["threads"][0]["anchor"], "+added")
        self.assertEqual(got["threads"][0]["comments"], [{"databaseId": 11, "author": {"login": "rev"}, "body": "rename"}])
        self.assertEqual([r["body"] for r in got["reviews"]], ["summary"])
        self.assertEqual(got["comments"][0]["body"], "top level")
        self.assertEqual(got["body"], "Summary")

    def test_a_reply_goes_to_the_thread_s_first_comment(self):
        path = os.path.join(self.dir, "reply.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("Fixed: renamed")
        self.ok("pr-reply", "7", "11", "--body-file", path)
        self.assertEqual(self.load()["replies"], [{"pr": "7", "comment": "11", "body": "body=Fixed: renamed"}])


class WritingAPullRequestSection(TrackerCase):
    BODY = "## Summary\n\nIt works.\n\n## Open\n\n- **A title.** Keep it?\n\nCloses #77\n"

    def given_pr(self, body=BODY, at=READ_AT):
        self.update(pull_requests={"7": {"number": 7, "body": body, "updatedAt": at}})

    def put(self, sections, at=READ_AT):
        return self.run_tracker("pr-write-sections", "7", "--expect-updated-at", at, stdin=json.dumps(sections))

    def test_a_write_replaces_only_that_section_and_keeps_the_closing_keyword(self):
        self.given_pr()
        done = self.put({"Summary": "It still works."})
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.load()["pull_requests"]["7"]["body"],
                         self.BODY.replace("It works.", "It still works."))

    def test_a_null_drops_the_section_and_a_new_one_is_added(self):
        self.given_pr()
        self.put({"Open": None, "Decided": "- **A title.** Kept."})
        self.assertEqual(self.load()["pull_requests"]["7"]["body"],
                         "## Summary\n\nIt works.\n\n## Decided\n\n- **A title.** Kept.\n\nCloses #77\n")

    def test_a_write_reports_the_updated_at_to_expect_next(self):
        self.given_pr()
        written = json.loads(self.put({"Summary": "a"}).stdout)
        self.assertEqual(written, {"pr": 7, "updatedAt": self.load()["pull_requests"]["7"]["updatedAt"]})

    def test_a_write_refuses_and_changes_nothing_when_the_pull_request_moved_since_it_was_read(self):
        self.given_pr(at="2026-10-28T09:30:00Z")
        self.refused("pr-write-sections", "7", "--expect-updated-at", READ_AT,
                     stdin=json.dumps({"Open": None}), why="pull request #7 changed since it was read")
        self.assertEqual(self.writes(), [])
        self.assertEqual(self.load()["pull_requests"]["7"]["body"], self.BODY)

    def test_a_write_that_would_drop_the_closing_keyword_is_refused(self):
        self.given_pr(body="## Summary\n\nCloses #77 once it works.\n\n## Notes\n\nx\n")
        self.refused("pr-write-sections", "7", "--expect-updated-at", READ_AT,
                     stdin=json.dumps({"Summary": None}), why="drops its closing keyword")
        self.assertEqual(self.writes(), [])

    def test_feedback_carries_the_updated_at_a_section_write_expects(self):
        graphql = json.loads(json.dumps(Feedback.GRAPHQL))
        graphql["data"]["repository"]["pullRequest"]["updatedAt"] = READ_AT
        self.update(graphql=graphql)
        self.assertEqual(self.ok("pr-feedback", "7")["updatedAt"], READ_AT)


if __name__ == "__main__":
    unittest.main()
