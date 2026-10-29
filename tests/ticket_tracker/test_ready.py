import unittest

from support import SECTIONS, TrackerCase, issue

TODO = ["status:todo", "type:feature", "context:board"]
UNANALYSED = "_Not analysed yet — `/ticket refine`._"


def with_section(name, text, body=SECTIONS):
    import re
    return re.sub(r"(## %s\n\n).*?(\n\n## |\n*\Z)" % name, lambda m: m.group(1) + text + m.group(2), body,
                  count=1, flags=re.S)


class RefineStartAndDesignKeepTheirRefusals(TrackerCase):
    def test_refine_refuses_anything_not_a_draft_and_says_what_it_is_instead(self):
        self.given(issue(70, labels=TODO))
        self.refused("ready", "70", "refine", why="#70 is todo, not draft")

    def test_refine_accepts_a_draft(self):
        self.given(issue(71))
        self.assertEqual(self.ok("ready", "71", "refine")["status"], "draft")

    def test_start_refuses_a_draft_and_names_refine(self):
        self.given(issue(72))
        self.refused("ready", "72", "start", why="#72 is a draft; run /ticket refine 72 first")

    def test_start_refuses_a_todo_whose_model_decision_is_still_the_unanalysed_marker(self):
        self.given(issue(73, labels=TODO, body=with_section("Model decision", UNANALYSED)))
        self.refused("ready", "73", "start", why="#73 has no Model decision")

    def test_start_refuses_a_todo_whose_model_decision_section_is_absent(self):
        self.given(issue(74, labels=TODO, body="## Acceptance criteria\n\n- [ ] a\n"))
        self.refused("ready", "74", "start", why="#74 has no Model decision")

    def test_start_refuses_a_todo_whose_model_decision_is_empty(self):
        self.given(issue(75, labels=TODO, body=with_section("Model decision", "")))
        self.refused("ready", "75", "start", why="#75 has no Model decision")

    def test_start_refuses_a_frontend_ticket_whose_design_direction_is_the_unanalysed_marker(self):
        body = with_section("Design direction", UNANALYSED).replace("it works", "a screen under `frontend/src`")
        self.given(issue(76, labels=TODO, body=body))
        self.refused("ready", "76", "start", why="#76 touches frontend/** and has no Design direction")

    def test_start_refuses_a_frontend_ticket_with_no_design_direction_section(self):
        body = "## Acceptance criteria\n\n- [ ] edits frontend/src\n\n## Model decision\n\nOn board.\n"
        self.given(issue(77, labels=TODO, body=body))
        self.refused("ready", "77", "start", why="#77 touches frontend/** and has no Design direction")

    def test_start_accepts_a_frontend_ticket_whose_design_direction_is_na(self):
        body = SECTIONS.replace("it works", "edits frontend/src")
        self.given(issue(78, labels=TODO, body=body))
        self.assertEqual(self.ok("ready", "78", "start")["status"], "todo")

    def test_start_accepts_a_refined_backend_ticket(self):
        self.given(issue(79, labels=TODO))
        self.assertEqual(self.ok("ready", "79", "start")["number"], 79)

    def test_start_refuses_a_done_ticket(self):
        self.given(issue(80, state="CLOSED", reason="COMPLETED"))
        self.refused("ready", "80", "start", why="#80 is done")

    def test_design_refuses_a_ticket_that_is_not_in_progress(self):
        self.given(issue(81, labels=TODO, body=SECTIONS.replace("it works", "frontend/src")))
        self.refused("ready", "81", "design", why="#81 is todo, not in-progress")

    def test_design_refuses_a_ticket_that_does_not_touch_the_frontend(self):
        self.given(issue(82, labels=["status:in-progress", "type:feature", "context:board"]))
        self.refused("ready", "82", "design", why="#82 does not touch frontend/**")

    def test_design_accepts_an_in_progress_frontend_ticket(self):
        body = SECTIONS.replace("it works", "frontend/src")
        self.given(issue(83, labels=["status:in-progress", "type:feature", "context:board"], body=body))
        self.assertEqual(self.ok("ready", "83", "design")["status"], "in-progress")

    def test_an_unreadable_ticket_is_refused_by_every_verb_with_the_reason(self):
        self.given(issue(84, labels=["status:todo", "type:feature"]))
        for verb in ("refine", "start", "design"):
            with self.subTest(verb=verb):
                self.refused("ready", "84", verb, why="#84 is unreadable: no context: label")


if __name__ == "__main__":
    unittest.main()
