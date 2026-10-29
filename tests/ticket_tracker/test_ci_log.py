import unittest

from support import TrackerCase


class CiLog(TrackerCase):
    def test_the_log_is_the_failed_steps_of_each_red_run_and_nothing_green(self):
        self.update(checks=[{"name": "build", "bucket": "fail", "link": "https://github.com/o/r/actions/runs/41/job/1"},
                            {"name": "lint", "bucket": "fail", "link": "https://github.com/o/r/actions/runs/41/job/2"},
                            {"name": "plugin", "bucket": "pass", "link": "https://github.com/o/r/actions/runs/42/job/3"}],
                    run_logs={"41": "build\tTest\tFAILED SomeTest"})
        got = self.ok("ci-log", "7")
        self.assertEqual(got["failed"], ["build", "lint"])
        self.assertEqual(got["logs"], [{"run": 41, "log": "build\tTest\tFAILED SomeTest\n"}])
        self.assertIn(["run", "view", "41", "--log-failed"], self.load()["calls"])

    def test_green_checks_read_no_log(self):
        self.update(checks=[{"name": "build", "bucket": "pass", "link": "https://github.com/o/r/actions/runs/43/job/1"}])
        self.assertEqual(self.ok("ci-log", "7")["logs"], [])


if __name__ == "__main__":
    unittest.main()
