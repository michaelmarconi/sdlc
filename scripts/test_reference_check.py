import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "reference_check.py")
sys.path.insert(0, HERE)

import reference_check  # noqa: E402


class Workspace(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = os.path.join(self.tmp.name, "repo")
        os.makedirs(self.project)
        patcher = mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": self.project})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.brief = self.at("docs/brief.md")
        self.spec = self.at("docs/specs/login.spec.md")
        self.adr = self.at("docs/adrs/0001-database.md")

    def at(self, relative):
        return os.path.join(self.project, *relative.split("/"))

    def put(self, path, text="x"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def write(self, text, path=None):
        return reference_check.check(
            {"tool_name": "Write", "tool_input": {"file_path": path or self.brief, "content": text}}
        )


class AllowedReferences(Workspace):
    def test_a_web_link_passes(self):
        self.assertIsNone(self.write("See [the standard](https://www.rfc-editor.org/rfc/rfc9110).\n"))

    def test_a_plain_http_link_and_a_mail_link_pass(self):
        self.assertIsNone(self.write("[a](http://example.com) [b](mailto:team@example.com)\n"))

    def test_a_reference_definition_to_the_web_passes(self):
        self.assertIsNone(self.write("[std]: https://example.com/std\n"))

    def test_a_reference_to_another_lifecycle_document_is_left_to_the_reviewer(self):
        self.put(self.at("docs/adrs/0002-cache.md"))
        self.put(self.at("docs/plans/2026-11-05-login.md"))
        self.put(self.at("docs/spikes/2026-11-05-speed.md"))
        text = "[a](0002-cache.md) [b](../plans/2026-11-05-login.md) [c](../spikes/2026-11-05-speed.md)\n"
        self.assertIsNone(self.write(text, self.adr))

    def test_a_reference_to_code_is_not_checked(self):
        self.put(self.at("src/app.py"))
        self.assertIsNone(self.write("Checked in [app.py](../../src/app.py).\n", self.adr))

    def test_a_protocol_relative_web_link_passes(self):
        self.assertIsNone(self.write("[RFC](//www.rfc-editor.org/rfc/rfc9110)\n"))

    def test_a_link_to_a_folder_passes(self):
        os.makedirs(self.at("docs/plans"))
        self.assertIsNone(self.write("See [the plans](../plans/) and [here](./).\n", self.adr))

    def test_a_heading_in_the_same_document_passes(self):
        self.assertIsNone(self.write("See [goals](#goals).\n"))

    def test_links_in_code_spans_and_fences_are_ignored(self):
        text = "Write `[x](/tmp/prd.md)` like this.\n\n```\n[y](~/prd.md)\n```\n"
        self.assertIsNone(self.write(text))

    def test_other_files_are_left_alone(self):
        self.assertIsNone(self.write("[prd](/Users/me/prd.pdf)\n", self.at("docs/plans/2026-11-05-x.md")))
        self.assertIsNone(self.write("[prd](/Users/me/prd.pdf)\n", self.at("README.md")))
        self.assertIsNone(self.write("[prd](/Users/me/prd.pdf)\n", self.at("docs/specs/notes.md")))


class RefusedReferences(Workspace):
    def assertRefused(self, reason, target):
        self.assertIsNotNone(reason)
        self.assertIn(target, reason)
        self.assertIn("own words", reason)

    def test_an_absolute_path_is_refused(self):
        self.assertRefused(self.write("From [the PRD](/Users/me/Downloads/prd.pdf).\n"),
                           "/Users/me/Downloads/prd.pdf")

    def test_a_home_path_is_refused(self):
        self.assertRefused(self.write("From [the PRD](~/prd.md).\n"), "~/prd.md")

    def test_a_file_scheme_is_refused(self):
        self.assertRefused(self.write("From [the PRD](file:///tmp/prd.md).\n"), "file:///tmp/prd.md")

    def test_a_windows_path_is_refused(self):
        self.assertRefused(self.write("From [the PRD](C:/Users/me/prd.docx).\n"), "C:/Users/me/prd.docx")

    def test_a_path_that_leaves_the_repository_is_refused(self):
        self.assertRefused(self.write("From [the PRD](../../prd.md).\n"), "../../prd.md")

    def test_a_document_under_docs_that_is_not_a_lifecycle_document_is_refused(self):
        self.put(self.at("docs/prd.md"))
        self.assertRefused(self.write("From [the PRD](prd.md).\n"), "prd.md")

    def test_any_file_under_docs_that_is_not_a_lifecycle_document_is_refused(self):
        self.assertRefused(self.write("From [notes](notes/kickoff.pdf).\n", self.brief), "notes/kickoff.pdf")
        self.assertRefused(self.write("See [it](../../docs/adrs/sketch.txt).\n", self.spec),
                           "../../docs/adrs/sketch.txt")

    def test_a_reference_definition_is_checked(self):
        self.assertRefused(self.write("[prd]: /tmp/prd.md\n"), "/tmp/prd.md")

    def test_specs_and_adrs_are_checked(self):
        self.assertRefused(self.write("[prd](/tmp/prd.md)\n", self.spec), "/tmp/prd.md")
        self.assertRefused(self.write("[prd](/tmp/prd.md)\n", self.adr), "/tmp/prd.md")
        self.assertRefused(self.write("[prd](/tmp/prd.md)\n", self.at("docs/specs/a/b.spec.md")), "/tmp/prd.md")

    def test_the_brief_is_checked_whatever_the_folders_case(self):
        self.assertRefused(self.write("[prd](/tmp/prd.md)\n", self.at("Docs/Brief.md")), "/tmp/prd.md")

    def test_every_refused_reference_is_named(self):
        reason = self.write("[a](/tmp/a.md) [b](~/b.md) [ok](https://example.com)\n")
        self.assertIn("/tmp/a.md", reason)
        self.assertIn("~/b.md", reason)
        self.assertNotIn("https://example.com", reason)

    def test_an_edit_that_leaves_an_old_reference_in_place_is_allowed(self):
        self.put(self.brief, "# Brief\n\nFrom [the PRD](/tmp/prd.md).\n\nGoal: one.\n")
        reason = reference_check.check({
            "tool_name": "Edit",
            "tool_input": {"file_path": self.brief, "old_string": "Goal: one.", "new_string": "Goal: two."},
        })
        self.assertIsNone(reason)

    def test_an_edit_that_adds_a_reference_beside_an_old_one_names_only_the_new_one(self):
        self.put(self.brief, "# Brief\n\nFrom [the PRD](/tmp/prd.md).\n\nGoal: one.\n")
        reason = reference_check.check({
            "tool_name": "Edit",
            "tool_input": {"file_path": self.brief, "old_string": "Goal: one.",
                           "new_string": "Goal: [two](~/notes.md)."},
        })
        self.assertRefused(reason, "~/notes.md")
        self.assertNotIn("/tmp/prd.md", reason)

    def test_a_decided_adr_holding_an_old_reference_can_still_be_superseded(self):
        self.put(self.adr, "---\nstatus: 👍 Accepted\n---\n\n# X\n\nSee [notes](../research/n.md).\n")
        reason = reference_check.check({
            "tool_name": "Edit",
            "tool_input": {"file_path": self.adr, "old_string": "status: 👍 Accepted",
                           "new_string": "status: ↪️ Superseded\nsuperseded-by: 0002"},
        })
        self.assertIsNone(reason)

    def test_a_write_is_checked_even_when_the_old_file_cannot_be_read(self):
        os.makedirs(os.path.dirname(self.brief), exist_ok=True)
        with open(self.brief, "wb") as f:
            f.write(b"caf\xe9\n")
        self.assertRefused(self.write("[prd](/tmp/prd.md)\n"), "/tmp/prd.md")

    def test_angle_bracket_targets_are_read_without_their_brackets(self):
        self.assertRefused(self.write("[prd](</Users/me/My Docs/prd.pdf>)\n"), "/Users/me/My Docs/prd.pdf")
        self.assertIsNone(self.write("[a](<https://example.com/a b>) [b](<specs/login.spec.md>)\n"))

    def test_autolinks_and_html_links_are_checked(self):
        self.assertRefused(self.write("See <file:///tmp/prd.md>.\n"), "file:///tmp/prd.md")
        self.assertRefused(self.write('See <a href="/tmp/prd.md">it</a>.\n'), "/tmp/prd.md")
        self.assertRefused(self.write("<img src='~/shot.png'>\n"), "~/shot.png")
        self.assertIsNone(self.write("See <https://example.com> and <a href=\"https://x.org\">x</a>.\n"))

    def test_an_edit_that_removes_the_reference_is_allowed(self):
        self.put(self.brief, "# Brief\n\nFrom [the PRD](/tmp/prd.md).\n")
        reason = reference_check.check({
            "tool_name": "MultiEdit",
            "tool_input": {"file_path": self.brief, "edits": [
                {"old_string": "From [the PRD](/tmp/prd.md).", "new_string": "Teams lose a day a week."}]},
        })
        self.assertIsNone(reason)


class Robustness(Workspace):
    def test_an_edit_that_cannot_be_matched_is_left_to_the_status_check(self):
        self.put(self.brief, "# Brief\n")
        reason = reference_check.check({
            "tool_name": "Edit",
            "tool_input": {"file_path": self.brief, "old_string": "absent", "new_string": "[p](/tmp/p.md)"},
        })
        self.assertIsNone(reason)

    def test_a_payload_without_a_path_is_allowed(self):
        self.assertIsNone(reference_check.check({"tool_name": "Write", "tool_input": {}}))


class CommandLine(Workspace):
    def run_script(self, text):
        return subprocess.run([sys.executable, SCRIPT], input=text, capture_output=True, text=True,
                              env={**os.environ, "CLAUDE_PROJECT_DIR": self.project})

    def test_refuses_with_exit_code_2(self):
        payload = {"tool_name": "Write", "tool_input": {"file_path": self.brief, "content": "[p](/tmp/p.md)\n"}}
        result = self.run_script(json.dumps(payload))
        self.assertEqual(result.returncode, 2)
        self.assertIn("/tmp/p.md", result.stderr)

    def test_allows_with_exit_code_0(self):
        payload = {"tool_name": "Write", "tool_input": {"file_path": self.brief, "content": "# Brief\n"}}
        result = self.run_script(json.dumps(payload))
        self.assertEqual((result.returncode, result.stderr), (0, ""))

    def test_input_that_is_not_json_is_allowed(self):
        self.assertEqual(self.run_script("not json").returncode, 0)

    def test_has_help(self):
        result = subprocess.run([sys.executable, SCRIPT, "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Exit codes", result.stdout)


if __name__ == "__main__":
    unittest.main()
