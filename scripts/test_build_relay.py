"""Tests for build_relay.py, fed recorded hook inputs, against a throwaway git repository."""

import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_relay  # noqa: E402
import fresh_session  # noqa: E402

PLAN = "docs/plans/2026-11-03-thing.md"
CODE_PROMPT = (f"Document: {PLAN}\nRun /code-review medium main...HEAD on the current branch, then reply "
               "with its findings word for word, as text.")
ENV = dict(os.environ, GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.com",
           GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.com",
           GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


class Relay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = os.path.join(self.tmp.name, "repo")
        os.makedirs(self.repo)
        patcher = mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": os.path.join(self.tmp.name, "data"),
                                               "CLAUDE_PROJECT_DIR": self.repo})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.git("init", "-q", "-b", "main")
        self.commit("Start")
        fresh_session.save("s1", {"fresh": True, "messages": 1, "building": True})
        self.calls = 0

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, env=ENV, check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, message):
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def hook(self, event, session="s1"):
        event = dict(event, session_id=session)
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(json.dumps(event))), redirect_stdout(out):
            self.assertEqual(build_relay.main([]), 0)
        text = out.getvalue().strip()
        return json.loads(text)["hookSpecificOutput"] if text else None

    def agent(self, agent, prompt, report, session="s1"):
        self.calls += 1
        call = f"call{self.calls}"
        tool_input = {"subagent_type": agent, "prompt": prompt}
        before = self.hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_use_id": call,
                            "tool_input": tool_input}, session)
        self.hook({"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_use_id": call,
                   "tool_input": tool_input, "tool_response": {"content": [{"type": "text", "text": report}]}},
                  session)
        return before

    def plan_review(self, report="Result: FAIL\nplan finding", session="s1"):
        return self.agent("agentic:build-reviewer", f"Document: {PLAN}\nBase: main\nReview this build.", report, session)

    def security_review(self, report="security finding", session="s1"):
        return self.agent("general-purpose", f"Document: {PLAN}\nRun /security-review and report.", report, session)

    def code_review(self, report='[{"summary": "code finding"}]', session="s1"):
        return self.agent("general-purpose", CODE_PROMPT, report, session)

    def all_reviews(self, session="s1"):
        self.code_review(session=session)
        self.security_review(session=session)
        self.plan_review(session=session)

    def check(self, session="s1"):
        return self.hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_use_id": "check",
                          "tool_input": {"subagent_type": "agentic:build-correction-checker",
                                         "prompt": f"Document: {PLAN}\nCheck the corrections."}}, session)


class Checker(Relay):
    def test_reports_and_reviewed_commit_attached(self):
        reviewed = self.git("rev-parse", "HEAD")
        self.code_review()
        self.security_review()
        self.plan_review()
        self.commit("Correct the findings")
        result = self.check()
        self.assertEqual(result["permissionDecision"], "allow")
        prompt = result["updatedInput"]["prompt"]
        self.assertIn("code finding", prompt)
        self.assertIn("security finding", prompt)
        self.assertIn("plan finding", prompt)
        self.assertIn(f"Reviewed commit: {reviewed}", prompt)
        self.assertIn("rubric.md", prompt)

    def test_refused_without_the_security_review(self):
        self.code_review()
        self.plan_review()
        self.commit("Correct")
        result = self.check()
        self.assertEqual(result["permissionDecision"], "deny")
        self.assertIn("security review", result["permissionDecisionReason"])
        self.assertIn("show the person", result["permissionDecisionReason"])

    def test_refused_without_the_code_review(self):
        self.security_review()
        self.plan_review()
        self.commit("Correct")
        self.assertIn("code review", self.check()["permissionDecisionReason"])

    def test_refused_without_the_plan_review(self):
        self.code_review()
        self.security_review()
        self.commit("Correct")
        result = self.check()
        self.assertEqual(result["permissionDecision"], "deny")
        self.assertIn("build review", result["permissionDecisionReason"])

    def test_refused_when_nothing_was_committed_since(self):
        self.all_reviews()
        result = self.check()
        self.assertEqual(result["permissionDecision"], "deny")
        self.assertIn("commit", result["permissionDecisionReason"])

    def test_later_reviews_replace_earlier_ones_of_another_commit(self):
        self.plan_review("old plan finding")
        self.commit("More work")
        self.code_review()
        self.security_review()
        self.plan_review("new plan finding")
        self.commit("Correct")
        prompt = self.check()["updatedInput"]["prompt"]
        self.assertIn("new plan finding", prompt)
        self.assertNotIn("old plan finding", prompt)

    def test_refused_without_document_line(self):
        result = self.hook({"hook_event_name": "PreToolUse", "tool_name": "Agent",
                            "tool_input": {"subagent_type": "agentic:build-correction-checker", "prompt": "Check."}})
        self.assertEqual(result["permissionDecision"], "deny")


