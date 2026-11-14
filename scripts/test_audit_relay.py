"""Tests for audit_relay.py, fed recorded hook inputs."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_relay  # noqa: E402

AUDITOR = ("agentic:auditor", "Document: /r/docs/adrs/0001-a.md\nRepository: /r\nAudit it.")
CHECKER = ("agentic:audit-checker", "Document: /r/docs/adrs/0001-a.md\nRepository: /r\n"
           "=== AUDIT REPORT ===\nx\n=== END AUDIT REPORT ===")
BRIEF_CHECKER_OF_A = ("agentic:audit-checker", "Document: /r/docs/adrs/0001-a.md\nRepository: /r\n"
                      "=== BRIEF REPORT ===\nx\n=== END BRIEF REPORT ===")
BRIEF = ("agentic:brief-checker", "Document: /r/docs/brief.md\nRepository: /r\nDocuments:\n...")
PICKER = ("agentic:audit-picker", "Repository: /r\nCommits:\nabc 2026-11-14 Change")


class Relay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = os.path.join(self.tmp.name, "data")
        patcher = mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": self.data})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.calls = 0

    def hook(self, event, session="s1"):
        event = dict(event, session_id=session)
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(json.dumps(event))), redirect_stdout(out):
            self.assertEqual(audit_relay.main([]), 0)
        self.assertEqual(out.getvalue(), "", "the hook never answers")

    def agent(self, kind, report, session="s1", handed_back=False):
        agent, prompt = kind
        self.calls += 1
        response = ({"handback": "send", "handbackReport": {"text": report},
                     "content": [{"type": "text", "text": "delivered as a message"}]}
                    if handed_back else {"content": [{"type": "text", "text": report}]})
        self.hook({"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_use_id": f"c{self.calls}",
                   "tool_input": {"subagent_type": agent, "prompt": prompt}, "tool_response": response}, session)

    def launch(self, kind, agent_id, session="s1"):
        agent, prompt = kind
        self.calls += 1
        self.hook({"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_use_id": f"c{self.calls}",
                   "tool_input": {"subagent_type": agent, "prompt": prompt},
                   "tool_response": {"status": "async_launched", "agentId": agent_id}}, session)

    def stopped(self, agent, agent_id, report, session="s1"):
        self.hook({"hook_event_name": "SubagentStop", "agent_id": agent_id, "agent_type": agent,
                   "last_assistant_message": report}, session)

    def hand_back(self, agent, agent_id, report, session="s1"):
        self.hook({"hook_event_name": "PostToolUse", "tool_name": "SubagentHandback", "agent_id": agent_id,
                   "agent_type": agent, "tool_input": {"message": report}, "tool_response": {"success": True}},
                  session)

    def reports(self, session="s1"):
        return audit_relay.reports(self.data, session)


class Keeps(Relay):
    def test_each_agent_kept_by_type_document_and_kind(self):
        self.agent(AUDITOR, "Drift: one")
        self.agent(CHECKER, "Confirmed")
        self.agent(BRIEF_CHECKER_OF_A, "Rejected")
        self.agent(BRIEF, "Contradicts: one")
        self.agent(PICKER, "Pick: 0001")
        got = {(r["agent"], r["document"], r["kind"]): r["text"] for r in self.reports()}
        self.assertEqual(got, {
            ("auditor", "/r/docs/adrs/0001-a.md", ""): "Drift: one",
            ("audit-checker", "/r/docs/adrs/0001-a.md", "AUDIT REPORT"): "Confirmed",
            ("audit-checker", "/r/docs/adrs/0001-a.md", "BRIEF REPORT"): "Rejected",
            ("brief-checker", "/r/docs/brief.md", ""): "Contradicts: one",
            ("audit-picker", "", ""): "Pick: 0001",
        })

    def test_report_kept_word_for_word(self):
        report = "Result\n\n| a | \"b\" |\n  indented\n"
        self.agent(AUDITOR, report)
        self.assertEqual(self.reports()[0]["text"], report)

    def test_rerun_keeps_last_report(self):
        self.agent(AUDITOR, "first")
        self.agent(AUDITOR, "second")
        self.assertEqual([r["text"] for r in self.reports()], ["second"])

    def test_handed_back_report_kept(self):
        self.agent(AUDITOR, "Drift: one", handed_back=True)
        self.assertEqual(self.reports()[0]["text"], "Drift: one")

    def test_other_agents_ignored(self):
        self.agent(("general-purpose", "Document: x\nDo something"), "nope")
        self.agent(("agentic:adr-reviewer", "Document: x\nReview this ADR."), "nope")
        self.assertEqual(self.reports(), [])

    def test_sessions_kept_apart(self):
        self.agent(AUDITOR, "mine", session="s1")
        self.agent(AUDITOR, "theirs", session="s2")
        self.assertEqual([r["text"] for r in self.reports("s1")], ["mine"])

    def test_nothing_saved_without_data_folder(self):
        with mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": ""}):
            self.agent(AUDITOR, "x")
        self.assertFalse(os.path.exists(self.data))

    def test_clear(self):
        self.agent(AUDITOR, "x")
        audit_relay.clear(self.data, "s1")
        self.assertEqual(self.reports(), [])


class Background(Relay):
    def test_background_report_from_stop(self):
        self.launch(AUDITOR, "a1")
        self.stopped("agentic:auditor", "a1", "Drift: one")
        self.assertEqual(self.reports()[0]["text"], "Drift: one")

    def test_stop_before_launch_is_seen(self):
        self.stopped("agentic:auditor", "a1", "Drift: one")
        self.launch(AUDITOR, "a1")
        self.assertEqual(self.reports()[0]["text"], "Drift: one")

    def test_hand_back_stays_final(self):
        self.launch(AUDITOR, "a1")
        self.hand_back("agentic:auditor", "a1", "Drift: one")
        self.stopped("agentic:auditor", "a1", "Handing back my report.")
        self.assertEqual(self.reports()[0]["text"], "Drift: one")

    def test_hand_back_before_launch(self):
        self.hand_back("agentic:auditor", "a1", "Drift: one")
        self.stopped("agentic:auditor", "a1", "Handing back my report.")
        self.launch(AUDITOR, "a1")
        self.assertEqual(self.reports()[0]["text"], "Drift: one")

    def test_launch_alone_keeps_nothing(self):
        self.launch(AUDITOR, "a1")
        self.assertEqual(self.reports(), [])


if __name__ == "__main__":
    unittest.main()
