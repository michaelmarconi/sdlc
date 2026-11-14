"""Tests for run_report.py, the shared code that writes a build's or an audit's report file."""

import os
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_report  # noqa: E402


class Names(unittest.TestCase):
    def test_safe_keeps_ordinary_names(self):
        self.assertEqual(run_report.safe("add-numbers"), "add-numbers")

    def test_safe_replaces_unsafe_characters(self):
        self.assertEqual(run_report.safe("last 7 days"), "last-7-days")
        self.assertEqual(run_report.safe("abc123..def456"), "abc123-def456")
        self.assertEqual(run_report.safe("../../etc/passwd"), "etc-passwd")
        self.assertEqual(run_report.safe("since a/b"), "since-a-b")

    def test_safe_never_empty(self):
        self.assertEqual(run_report.safe("../"), "report")
        self.assertEqual(run_report.safe(""), "report")


class Folder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.temp = os.path.join(self.tmp.name, "system-temp")
        os.makedirs(self.temp)
        patcher = mock.patch.object(run_report.tempfile, "gettempdir", return_value=self.temp)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_data_folder_used(self):
        data = os.path.join(self.tmp.name, "data")
        folder, fell_back = run_report.report_folder(data, "/work/my repo")
        self.assertEqual(folder, os.path.join(data, "reports", "my-repo"))
        self.assertFalse(fell_back)
        self.assertTrue(os.path.isdir(folder))

    def test_empty_data_falls_back_to_private_folder(self):
        folder, fell_back = run_report.report_folder("", "/work/repo")
        root = os.path.join(self.temp, f"agentic-reports-{os.getuid()}")
        self.assertEqual(folder, os.path.join(root, "repo"))
        self.assertTrue(fell_back)
        self.assertEqual(stat.S_IMODE(os.stat(root).st_mode) & 0o077, 0)

    def test_unwritable_data_falls_back(self):
        data = os.path.join(self.tmp.name, "data")
        with mock.patch.object(run_report, "writable", side_effect=lambda f: not f.startswith(data)):
            folder, fell_back = run_report.report_folder(data, "/work/repo")
        self.assertTrue(fell_back)
        self.assertTrue(folder.startswith(self.temp))

    def test_fallback_others_can_open_is_refused(self):
        root = os.path.join(self.temp, f"agentic-reports-{os.getuid()}")
        os.makedirs(root)
        os.chmod(root, 0o755)
        with self.assertRaises(run_report.ReportError):
            run_report.report_folder("", "/work/repo")

    def test_fallback_symlink_is_refused(self):
        root = os.path.join(self.temp, f"agentic-reports-{os.getuid()}")
        elsewhere = os.path.join(self.tmp.name, "elsewhere")
        os.makedirs(elsewhere, mode=0o700)
        os.symlink(elsewhere, root)
        with self.assertRaises(run_report.ReportError):
            run_report.report_folder("", "/work/repo")


class Parse(unittest.TestCase):
    def test_sections_by_heading(self):
        text = "## What was built\n\nAn adder.\n\n## Choices\n\n- Named it add.\n"
        own = run_report.parse("build", text)
        self.assertEqual(own, {"What was built": "An adder.", "Choices": "- Named it add."})

    def test_unknown_heading_refused(self):
        with self.assertRaises(run_report.ReportError) as caught:
            run_report.parse("build", "## Something else\n\ntext\n")
        self.assertIn("Something else", str(caught.exception))

    def test_copied_heading_refused(self):
        with self.assertRaises(run_report.ReportError):
            run_report.parse("build", "## The hand-over script's report\n\nmy version\n")

    def test_repeated_heading_refused(self):
        with self.assertRaises(run_report.ReportError):
            run_report.parse("build", "## Choices\n\na\n\n## Choices\n\nb\n")

    def test_text_before_first_heading_refused(self):
        with self.assertRaises(run_report.ReportError):
            run_report.parse("build", "stray\n## Choices\n\na\n")

    def test_deeper_headings_stay_in_their_section(self):
        own = run_report.parse("build", "## Choices\n\n### One\n\nA.\n")
        self.assertEqual(own, {"Choices": "### One\n\nA."})


class Write(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = os.path.join(self.tmp.name, "data")

    def write(self, own=None, copied=None, kind="build", name="add-numbers"):
        return run_report.write(kind, name, "/work/repo", self.data, own or {}, copied or {},
                                date="2026-11-14")

    def test_path_and_headings_in_order(self):
        path, lines = self.write({"Choices": "Named it add."})
        self.assertEqual(path, os.path.join(self.data, "reports", "repo", "2026-11-14-build-add-numbers.md"))
        with open(path, encoding="utf-8") as f:
            text = f.read()
        positions = [text.index(f"## {h}\n") for h in run_report.HEADINGS["build"]]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Named it add.", text)
        self.assertEqual(lines[0], f"Report written: {path}")

    def test_empty_heading_says_nothing_to_report(self):
        path, _ = self.write()
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("## Choices\n\nNothing to report.\n", text)

    def test_copied_reports_word_for_word_under_their_heading(self):
        report = "Result: FAIL\n\n| Check | Result |\n|---|---|\n| 1 | fail: \"quoted\" |\n  indented\n"
        copied = {"What each review found": [("Build review", report)],
                  "The hand-over script's report": [("Output", "Committed.\nPushed.")]}
        path, lines = self.write({"What each review found": "Corrected check 1."}, copied)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertIn(report, text)
        section = text[text.index("## What each review found"):text.index("## The hand-over script's report")]
        self.assertIn("Corrected check 1.", section)
        self.assertIn("### Build review\n\n" + report, section)
        self.assertIn("Committed.\nPushed.", text)
        self.assertIn(f"Copied: Build review ({len(report)} characters)", lines)

    def test_second_report_same_day_is_numbered(self):
        first, _ = self.write()
        second, _ = self.write()
        third, _ = self.write()
        self.assertTrue(second.endswith("2026-11-14-build-add-numbers-2.md"))
        self.assertTrue(third.endswith("2026-11-14-build-add-numbers-3.md"))
        self.assertTrue(os.path.exists(first))

    def test_audit_kind(self):
        path, _ = self.write(kind="audit", name="all")
        self.assertTrue(path.endswith("2026-11-14-audit-all.md"))
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for heading in run_report.HEADINGS["audit"]:
            self.assertIn(f"## {heading}\n", text)

    def test_fallback_is_said(self):
        with mock.patch.object(run_report.tempfile, "gettempdir", return_value=self.tmp.name):
            path, lines = run_report.write("build", "p", "/work/repo", "", {}, {}, date="2026-11-14")
        self.assertTrue(any("could not be written" in line for line in lines))
        self.assertTrue(path.startswith(self.tmp.name))

    def test_unknown_copied_heading_refused(self):
        with self.assertRaises(run_report.ReportError):
            self.write(copied={"Nowhere": [("x", "y")]})


if __name__ == "__main__":
    unittest.main()