class Corrections(Relay):
    def test_security_agent_without_a_type_counted(self):
        self.code_review()
        self.agent("", f"Document: {PLAN}\nRun /security-review and report.", "security finding")
        self.plan_review()
        self.commit("Correct")
        self.assertIn("security finding", self.check()["updatedInput"]["prompt"])

    def test_empty_code_review_result_not_kept(self):
        self.code_review(report="")
        self.security_review()
        self.plan_review()
        self.commit("Correct")
        self.assertIn("code review", self.check()["permissionDecisionReason"])

    def test_reports_handed_back_are_attached(self):
        # In a Claude project thread the report comes in handbackReport; content only points to it.
        pointer = "This agent's report was delivered to you as a message (its SubagentHandback call)."
        for agent, prompt, report in [
                ("general-purpose", CODE_PROMPT, "code finding"),
                ("general-purpose", f"Document: {PLAN}\nRun /security-review and report.", "security finding"),
                ("agentic:build-reviewer", f"Document: {PLAN}\nBase: main\nReview this build.", "plan finding")]:
            tool_input = {"subagent_type": agent, "prompt": prompt}
            self.hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_use_id": prompt,
                       "tool_input": tool_input})
            self.hook({"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_use_id": prompt,
                       "tool_input": tool_input,
                       "tool_response": {"handback": "send", "handbackReport": {"text": report},
                                         "content": [{"type": "text", "text": pointer}]}})
        self.commit("Correct")
        prompt = self.check()["updatedInput"]["prompt"]
        self.assertIn("=== CODE REVIEW REPORT ===\ncode finding\n", prompt)
        self.assertIn("security finding", prompt)
        self.assertIn("plan finding", prompt)
        self.assertNotIn("SubagentHandback", prompt)

    def test_a_code_review_run_inside_the_session_is_no_report(self):
        # Issue #79: run by the Skill tool, the review's findings never reach the hook, whether the
        # skill runs inline (only a success flag comes back) or forked (its result has text). Only
        # the agent /build starts for it counts.
        for response in ({"success": True, "commandName": "code-review"},
                         {"success": True, "status": "forked", "result": "code finding"}):
            self.hook({"hook_event_name": "PostToolUse", "tool_name": "Skill",
                       "tool_input": {"skill": "code-review", "args": "medium main...HEAD"},
                       "tool_response": response})
        self.security_review()
        self.plan_review()
        self.commit("Correct")
        self.assertIn("No code review report", self.check()["permissionDecisionReason"])

    def test_the_code_and_security_reviews_are_told_apart(self):
        self.code_review(report="code finding")
        self.security_review(report="security finding")
        self.plan_review()
        self.commit("Correct")
        prompt = self.check()["updatedInput"]["prompt"]
        self.assertIn("=== CODE REVIEW REPORT ===\ncode finding\n", prompt)
        self.assertIn("=== SECURITY REVIEW REPORT ===\nsecurity finding\n", prompt)

    def launch(self, agent, prompt, agent_id, session="s1", **extra):
        """Start a review that Claude Code runs in the background: its tool result is a launch notice."""
        self.calls += 1
        call = f"call{self.calls}"
        tool_input = dict({"subagent_type": agent, "prompt": prompt}, **extra)
        before = self.hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_use_id": call,
                            "tool_input": tool_input}, session)
        self.hook({"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_use_id": call,
                   "tool_input": tool_input,
                   "tool_response": {"isAsync": True, "status": "async_launched", "agentId": agent_id}},
                  session)
        return before, call

    def stopped(self, agent, agent_id, report, session="s1"):
        return self.hook({"hook_event_name": "SubagentStop", "agent_id": agent_id, "agent_type": agent,
                          "stop_hook_active": False, "last_assistant_message": report}, session)

    SECURITY = ("general-purpose", f"Document: {PLAN}\nRun /security-review and report.")
    CODE = ("general-purpose", CODE_PROMPT)
    REVIEW = ("agentic:build-reviewer", f"Document: {PLAN}\nBase: main\nReview this build.")

    def test_reports_of_background_reviews_are_attached(self):
        self.code_review()
        self.assertIsNone(self.launch(*self.SECURITY, "a1")[0])
        self.assertIsNone(self.launch(*self.REVIEW, "a2")[0])
        self.assertIsNone(self.stopped("general-purpose", "a1", "security finding"))
        self.assertIsNone(self.stopped("agentic:build-reviewer", "a2", "plan finding"))
        self.commit("Correct")
        prompt = self.check()["updatedInput"]["prompt"]
        self.assertIn("=== SECURITY REVIEW REPORT ===\nsecurity finding\n", prompt)
        self.assertIn("=== BUILD REVIEW REPORT ===\nplan finding\n", prompt)

    def test_a_background_report_counts_when_the_agent_stops_before_its_launch_is_seen(self):
        self.code_review()
        calls = []
        for (agent, prompt), agent_id, report in ((self.SECURITY, "a1", "security finding"),
                                                  (self.REVIEW, "a2", "plan finding")):
            self.calls += 1
            call = f"call{self.calls}"
            tool_input = {"subagent_type": agent, "prompt": prompt}
            self.hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_use_id": call,
                       "tool_input": tool_input})
            self.stopped(agent, agent_id, report)
            calls.append((call, tool_input, agent_id))
        for call, tool_input, agent_id in calls:
            self.hook({"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_use_id": call,
                       "tool_input": tool_input,
                       "tool_response": {"status": "async_launched", "agentId": agent_id}})
        self.commit("Correct")
        prompt = self.check()["updatedInput"]["prompt"]
        self.assertIn("security finding", prompt)
        self.assertIn("plan finding", prompt)

    def test_a_background_code_review_is_attached_beside_a_background_security_review(self):
        self.launch(*self.CODE, "a3")
        self.launch(*self.SECURITY, "a1")
        self.plan_review()
        self.stopped("general-purpose", "a1", "security finding")
        self.stopped("general-purpose", "a3", "code finding")
        self.commit("Correct")
        prompt = self.check()["updatedInput"]["prompt"]
        self.assertIn("=== CODE REVIEW REPORT ===\ncode finding\n", prompt)
        self.assertIn("=== SECURITY REVIEW REPORT ===\nsecurity finding\n", prompt)

    def test_a_code_review_that_stops_before_its_launch_is_seen_counts(self):
        self.security_review()
        self.plan_review()
        self.calls += 1
        tool_input = {"subagent_type": "general-purpose", "prompt": CODE_PROMPT}
        self.hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_use_id": "c",
                   "tool_input": tool_input})
        self.stopped("general-purpose", "a3", "code finding")
        self.hook({"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_use_id": "c",
                   "tool_input": tool_input, "tool_response": {"status": "async_launched", "agentId": "a3"}})
        self.commit("Correct")
        self.assertIn("code finding", self.check()["updatedInput"]["prompt"])

    def test_the_code_reviews_own_agents_do_not_replace_its_report(self):
        # /code-review starts finder and verifier agents of its own, which also run as general-purpose.
        self.launch(*self.CODE, "a3")
        self.security_review()
        self.plan_review()
        for n in range(8):
            self.stopped("general-purpose", f"f{n}", "a finder's candidates")
        self.stopped("general-purpose", "a3", "code finding")
        self.commit("Correct")
        prompt = self.check()["updatedInput"]["prompt"]
        self.assertIn("=== CODE REVIEW REPORT ===\ncode finding\n", prompt)
        self.assertNotIn("candidates", prompt)

    def test_a_held_report_outlasts_the_code_reviews_own_agents(self):
        # The security review stops before its launch is seen, then the code review's finders stop.
        self.code_review()
        self.plan_review()
        tool_input = {"subagent_type": "general-purpose", "prompt": self.SECURITY[1]}
        self.hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_use_id": "s",
                   "tool_input": tool_input})
        self.stopped("general-purpose", "a1", "security finding")
        for n in range(20):
            self.stopped("general-purpose", f"f{n}", "a finder's candidates")
        self.hook({"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_use_id": "s",
                   "tool_input": tool_input, "tool_response": {"status": "async_launched", "agentId": "a1"}})
        self.commit("Correct")
        self.assertIn("security finding", self.check()["updatedInput"]["prompt"])

    def test_a_launch_notice_alone_is_no_report(self):
        self.code_review()
        self.launch(*self.SECURITY, "a1")
        self.launch(*self.REVIEW, "a2")
        self.commit("Correct")
        self.assertEqual(self.check()["permissionDecision"], "deny")

    def test_an_agent_the_relay_never_saw_start_changes_nothing(self):
        self.all_reviews()
        self.stopped("agentic:build-reviewer", "a9", "another report")
        self.stopped("general-purpose", "a8", "another report")
        self.commit("Correct")
        prompt = self.check()["updatedInput"]["prompt"]
        self.assertNotIn("another report", prompt)
        self.assertIn("plan finding", prompt)

    def test_a_stop_outside_a_build_saves_nothing(self):
        fresh_session.save("s2", {"fresh": True, "messages": 1})
        self.stopped("agentic:build-reviewer", "a1", "plan finding", session="s2")
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "data", "builds", "s2.json")))

    def test_an_agent_that_stops_again_has_its_last_report_kept(self):
        self.code_review()
        self.launch(*self.SECURITY, "a1")
        self.launch(*self.REVIEW, "a2")
        self.stopped("general-purpose", "a1", "an early line")
        self.stopped("general-purpose", "a1", "security finding")
        self.stopped("agentic:build-reviewer", "a2", "plan finding")
        self.commit("Correct")
        prompt = self.check()["updatedInput"]["prompt"]
        self.assertIn("security finding", prompt)
        self.assertNotIn("an early line", prompt)

    # In auto mode an agent ends by calling SubagentHandback: its SubagentStop then has no last
    # message, and the hand-back may not be in its transcript yet.

    def hand_back(self, agent, agent_id, report, session="s1"):
        return self.hook({"hook_event_name": "PostToolUse", "agent_id": agent_id, "agent_type": agent,
                          "tool_name": "SubagentHandback", "tool_use_id": f"handback-{agent_id}",
                          "tool_input": {"message": report},
                          "tool_response": {"success": True, "message": "Report delivered to your caller."}},
                         session)

    def stopped_after_hand_back(self, agent, agent_id, session="s1"):
        return self.hook({"hook_event_name": "SubagentStop", "agent_id": agent_id, "agent_type": agent,
                          "stop_hook_active": False,
                          "agent_transcript_path": os.path.join(self.tmp.name, "not-yet.jsonl")}, session)

    def test_reports_handed_back_by_background_reviews_are_attached(self):
        self.code_review()
        self.launch(*self.SECURITY, "a1")
        self.launch(*self.REVIEW, "a2")
        for agent, agent_id, report in (("general-purpose", "a1", "security finding"),
                                        ("agentic:build-reviewer", "a2", "plan finding")):
            self.assertIsNone(self.hand_back(agent, agent_id, report))
            self.assertIsNone(self.stopped_after_hand_back(agent, agent_id))
        self.commit("Correct")
        prompt = self.check()["updatedInput"]["prompt"]
        self.assertIn("=== SECURITY REVIEW REPORT ===\nsecurity finding\n", prompt)
        self.assertIn("=== BUILD REVIEW REPORT ===\nplan finding\n", prompt)

    def test_a_line_left_after_a_hand_back_does_not_replace_the_report(self):
        self.code_review()
        self.launch(*self.SECURITY, "a1")
        self.launch(*self.REVIEW, "a2")
        self.hand_back("general-purpose", "a1", "security finding")
        self.stopped("general-purpose", "a1", "Handing back my report.")
        self.hand_back("agentic:build-reviewer", "a2", "plan finding")
        self.commit("Correct")
        prompt = self.check()["updatedInput"]["prompt"]
        self.assertIn("security finding", prompt)
        self.assertNotIn("Handing back", prompt)

    def test_a_report_handed_back_before_its_launch_is_seen_counts(self):
        self.code_review()
        calls = []
        for (agent, prompt), agent_id, report in ((self.SECURITY, "a1", "security finding"),
                                                  (self.REVIEW, "a2", "plan finding")):
            self.calls += 1
            call = f"call{self.calls}"
            tool_input = {"subagent_type": agent, "prompt": prompt}
            self.hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_use_id": call,
                       "tool_input": tool_input})
            self.hand_back(agent, agent_id, report)
            self.stopped(agent, agent_id, "Handing back my report.")
            calls.append((call, tool_input, agent_id))
        for call, tool_input, agent_id in calls:
            self.hook({"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_use_id": call,
                       "tool_input": tool_input,
                       "tool_response": {"status": "async_launched", "agentId": agent_id}})
        self.commit("Correct")
        prompt = self.check()["updatedInput"]["prompt"]
        self.assertIn("security finding", prompt)
        self.assertIn("plan finding", prompt)
        self.assertNotIn("Handing back", prompt)

    def test_a_hand_back_stays_final_after_other_agents_hand_back(self):
        self.code_review()
        self.launch(*self.SECURITY, "a1")
        self.launch(*self.REVIEW, "a2")
        self.hand_back("general-purpose", "a1", "security finding")
        for n in range(8):  # implementers and other helpers that run as general-purpose
            self.hand_back("general-purpose", f"x{n}", "an implementer's summary")
        self.stopped("general-purpose", "a1", "Handing back my report.")
        self.hand_back("agentic:build-reviewer", "a2", "plan finding")
        self.commit("Correct")
        prompt = self.check()["updatedInput"]["prompt"]
        self.assertIn("security finding", prompt)
        self.assertNotIn("Handing back", prompt)

    def test_agents_no_review_waits_for_are_not_held(self):
        self.all_reviews()
        self.stopped("general-purpose", "a9", "an implementer's summary")
        with open(build_relay.record_path("s1"), encoding="utf-8") as f:
            self.assertNotIn("implementer", f.read())

    def test_review_asked_to_run_in_the_background_is_allowed(self):
        self.code_review()
        self.assertIsNone(self.launch(*self.SECURITY, "a1", run_in_background=True)[0])
        self.assertIsNone(self.launch(*self.REVIEW, "a2", run_in_background=True)[0])
        self.stopped("general-purpose", "a1", "security finding")
        self.stopped("agentic:build-reviewer", "a2", "plan finding")
        self.commit("Correct")
        self.assertEqual(self.check()["permissionDecision"], "allow")

    def test_one_correction_check_only(self):
        self.all_reviews()
        self.commit("Correct")
        self.assertEqual(self.check()["permissionDecision"], "allow")
        self.hook({"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_use_id": "check",
                   "tool_input": {"subagent_type": "agentic:build-correction-checker",
                                  "prompt": f"Document: {PLAN}\nCheck the corrections."},
                   "tool_response": {"content": [{"type": "text", "text": "Result: FAIL"}]}})
        self.commit("Correct again")
        self.assertEqual(self.check()["permissionDecision"], "deny")


