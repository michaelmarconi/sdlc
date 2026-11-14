"""Tests for hand_over.py, run against throwaway git repositories made in each test."""

import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_over  # noqa: E402
import build_relay  # noqa: E402
import uncommitted  # noqa: E402

PLAN = "docs/plans/2026-11-03-thing.md"
TODAY = "2026-11-10"  # the script's "today" in these tests; never read from the clock

ENV = dict(os.environ, GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.com",
           GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.com",
           GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


def plan(status="🟢 Ready to build", date="2026-11-04"):
    dated = f"date: {date}\n" if date else ""
    return f"---\nstatus: {status}\n{dated}---\n\n# Thing\n\n## Plan\n\nDo the thing.\n"


class Repo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = os.path.join(self.tmp.name, "repo")
        os.makedirs(self.dir)
        self.git("init", "-q", "-b", "main")
        self.put(PLAN, plan())
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "Start")
        self.bare = self.add_origin()
        self.git("push", "-q", "origin", "main")
        self.git("remote", "set-head", "origin", "main")
        self.git("checkout", "-q", "-b", "build/thing")
        self.old_env = dict(os.environ)
        os.environ.update(ENV)
        self.addCleanup(os.environ.clear)
        self.addCleanup(os.environ.update, self.old_env)
        today = mock.patch.object(hand_over, "today", return_value=TODAY)
        today.start()
        self.addCleanup(today.stop)

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.dir, env=ENV, check=True,
                              capture_output=True, text=True).stdout.strip()

    def put(self, path, text):
        full = os.path.join(self.dir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)

    def read(self, path):
        with open(os.path.join(self.dir, path), encoding="utf-8") as f:
            return f.read()

    def add_origin(self):
        bare = os.path.join(self.tmp.name, "origin.git")
        self.git("init", "-q", "--bare", bare, cwd=self.tmp.name)
        self.git("remote", "add", "origin", bare)
        return bare

    def run_it(self, *args, own=""):
        out = io.StringIO()
        self.data = os.path.join(self.tmp.name, "data")
        with redirect_stdout(out), mock.patch("sys.stdin", io.StringIO(own)):
            code = hand_over.main(["--repo", self.dir, "--plan", PLAN, "--message", "Build the thing",
                                   "--data", self.data, "--session", "s1", "--report", "-", *args])
        return code, out.getvalue()

    def report_file(self, out):
        line = next(line for line in out.splitlines() if line.startswith("Report written: "))
        with open(line[len("Report written: "):], encoding="utf-8") as f:
            return line[len("Report written: "):], f.read()

    def subjects(self):
        return self.git("log", "--format=%s").splitlines()


class Commit(Repo):
    def test_work_committed_with_the_message(self):
        self.put("src/thing.py", "print('thing')\n")
        code, out = self.run_it()
        self.assertEqual(code, 0)
        self.assertEqual(self.subjects()[0], "Build the thing")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertIn("build/thing", out)

    def test_nothing_to_commit_said_so(self):
        code, out = self.run_it()
        self.assertEqual(code, 0)
        self.assertEqual(self.subjects(), ["Start"])
        self.assertIn("nothing new to commit", out)

    def test_sandbox_stand_ins_left_out_of_the_commit(self):
        # Git can't add the sandbox's stand-ins, and one failing file stops `git add -A` adding
        # anything. Ordinary files stand in for them here, as in test_uncommitted.py.
        self.put(".bashrc", "")
        self.put(".claude/settings.json", "")
        self.put("src/thing.py", "print('thing')\n")
        stand_ins = {os.path.join(self.dir, ".bashrc"), os.path.join(self.dir, ".claude/settings.json")}
        null = os.stat(os.devnull)
        fake = type("Stat", (), {"st_mode": stat.S_IFCHR | 0o666, "st_rdev": null.st_rdev})
        real = uncommitted.lstat_of
        with mock.patch.object(uncommitted, "lstat_of", lambda p: fake if p in stand_ins else real(p)):
            code, out = self.run_it()
        self.assertEqual(code, 0)
        self.assertEqual(self.subjects()[0], "Build the thing")
        self.assertEqual(self.git("show", "--name-only", "--format=", "HEAD"), "src/thing.py")

    def test_failed_add_reported(self):
        self.put("src/thing.py", "print('thing')\n")
        failing = subprocess.CompletedProcess([], 128, "", "fatal: adding files failed")
        real = hand_over.git
        with mock.patch.object(hand_over, "git", lambda repo, *a: failing if a[0] == "add" else real(repo, *a)):
            code, out = self.run_it()
        self.assertEqual(code, 1)
        self.assertEqual(self.subjects(), ["Start"])
        self.assertIn("fatal: adding files failed", out)

    def test_refused_on_the_default_branch(self):
        self.git("checkout", "-q", "main")
        self.put("src/thing.py", "print('thing')\n")
        code, out = self.run_it()
        self.assertEqual(code, 2)
        self.assertEqual(self.subjects(), ["Start"])
        self.assertIn("default branch", out)

    def test_refused_on_the_remote_default_branch(self):
        self.git("checkout", "-q", "-b", "trunk")
        self.git("push", "-q", "origin", "trunk")
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
        code, out = self.run_it()
        self.assertEqual(code, 2)
        self.assertIn("trunk", out)

    def test_refused_without_a_branch(self):
        self.git("checkout", "-q", "--detach")
        code, out = self.run_it()
        self.assertEqual(code, 2)
        self.assertIn("branch", out)


