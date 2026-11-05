import json
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "status_check.sh")


def hook_input(path):
    return json.dumps({"tool_name": "Write", "tool_input": {"file_path": path, "content": "x"}})


class WithoutPython(unittest.TestCase):
    """Runs the wrapper with a PATH that holds the shell tools it needs but no python3."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bin = os.path.join(self.tmp.name, "bin")
        os.mkdir(self.bin)
        for tool in ("sh", "cat", "grep"):
            os.symlink(shutil.which(tool), os.path.join(self.bin, tool))

    def run_hook(self, path):
        return subprocess.run(
            [os.path.join(self.bin, "sh"), SCRIPT],
            input=hook_input(path),
            capture_output=True,
            text=True,
            env={"PATH": self.bin},
        )

    def test_refuses_a_spec_edit(self):
        result = self.run_hook("/repo/docs/specs/login.spec.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("needs Python 3", result.stderr)

    def test_refuses_an_adr_edit(self):
        result = self.run_hook("/repo/docs/adrs/0001-single-plugin.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("needs Python 3", result.stderr)

    def test_refuses_a_plan_edit(self):
        result = self.run_hook("/repo/docs/plans/2026-10-29-login.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("needs Python 3", result.stderr)

    def test_refuses_a_spike_record_edit(self):
        result = self.run_hook("/repo/docs/spikes/2026-11-04-tiff-files-open.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("needs Python 3", result.stderr)

    def test_refuses_a_brief_edit(self):
        result = self.run_hook("/repo/docs/brief.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("needs Python 3", result.stderr)

    def test_refuses_whatever_the_folders_case(self):
        self.assertEqual(self.run_hook("/repo/Docs/ADRs/0001-x.md").returncode, 2)

    def test_allows_any_other_file(self):
        result = self.run_hook("/repo/src/app.py")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")

    def test_allows_a_file_that_only_mentions_the_folder_in_its_content(self):
        text = json.dumps(
            {"tool_name": "Write", "tool_input": {"file_path": "/repo/README.md", "content": "see docs/adrs/"}}
        )
        result = subprocess.run(
            [os.path.join(self.bin, "sh"), SCRIPT], input=text, capture_output=True, text=True,
            env={"PATH": self.bin},
        )
        self.assertEqual(result.returncode, 0)


class WithPython(unittest.TestCase):
    def test_hands_the_input_to_the_python_check(self):
        with tempfile.TemporaryDirectory() as project:
            path = os.path.join(project, "docs", "adrs", "0001-x.md")
            os.makedirs(os.path.dirname(path))
            text = json.dumps(
                {"tool_name": "Write", "tool_input": {"file_path": path, "content": "---\nstatus: Accepted\n---\n"}}
            )
            result = subprocess.run(
                ["sh", SCRIPT], input=text, capture_output=True, text=True,
                env={**os.environ, "CLAUDE_PROJECT_DIR": project},
            )
        # A new ADR must start as Draft, so the Python check refuses it.
        self.assertEqual(result.returncode, 2)

    def run_brief(self, content):
        with tempfile.TemporaryDirectory() as project:
            path = os.path.join(project, "docs", "brief.md")
            text = json.dumps({"tool_name": "Write", "tool_input": {"file_path": path, "content": content}})
            return subprocess.run(
                ["sh", SCRIPT], input=text, capture_output=True, text=True,
                env={**os.environ, "CLAUDE_PROJECT_DIR": project},
            )

    def test_hands_the_input_to_the_reference_check(self):
        result = self.run_brief("# Brief\n\nFrom [the PRD](/tmp/prd.md).\n")
        self.assertEqual(result.returncode, 2)
        self.assertIn("/tmp/prd.md", result.stderr)

    def test_allows_a_brief_with_only_web_links(self):
        result = self.run_brief("# Brief\n\nSee [it](https://example.com).\n")
        self.assertEqual((result.returncode, result.stderr), (0, ""))


if __name__ == "__main__":
    unittest.main()