class KeptForTheReport(Relay):
    """The reviews and the correction check stay on record, for hand_over.py's report file (ADR 0034)."""

    def checked(self, response):
        self.all_reviews()
        self.commit("Correct")
        self.assertEqual(self.check()["permissionDecision"], "allow")
        self.hook({"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_use_id": "check",
                   "tool_input": {"subagent_type": "agentic:build-correction-checker",
                                  "prompt": f"Document: {PLAN}\nCheck the corrections."},
                   "tool_response": response})

    def kept(self, plan=PLAN):
        return build_relay.kept_reports(os.path.join(self.tmp.name, "data"), "s1", plan, cwd=self.repo)

    def test_reviews_and_check_kept_after_the_check(self):
        self.checked({"content": [{"type": "text", "text": "Result: PASS\nall made"}]})
        kept = self.kept()
        self.assertEqual(kept["code"], '[{"summary": "code finding"}]')
        self.assertEqual(kept["security"], "security finding")
        self.assertEqual(kept["plan"], "Result: FAIL\nplan finding")
        self.assertEqual(kept["check"], "Result: PASS\nall made")

    def test_handed_back_check_kept(self):
        self.checked({"handback": "send", "handbackReport": {"text": "Result: PASS"},
                      "content": [{"type": "text", "text": "delivered as a message"}]})
        self.assertEqual(self.kept()["check"], "Result: PASS")

    def test_background_check_kept(self):
        self.all_reviews()
        self.commit("Correct")
        tool_input = {"subagent_type": "agentic:build-correction-checker",
                      "prompt": f"Document: {PLAN}\nCheck the corrections."}
        self.hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_use_id": "check",
                   "tool_input": tool_input})
        self.hook({"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_use_id": "check",
                   "tool_input": tool_input, "tool_response": {"status": "async_launched", "agentId": "c1"}})
        self.hook({"hook_event_name": "SubagentStop", "agent_id": "c1",
                   "agent_type": "agentic:build-correction-checker", "last_assistant_message": "Result: FAIL\nCHK-1"})
        self.assertEqual(self.kept()["check"], "Result: FAIL\nCHK-1")
        self.commit("Correct again")
        self.assertEqual(self.check()["permissionDecision"], "deny")

    def test_reviews_kept_without_a_check(self):
        self.all_reviews()
        kept = self.kept()
        self.assertEqual(sorted(kept), ["code", "plan", "security"])

    def test_another_plan_gets_nothing(self):
        self.all_reviews()
        self.assertIsNone(self.kept("docs/plans/2026-11-03-other.md"))

    def test_plan_named_by_its_full_path_matches(self):
        self.all_reviews()
        self.assertIsNotNone(self.kept(os.path.join(self.repo, PLAN)))

    def test_no_record_gets_nothing(self):
        self.assertIsNone(self.kept())