class Built(Repo):
    def test_reviews_passed_marks_the_plan_built(self):
        self.put("src/thing.py", "print('thing')\n")
        code, out = self.run_it("--reviews-passed")
        self.assertEqual(code, 0)
        self.assertIn("status: ✅ Built\n", self.read(PLAN))
        self.assertEqual(self.subjects()[:2], ["Mark the plan 2026-11-03-thing.md as built", "Build the thing"])
        self.assertIn("✅ Built", out)

    def test_plan_left_ready_without_passing_reviews(self):
        code, out = self.run_it()
        self.assertEqual(code, 0)
        self.assertIn("status: 🟢 Ready to build\n", self.read(PLAN))
        self.assertIn("🟢 Ready to build", out)

    def test_draft_plan_without_passing_reviews_says_it_is_not_ready(self):
        self.put(PLAN, plan("📝 Draft"))
        code, out = self.run_it()
        self.assertEqual(code, 0)
        self.assertIn("status: 📝 Draft\n", self.read(PLAN))
        self.assertIn("stays `📝 Draft`, because it is not `🟢 Ready to build`", out)
        self.assertNotIn("reviews have not all passed", out)

    def test_only_a_ready_plan_is_marked_built(self):
        self.put(PLAN, plan("📝 Draft"))
        code, out = self.run_it("--reviews-passed")
        self.assertEqual(code, 1)
        self.assertIn("status: 📝 Draft\n", self.read(PLAN))
        self.assertIn("📝 Draft", out)

    def test_ready_written_before_the_emoji_counts(self):
        self.put(PLAN, plan("Ready to build"))
        code, _ = self.run_it("--reviews-passed")
        self.assertEqual(code, 0)
        self.assertIn("status: ✅ Built\n", self.read(PLAN))

    def test_only_the_status_and_date_lines_change(self):
        before = self.read(PLAN)
        self.run_it("--reviews-passed")
        self.assertEqual(self.read(PLAN), before.replace("🟢 Ready to build", "✅ Built").replace(
            "date: 2026-11-04", f"date: {TODAY}"))

    def test_built_plan_dated_today(self):
        self.run_it("--reviews-passed")
        self.assertIn(f"status: ✅ Built\ndate: {TODAY}\n", self.read(PLAN))

    def test_plan_from_before_dates_gains_todays_date_under_its_status(self):
        self.put(PLAN, plan(date=None))
        code, _ = self.run_it("--reviews-passed")
        self.assertEqual(code, 0)
        self.assertEqual(self.read(PLAN), plan("✅ Built", date=TODAY))

    def test_date_with_a_comment_keeps_it(self):
        self.put(PLAN, plan(date="2026-11-04  # status day"))
        self.run_it("--reviews-passed")
        self.assertIn(f"date: {TODAY}  # status day\n", self.read(PLAN))

    def built_from(self, line):
        self.put(PLAN, plan(date=None).replace("---\n\n#", f"{line}\n---\n\n#"))
        self.run_it("--reviews-passed")
        return self.read(PLAN)

    def test_date_key_in_another_case_replaced_not_doubled(self):
        text = self.built_from("Date: 2026-11-04")
        self.assertIn(f"Date: {TODAY}\n", text)
        self.assertEqual(text.lower().count("date"), 1)

    def test_date_key_with_a_space_replaced_not_doubled(self):
        text = self.built_from("date : 2026-11-04")
        self.assertIn(f"date : {TODAY}\n", text)
        self.assertEqual(text.lower().count("date"), 1)

    def test_date_left_alone_when_not_built(self):
        self.run_it()
        self.assertIn("date: 2026-11-04\n", self.read(PLAN))

    def test_date_outside_the_frontmatter_left_alone(self):
        self.put(PLAN, plan(date=None) + "\ndate: 2026-01-01\n")
        self.run_it("--reviews-passed")
        text = self.read(PLAN)
        self.assertIn(f"status: ✅ Built\ndate: {TODAY}\n", text)
        self.assertTrue(text.endswith("\ndate: 2026-01-01\n"))

    def test_missing_plan_refused(self):
        os.remove(os.path.join(self.dir, PLAN))
        code, out = self.run_it("--reviews-passed")
        self.assertEqual(code, 2)
        self.assertIn(PLAN, out)