class LeftAlone(Relay):
    def test_reviews_outside_a_build_not_kept(self):
        fresh_session.save("s2", {"fresh": True, "messages": 1})
        self.all_reviews(session="s2")
        self.commit("Correct")
        self.assertEqual(self.check(session="s2")["permissionDecision"], "deny")

    def test_other_agents_left_alone(self):
        self.assertIsNone(self.agent("Explore", "Find the code", "found"))
        self.assertIsNone(self.agent("general-purpose", f"Document: {PLAN}\nDo something else.", "x"))

    def test_reports_survive_the_session_ending_so_a_resumed_build_can_check_them(self):
        # Issue #37: `claude --resume`, or a restarted container, brings the same session back.
        self.all_reviews()
        self.hook({"hook_event_name": "SessionEnd"})
        self.commit("Correct")
        self.assertEqual(self.check()["permissionDecision"], "allow")

    def test_saving_reports_deletes_another_sessions_once_they_are_a_month_old(self):
        fresh_session.save("old", {"fresh": True, "messages": 1, "building": True})
        self.plan_review(session="old")
        builds = os.path.join(self.tmp.name, "data", "builds")
        month = time.time() - 31 * 24 * 60 * 60
        for name in os.listdir(builds):
            os.utime(os.path.join(builds, name), (month, month))
        self.plan_review()
        self.assertEqual(sorted(os.listdir(builds)), ["s1.json", "s1.json.lock"])

    def test_bad_input_ignored(self):
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO("nope")), redirect_stdout(out):
            self.assertEqual(build_relay.main([]), 0)
        self.assertEqual(out.getvalue(), "")


class SessionFolderAboveTheRepository(Relay):
    """A Claude project thread: the session folder is not a repository, and holds the repository
    one level down (issue #84)."""

    def setUp(self):
        super().setUp()
        self.session = os.path.realpath(self.tmp.name)
        patcher = mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": self.session})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.cwd = self.session

    def hook(self, event, session="s1"):
        return super().hook(dict(event, cwd=self.cwd), session)

    def reviews_named(self, plan):
        self.agent("general-purpose", CODE_PROMPT.replace(PLAN, plan), '[{"summary": "code finding"}]')
        self.agent("general-purpose", f"Document: {plan}\nRun /security-review and report.", "security finding")
        self.agent("agentic:build-reviewer", f"Document: {plan}\nBase: main\nReview this build.", "plan finding")

    def check_named(self, plan):
        return self.hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_use_id": "check",
                          "tool_input": {"subagent_type": "agentic:build-correction-checker",
                                         "prompt": f"Document: {plan}\nCheck the corrections."}})

    def assert_checks_after_a_commit(self, plan):
        reviewed = self.git("rev-parse", "HEAD")
        self.reviews_named(plan)
        self.assertEqual(self.check_named(plan)["permissionDecision"], "deny")
        self.commit("Correct the findings")
        result = self.check_named(plan)
        self.assertEqual(result["permissionDecision"], "allow")
        self.assertIn(f"Reviewed commit: {reviewed}", result["updatedInput"]["prompt"])

    def test_plan_named_from_the_session_folder(self):
        self.assert_checks_after_a_commit(f"repo/{PLAN}")

    def test_plan_named_by_its_full_path(self):
        self.assert_checks_after_a_commit(os.path.join(self.repo, PLAN))

    def test_plan_named_from_the_repository_when_the_shell_is_in_it(self):
        self.cwd = self.repo
        self.assert_checks_after_a_commit(PLAN)

    def test_no_repository_holds_the_plan(self):
        os.makedirs(os.path.join(self.session, "loose"))
        self.reviews_named(f"loose/{PLAN}")
        result = self.check_named(f"loose/{PLAN}")
        self.assertEqual(result["permissionDecision"], "deny")
        reason = result["permissionDecisionReason"]
        self.assertIn("no git repository", reason)
        self.assertNotIn("Nothing has been committed", reason)

    def test_a_record_with_no_repository_still_checks(self):
        # A record written before the repository was kept beside the commit.
        reviewed = self.git("rev-parse", "HEAD")
        self.reviews_named(f"repo/{PLAN}")
        path = build_relay.record_path("s1")
        with open(path, encoding="utf-8") as f:
            record = json.load(f)
        record.pop("repository", None)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f)
        self.commit("Correct")
        result = self.check_named(f"repo/{PLAN}")
        self.assertEqual(result["permissionDecision"], "allow")
        self.assertIn(f"Reviewed commit: {reviewed}", result["updatedInput"]["prompt"])

    def test_a_review_whose_plan_no_repository_holds_keeps_the_other_reports(self):
        self.reviews_named(f"repo/{PLAN}")
        self.agent("agentic:build-reviewer", f"Document: missing/{PLAN}\nBase: main\nReview this build.", "stray")
        with open(build_relay.record_path("s1"), encoding="utf-8") as f:
            record = json.load(f)
        self.assertEqual(sorted(record["reports"]), ["code", "plan", "security"])
        self.assertIsNotNone(record["commit"])

    def test_a_review_of_a_plan_in_another_repository_starts_a_new_record(self):
        other = os.path.join(self.session, "other")
        os.makedirs(other)
        subprocess.run(["git", "init", "-q", "-b", "main", other], check=True, env=ENV)
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "Start"], cwd=other, check=True, env=ENV)
        self.reviews_named(f"repo/{PLAN}")
        self.agent("agentic:build-reviewer", f"Document: other/{PLAN}\nBase: main\nReview this build.", "other finding")
        with open(build_relay.record_path("s1"), encoding="utf-8") as f:
            record = json.load(f)
        self.assertEqual(record["repository"], other)
        self.assertEqual(sorted(record["reports"]), ["plan"])


if __name__ == "__main__":
    unittest.main()