class Push(Repo):
    def test_pushed_to_origin(self):
        bare = self.bare
        self.put("src/thing.py", "print('thing')\n")
        code, out = self.run_it("--reviews-passed")
        self.assertEqual(code, 0)
        self.assertEqual(self.git("rev-parse", "build/thing", cwd=bare), self.git("rev-parse", "HEAD"))
        self.assertIn("pushed", out)

    def test_refused_without_an_origin(self):
        self.git("remote", "remove", "origin")
        self.put("src/thing.py", "print('thing')\n")
        code, out = self.run_it("--reviews-passed")
        self.assertEqual(code, 2)
        self.assertEqual(self.subjects(), ["Start"])
        self.assertIn("status: 🟢 Ready to build\n", self.read(PLAN))
        self.assertIn("no remote named `origin`", out)

    def test_refused_without_the_remote_default_branch(self):
        self.git("symbolic-ref", "--delete", "refs/remotes/origin/HEAD")
        code, out = self.run_it()
        self.assertEqual(code, 2)
        self.assertEqual(self.subjects(), ["Start"])
        self.assertIn("git remote set-head origin -a", out)

    def test_failed_push_reported(self):
        self.git("remote", "set-url", "origin", os.path.join(self.tmp.name, "missing.git"))
        self.put("src/thing.py", "print('thing')\n")
        code, out = self.run_it()
        self.assertEqual(code, 1)
        self.assertEqual(self.subjects()[0], "Build the thing")
        self.assertIn("push failed", out)


class Report(Repo):
    """The build's report file (ADRs 0033 and 0034)."""

    def keep(self, plan_path, reports):
        record = {"commit": "abc", "repository": self.dir, "plan": plan_path, "reports": reports, "started": {}}
        path = build_relay.record_path("s1", os.path.join(self.tmp.name, "data"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f)

    def test_own_sections_and_script_output_written(self):
        code, out = self.run_it(own="## What was built\n\nThe thing.\n\n## Choices\n\n- Named it thing.\n")
        self.assertEqual(code, 0, out)
        path, text = self.report_file(out)
        self.assertTrue(path.endswith(f"reports/repo/{TODAY}-build-2026-11-03-thing.md"), path)
        self.assertIn("## What was built\n\nThe thing.", text)
        script = text[text.index("## The hand-over script's report"):text.index("## Left for you to check")]
        self.assertIn("Branch: build/thing", script)
        self.assertIn("Push: pushed build/thing to origin.", script)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_kept_reviews_copied_word_for_word(self):
        reports = {"code": '[{"summary": "x"}]', "security": "No issues.\n", "plan": "Result: PASS\n| 1 | pass |",
                   "check": "Result: PASS"}
        self.keep(os.path.realpath(os.path.join(self.dir, PLAN)), reports)
        _, out = self.run_it()
        _, text = self.report_file(out)
        reviews = text[text.index("## What each review found"):text.index("## The hand-over script's report")]
        for title, part in (("Code review", "code"), ("Security review", "security"),
                            ("Build review", "plan"), ("Correction check", "check")):
            self.assertIn(f"### {title}\n\n{reports[part]}", reviews)

    def test_another_plans_reviews_not_copied(self):
        self.keep(os.path.realpath(os.path.join(self.dir, "docs/plans/other.md")), {"code": "theirs"})
        _, out = self.run_it()
        _, text = self.report_file(out)
        self.assertNotIn("theirs", text)
        self.assertIn("No report kept.", text)

    def test_missing_check_says_no_report_kept(self):
        self.keep(os.path.realpath(os.path.join(self.dir, PLAN)), {"code": "c", "security": "s", "plan": "p"})
        _, out = self.run_it()
        _, text = self.report_file(out)
        self.assertIn("### Correction check\n\nNo report kept.", text)

    def test_refused_hand_over_still_writes_the_file(self):
        self.git("checkout", "-q", "main")
        code, out = self.run_it(own="## What was built\n\nNothing: refused.\n")
        self.assertEqual(code, 2)
        _, text = self.report_file(out)
        self.assertIn("Refused:", text)

    def test_unknown_heading_refused_before_any_git_step(self):
        self.put("work.txt", "new")
        code, out = self.run_it(own="## My own heading\n\ntext\n")
        self.assertEqual(code, 2)
        self.assertIn("My own heading", out)
        self.assertNotIn("Report written", out)
        self.assertIn("work.txt", self.git("status", "--porcelain"))

    def test_claude_cannot_write_the_script_report(self):
        code, out = self.run_it(own="## The hand-over script's report\n\nAll pushed.\n")
        self.assertEqual(code, 2)


class Help(unittest.TestCase):
    def test_help(self):
        result = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_over.py"), "--help"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--reviews-passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
