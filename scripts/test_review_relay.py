import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "review_relay.py")
ROOT = os.path.normpath(os.path.join(HERE, ".."))

SPEC = "docs/specs/booking.spec.md"
REPORT = "Result: FAIL\n\n| Check | Result | Evidence |\n|---|---|---|\n| 2. Story | fail | \"x\" |\n"
DRAFT = "Title: Review stops early\n\nBody line one.\nBody line two.\n"
WORDING = "Result: FAIL\n\nFindings:\n- \"rides along\": rewrite as \"is sent with\"\n"
LANGUAGE = "sdlc:language-checker"
# In a Claude project thread a subagent reports through its SubagentHandback tool: the Agent
# tool's result then carries the report in handbackReport, and its content only says where it went.
POINTER = ('This agent\'s report was delivered to you as a message from "a1b2c3" (its '
           'SubagentHandback call). Read it there; it is not repeated here.')


def handed_back(report):
    """An Agent tool result whose report came through a hand-back."""
    return {"status": "completed", "agentId": "a1b2c3", "handback": "send",
            "handbackReport": {"text": report}, "content": [{"type": "text", "text": POINTER}]}
TOPIC = "docs/practices/testing.md"
PAIR = f"AGENTS.md, {TOPIC}"


def feedback_request(draft, kind="bug"):
    return f"Document: feedback draft\nKind: {kind}\n=== DRAFT ===\n{draft}=== END DRAFT ===\n"


class Relay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = os.path.join(self.tmp.name, "project")
        self.data = os.path.join(self.tmp.name, "data")
        os.makedirs(self.project)
        self.session = "s1"

    def put(self, path, text):
        full = os.path.join(self.project, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)

    def run_hook(self, event, raw=None, data=True):
        env = dict(os.environ, CLAUDE_PLUGIN_DATA=self.data, CLAUDE_PROJECT_DIR=self.project,
                   CLAUDE_PLUGIN_ROOT=ROOT)
        if not data:
            del env["CLAUDE_PLUGIN_DATA"]
        done = subprocess.run([sys.executable, SCRIPT], input=raw if raw is not None else json.dumps(event),
                              capture_output=True, text=True, env=env)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout) if done.stdout.strip() else None

    def agent(self, when, agent, prompt, response=None, session=None, call=None, **extra):
        event = {"hook_event_name": when, "session_id": session or self.session, "cwd": self.project,
                 "tool_name": "Agent", "tool_use_id": call or f"{agent}-{prompt}",
                 "tool_input": dict({"subagent_type": agent, "prompt": prompt,
                                     "description": "a task"}, **extra)}
        if response is not None:
            event["tool_response"] = {"content": [{"type": "text", "text": response}]}
        return self.run_hook(event)

    def review(self, agent="sdlc:spec-reviewer", prompt=f"Document: {SPEC}\nReview this spec.",
               report=REPORT, session=None, wording=WORDING):
        """Run the skill's reviewer, then the language checker unless wording is None."""
        out = self.agent("PreToolUse", agent, prompt, session=session)
        if "feedback draft" in prompt:
            self.assertIsNone(out)
        else:
            self.assertAllowed(out)
        self.assertIsNone(self.agent("PostToolUse", agent, prompt, response=report, session=session))
        if wording is not None:
            self.language(prompt, wording, session=session)

    def language(self, prompt=f"Document: {SPEC}\nCheck the wording.", wording=WORDING, session=None):
        out = self.agent("PreToolUse", LANGUAGE, prompt, session=session)
        if "feedback draft" in prompt:
            self.assertIsNone(out)
        else:
            self.assertAllowed(out)
        self.assertIsNone(self.agent("PostToolUse", LANGUAGE, prompt, response=wording, session=session))

    def check(self, prompt=f"Document: {SPEC}\nCheck the corrections.", session=None, **extra):
        return self.agent("PreToolUse", "sdlc:correction-checker", prompt, session=session, **extra)

    def assertAllowed(self, out):
        self.assertIsNotNone(out)
        decision = out["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "allow")
        return decision["updatedInput"]

    def assertStarted(self, out, document=SPEC, project=None):
        """The agent starts with the document relative to its repository and that folder named."""
        prompt = self.assertAllowed(out)["prompt"]
        lines = prompt.splitlines()
        self.assertEqual(lines[0], f"Document: {document}")
        self.assertEqual(lines[1], f"Repository: {os.path.realpath(project or self.project)}")
        return prompt

    def assertRefused(self, out, needle):
        self.assertIsNotNone(out)
        decision = out["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn(needle, decision["permissionDecisionReason"])

    def saved(self):
        folder = os.path.join(self.data, "reviews")
        return [os.path.join(d, f) for d, _, files in os.walk(folder) for f in files]

    # Reviewer start and finish

    def test_checker_gets_the_report_and_the_text_as_reviewed_word_for_word(self):
        self.put(SPEC, "# Booking\n\nAs reviewed.\n")
        self.review()
        self.put(SPEC, "# Booking\n\nCorrected.\n")
        updated = self.assertAllowed(self.check())
        prompt = updated["prompt"]
        self.assertTrue(prompt.startswith(f"Document: {SPEC}\nRepository: {os.path.realpath(self.project)}\n"
                                          "Check the corrections."))
        self.assertIn("=== REVIEW REPORT ===\n" + REPORT + "\n=== END REVIEW REPORT ===", prompt)
        self.assertIn(f"=== DOCUMENT AS REVIEWED: {SPEC} ===\n# Booking\n\nAs reviewed.\n\n"
                      "=== END DOCUMENT ===", prompt)
        self.assertNotIn("Corrected.", prompt)

    def test_checker_request_keeps_its_other_fields(self):
        self.put(SPEC, "v1\n")
        self.review()
        self.put(SPEC, "v2\n")
        updated = self.assertAllowed(self.check(model="sonnet"))
        self.assertEqual(updated["subagent_type"], "sdlc:correction-checker")
        self.assertEqual(updated["description"], "a task")
        self.assertEqual(updated["model"], "sonnet")

    def test_checker_is_told_the_rubric_and_files_of_the_skill_that_reviewed(self):
        self.put(SPEC, "v1\n")
        self.review()
        self.put(SPEC, "v2\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn(os.path.join(ROOT, "skills", "spec", "references", "rubric.md"), prompt)
        self.assertIn("docs/brief.md", prompt)
        adr = "docs/adrs/0001-use-x.md"
        self.put(adr, "v1\n")
        self.review(agent="sdlc:adr-reviewer", prompt=f"Document: {adr}\nReview this ADR.")
        self.put(adr, "v2\n")
        prompt = self.assertAllowed(self.check(prompt=f"Document: {adr}\nCheck."))["prompt"]
        self.assertIn(os.path.join(ROOT, "skills", "adr", "references", "rubric.md"), prompt)
        self.assertNotIn("spec", prompt.split("=== REVIEW REPORT ===")[1].split("=== END DOCUMENT ===")[1])

    def test_checker_of_a_plan_is_told_the_plan_rubric_and_the_documents_it_names(self):
        plan = "docs/plans/2026-10-29-x.md"
        self.put(plan, "v1\n")
        self.review(agent="sdlc:plan-reviewer", prompt=f"Document: {plan}\nReview this plan.")
        self.put(plan, "v2\n")
        prompt = self.assertAllowed(self.check(prompt=f"Document: {plan}\nCheck."))["prompt"]
        self.assertIn(os.path.join(ROOT, "skills", "plan", "references", "rubric.md"), prompt)
        self.assertIn("docs/specs/, docs/adrs/, docs/plans/", prompt)

    def test_checker_of_a_plan_may_read_the_practices_it_keeps_to(self):
        plan = "docs/plans/2026-10-29-x.md"
        self.put(plan, "v1\n")
        self.review(agent="sdlc:plan-reviewer", prompt=f"Document: {plan}\nReview this plan.")
        self.put(plan, "v2\n")
        prompt = self.assertAllowed(self.check(prompt=f"Document: {plan}\nCheck."))["prompt"]
        files = prompt.split("=== FILES TO READ ===")[1]
        for practices in ("AGENTS.md", "CLAUDE.md", "docs/practices/"):
            self.assertIn(practices, files)

    def test_checker_of_a_spec_may_read_the_documents_a_reference_could_name(self):
        self.put(SPEC, "v1\n")
        self.review()
        self.put(SPEC, "v2\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn("docs/brief.md, docs/specs/, docs/adrs/, docs/plans/, docs/spikes/", prompt)

    def test_checkers_of_other_documents_may_read_spike_records(self):
        for agent, path in (("adr", "docs/adrs/0001-use-x.md"), ("plan", "docs/plans/2026-10-29-x.md"),
                            ("brief", "docs/brief.md")):
            self.put(path, "v1\n")
            self.review(agent=f"sdlc:{agent}-reviewer", prompt=f"Document: {path}\nReview.")
            self.put(path, "v2\n")
            prompt = self.assertAllowed(self.check(prompt=f"Document: {path}\nCheck."))["prompt"]
            self.assertIn("docs/spikes/", prompt.split("=== END DOCUMENT ===")[-1], agent)

    def test_checker_of_a_spike_record_is_told_the_spike_rubric_and_where_answers_go(self):
        record = "docs/spikes/2026-11-04-x.md"
        self.put(record, "v1\n")
        self.review(agent="sdlc:spike-reviewer", prompt=f"Document: {record}\nReview this spike record's design.")
        self.put(record, "v2\n")
        prompt = self.assertAllowed(self.check(prompt=f"Document: {record}\nCheck."))["prompt"]
        self.assertIn(os.path.join(ROOT, "skills", "spike", "references", "rubric.md"), prompt)
        self.assertIn("docs/specs/, docs/adrs/", prompt)

    def test_a_spike_records_verdict_check_gets_the_verdict_review(self):
        record = "docs/spikes/2026-11-04-x.md"
        design, verdict = REPORT.replace("Story", "One question"), REPORT.replace("Story", "Answer follows")
        reviewer = "sdlc:spike-reviewer"
        check = f"Document: {record}\nCheck the corrections."
        self.put(record, "design v1\n")
        self.review(agent=reviewer, prompt=f"Document: {record}\nReview this spike record's design.", report=design)
        self.put(record, "design v2\n")
        self.assertIn(design, self.assertAllowed(self.check(prompt=check))["prompt"])
        self.assertIsNone(self.agent("PostToolUse", "sdlc:correction-checker", check, response="Result: PASS"))
        self.put(record, "verdict v1\n")
        self.review(agent=reviewer, prompt=f"Document: {record}\nReview this spike record's verdict.",
                    report=verdict, wording=WORDING.replace("rides along", "hits the wall"))
        self.put(record, "verdict v2\n")
        prompt = self.assertAllowed(self.check(prompt=check))["prompt"]
        self.assertIn(verdict, prompt)
        self.assertNotIn(design, prompt)
        self.assertIn("hits the wall", prompt)
        self.assertIn("verdict v1", prompt)
        self.assertNotIn("design v", prompt)

    def test_checker_of_the_brief_may_read_the_documents_a_reference_could_name(self):
        brief = "docs/brief.md"
        self.put(brief, "v1\n")
        self.review(agent="sdlc:brief-reviewer", prompt=f"Document: {brief}\nReview the brief.")
        self.put(brief, "v2\n")
        prompt = self.assertAllowed(self.check(prompt=f"Document: {brief}\nCheck."))["prompt"]
        self.assertIn(os.path.join(ROOT, "skills", "brief", "references", "rubric.md"), prompt)
        self.assertIn("docs/specs/, docs/adrs/, docs/plans/", prompt)

    def test_names_without_the_plugin_prefix_work_too(self):
        self.put(SPEC, "v1\n")
        self.review(agent="spec-reviewer")
        self.put(SPEC, "v2\n")
        self.assertAllowed(self.agent("PreToolUse", "correction-checker",
                                      f"Document: {SPEC}\nCheck."))

    def test_absolute_and_relative_paths_name_the_same_document(self):
        self.put(SPEC, "v1\n")
        self.review(prompt=f"Document: {os.path.join(self.project, SPEC)}\nReview.")
        self.put(SPEC, "v2\n")
        self.assertAllowed(self.check())

    def test_reviewer_without_a_document_line_saves_nothing(self):
        self.put(SPEC, "v1\n")
        self.assertIsNone(self.agent("PreToolUse", "sdlc:spec-reviewer", f"Review the spec at {SPEC}."))
        self.assertEqual(self.saved(), [])

    def test_reviewer_of_a_missing_file_is_refused_and_saves_nothing(self):
        self.assertRefused(self.agent("PreToolUse", "sdlc:spec-reviewer", f"Document: {SPEC}\nReview."),
                           "Can't find")
        self.assertEqual(self.saved(), [])

    def test_a_new_review_replaces_the_last_one(self):
        self.put(SPEC, "v1\n")
        self.review(report="first report")
        self.put(SPEC, "v2\n")
        self.review(report="second report")
        self.put(SPEC, "v3\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn("second report", prompt)
        self.assertNotIn("first report", prompt)
        self.assertIn("=== DOCUMENT AS REVIEWED: " + SPEC + " ===\nv2\n", prompt)

    def test_two_documents_keep_separate_reviews(self):
        other = "docs/specs/payments.spec.md"
        self.put(SPEC, "booking v1\n")
        self.put(other, "payments v1\n")
        self.review(report="booking report")
        self.review(prompt=f"Document: {other}\nReview.", report="payments report")
        self.put(SPEC, "booking v2\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn("booking report", prompt)
        self.assertNotIn("payments", prompt)

    # The language checker runs beside every reviewer

    def test_checker_gets_the_wording_report_word_for_word_in_its_own_block(self):
        self.put(SPEC, "v1\n")
        self.review()
        self.put(SPEC, "v2\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn("=== REVIEW REPORT ===\n" + REPORT + "\n=== END REVIEW REPORT ===", prompt)
        self.assertIn("=== WORDING REPORT ===\n" + WORDING + "\n=== END WORDING REPORT ===", prompt)

    def test_checker_is_told_where_the_plain_words_rule_is(self):
        self.put(SPEC, "v1\n")
        self.review()
        self.put(SPEC, "v2\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        files = prompt.split("=== FILES TO READ ===")[1]
        self.assertIn(os.path.join(ROOT, "docs", "lifecycle.md"), files)
        self.assertIn("Plain words", files)

    def test_both_reports_count_whichever_starts_or_finishes_first(self):
        review = f"Document: {SPEC}\nReview."
        wording = f"Document: {SPEC}\nCheck the wording."
        orders = [
            [("PreToolUse", LANGUAGE), ("PreToolUse", "sdlc:spec-reviewer"),
             ("PostToolUse", "sdlc:spec-reviewer"), ("PostToolUse", LANGUAGE)],
            [("PreToolUse", "sdlc:spec-reviewer"), ("PreToolUse", LANGUAGE),
             ("PostToolUse", LANGUAGE), ("PostToolUse", "sdlc:spec-reviewer")],
            [("PreToolUse", LANGUAGE), ("PostToolUse", LANGUAGE),
             ("PreToolUse", "sdlc:spec-reviewer"), ("PostToolUse", "sdlc:spec-reviewer")],
        ]
        for n, order in enumerate(orders):
            with self.subTest(order=n):
                session = f"order{n}"
                self.put(SPEC, "v1\n")
                for when, agent in order:
                    prompt = wording if agent == LANGUAGE else review
                    response = None
                    if when == "PostToolUse":
                        response = WORDING if agent == LANGUAGE else REPORT
                    out = self.agent(when, agent, prompt, response=response, session=session)
                    if when == "PreToolUse":
                        self.assertStarted(out)
                    else:
                        self.assertIsNone(out)
                self.put(SPEC, "v2\n")
                prompt = self.assertAllowed(self.check(session=session))["prompt"]
                self.assertIn(REPORT, prompt)
                self.assertIn(WORDING, prompt)
                self.assertIn("=== DOCUMENT AS REVIEWED: " + SPEC + " ===\nv1\n", prompt)

    def test_checker_without_the_wording_report_is_refused(self):
        self.put(SPEC, "v1\n")
        self.review(wording=None)
        self.put(SPEC, "v2\n")
        self.assertRefused(self.check(), "language checker")

    def test_checker_with_only_the_wording_report_is_refused(self):
        self.put(SPEC, "v1\n")
        self.language()
        self.put(SPEC, "v2\n")
        self.assertRefused(self.check(), "No review")

    def test_wording_report_of_another_version_does_not_count(self):
        self.put(SPEC, "v1\n")
        self.review(wording=None)
        self.put(SPEC, "v2\n")
        self.language()
        self.put(SPEC, "v3\n")
        self.assertRefused(self.check(), "No review")

    def test_a_new_review_of_unchanged_text_replaces_both_reports(self):
        self.put(SPEC, "v1\n")
        self.review(report="first report", wording="first wording")
        self.review(report="second report", wording="second wording")
        self.put(SPEC, "v2\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn("second report", prompt)
        self.assertIn("second wording", prompt)
        self.assertNotIn("first", prompt)

    def test_wording_of_a_feedback_draft_counts(self):
        self.review(agent="sdlc:feedback-reviewer", prompt=feedback_request(DRAFT))
        corrected = DRAFT.replace("line two", "line 2")
        prompt = self.assertAllowed(self.check(prompt=feedback_request(corrected)))["prompt"]
        self.assertIn("=== WORDING REPORT ===\n" + WORDING, prompt)

    def test_language_checker_names_without_the_plugin_prefix_work_too(self):
        self.put(SPEC, "v1\n")
        self.review(wording=None)
        self.assertAllowed(self.agent("PreToolUse", "language-checker", f"Document: {SPEC}\nGo."))
        self.assertIsNone(self.agent("PostToolUse", "language-checker", f"Document: {SPEC}\nGo.",
                                     response=WORDING))
        self.put(SPEC, "v2\n")
        self.assertAllowed(self.check())

    def test_a_late_report_from_an_earlier_run_does_not_count(self):
        v1 = f"Document: {SPEC}\nCheck the wording."
        self.put(SPEC, "v1\n")
        self.assertAllowed(self.agent("PreToolUse", LANGUAGE, v1, call="old"))
        self.put(SPEC, "v2\n")
        self.assertAllowed(self.agent("PreToolUse", "sdlc:spec-reviewer", v1, call="rev"))
        self.assertAllowed(self.agent("PreToolUse", LANGUAGE, v1, call="new"))
        self.assertIsNone(self.agent("PostToolUse", "sdlc:spec-reviewer", v1, response=REPORT, call="rev"))
        self.assertIsNone(self.agent("PostToolUse", LANGUAGE, v1, response="current wording", call="new"))
        self.assertIsNone(self.agent("PostToolUse", LANGUAGE, v1, response="stale wording", call="old"))
        self.put(SPEC, "v3\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn("current wording", prompt)
        self.assertNotIn("stale wording", prompt)

    def test_refusal_for_a_missing_wording_report_never_asks_for_another_review(self):
        self.put(SPEC, "v1\n")
        self.review(wording=None)
        self.put(SPEC, "v2\n")
        out = self.check()
        self.assertRefused(out, "language checker")
        reason = out["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("show the person", reason)
        self.assertNotIn("Start the language checker", reason)

    def test_a_saved_record_in_another_shape_counts_as_no_review(self):
        self.put(SPEC, "v1\n")
        self.review()
        for path in self.saved():
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"reviewer": "spec-reviewer", "text": "v1\n", "report": "old shape"}, f)
        self.put(SPEC, "v2\n")
        self.assertRefused(self.check(), "No review")
        for path in self.saved():
            with open(path, "w", encoding="utf-8") as f:
                f.write("[1, 2]")
        self.assertAllowed(self.agent("PreToolUse", "sdlc:spec-reviewer", f"Document: {SPEC}\nGo."))
        self.assertRefused(self.check(), "No review")

    def test_wording_of_a_slightly_different_copy_of_the_same_review_still_joins(self):
        # /feedback types the draft into both requests; a stray space must not lose the review.
        self.assertIsNone(self.agent("PreToolUse", "sdlc:feedback-reviewer", feedback_request(DRAFT)))
        self.assertIsNone(self.agent("PreToolUse", LANGUAGE, feedback_request(DRAFT + " ")))
        self.assertIsNone(self.agent("PostToolUse", "sdlc:feedback-reviewer", feedback_request(DRAFT), response=REPORT))
        self.assertIsNone(self.agent("PostToolUse", LANGUAGE, feedback_request(DRAFT + " "), response=WORDING))
        corrected = DRAFT.replace("line two", "line 2")
        prompt = self.assertAllowed(self.check(prompt=feedback_request(corrected)))["prompt"]
        self.assertIn("=== DOCUMENT AS REVIEWED: feedback draft ===\n" + DRAFT, prompt)
        self.assertIn(WORDING, prompt)

    def test_a_second_language_check_during_a_review_leaves_it_alone(self):
        self.put(SPEC, "v1\n")
        self.review()
        self.put(SPEC, "v2\n")
        self.language(prompt=f"Document: {SPEC}\nCheck my wording fixes.", wording="second wording")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn(REPORT, prompt)
        self.assertIn(WORDING, prompt)
        self.assertNotIn("second wording", prompt)

    def test_a_new_review_may_start_with_the_language_checker(self):
        self.put(SPEC, "v1\n")
        self.review(report="first report", wording="first wording")
        self.put(SPEC, "v2\n")
        self.language(prompt=f"Document: {SPEC}\nCheck the wording.", wording="second wording")
        self.review(report="second report", wording=None)
        self.put(SPEC, "v3\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn("second report", prompt)
        self.assertIn("second wording", prompt)
        self.assertNotIn("first", prompt)

    # Runs that Claude Code moves to the background

    def launch(self, agent, prompt, agent_id, session=None, **extra):
        """Start an agent that Claude Code runs in the background: its tool result is a launch notice."""
        out = self.agent("PreToolUse", agent, prompt, session=session, **extra)
        self.assertIsNone(self.run_hook({
            "hook_event_name": "PostToolUse", "session_id": session or self.session, "tool_name": "Agent",
            "tool_use_id": f"{agent}-{prompt}",
            "tool_input": dict({"subagent_type": agent, "prompt": prompt, "description": "a task"}, **extra),
            "tool_response": {"isAsync": True, "status": "async_launched", "agentId": agent_id,
                              "description": "a task", "prompt": prompt, "outputFile": "/tmp/out"}}))
        return out

    def stopped(self, agent, agent_id, report, session=None):
        """The background agent finishes: Claude Code sends SubagentStop with its last message."""
        return self.run_hook({"hook_event_name": "SubagentStop", "session_id": session or self.session,
                              "agent_id": agent_id, "agent_type": agent, "stop_hook_active": False,
                              "last_assistant_message": report})

    def test_reports_of_background_runs_reach_the_checker_word_for_word(self):
        self.put(SPEC, "v1\n")
        review, check = f"Document: {SPEC}\nReview this spec.", f"Document: {SPEC}\nCheck the wording."
        self.assertStarted(self.launch("sdlc:spec-reviewer", review, "a1"))
        self.assertStarted(self.launch(LANGUAGE, check, "a2"))
        self.assertIsNone(self.stopped("sdlc:spec-reviewer", "a1", REPORT))
        self.assertIsNone(self.stopped(LANGUAGE, "a2", WORDING))
        self.put(SPEC, "v2\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn("=== REVIEW REPORT ===\n" + REPORT + "\n=== END REVIEW REPORT ===", prompt)
        self.assertIn("=== WORDING REPORT ===\n" + WORDING + "\n=== END WORDING REPORT ===", prompt)
        self.assertIn("=== DOCUMENT AS REVIEWED: " + SPEC + " ===\nv1\n", prompt)

    def test_a_background_report_counts_when_the_agent_stops_before_its_launch_is_seen(self):
        self.put(SPEC, "v1\n")
        review, check = f"Document: {SPEC}\nReview this spec.", f"Document: {SPEC}\nCheck the wording."
        self.agent("PreToolUse", "sdlc:spec-reviewer", review)
        self.agent("PreToolUse", LANGUAGE, check)
        self.assertIsNone(self.stopped("sdlc:spec-reviewer", "a1", REPORT))
        self.assertIsNone(self.stopped(LANGUAGE, "a2", WORDING))
        for agent, prompt, agent_id in (("sdlc:spec-reviewer", review, "a1"), (LANGUAGE, check, "a2")):
            self.run_hook({"hook_event_name": "PostToolUse", "session_id": self.session,
                           "tool_name": "Agent", "tool_use_id": f"{agent}-{prompt}",
                           "tool_input": {"subagent_type": agent, "prompt": prompt},
                           "tool_response": {"status": "async_launched", "agentId": agent_id}})
        self.put(SPEC, "v2\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn(REPORT, prompt)
        self.assertIn(WORDING, prompt)

    def test_one_part_in_the_foreground_and_one_in_the_background_both_count(self):
        self.put(SPEC, "v1\n")
        review = f"Document: {SPEC}\nReview this spec."
        self.agent("PreToolUse", "sdlc:spec-reviewer", review)
        self.agent("PostToolUse", "sdlc:spec-reviewer", review, response=REPORT)
        self.launch(LANGUAGE, f"Document: {SPEC}\nCheck the wording.", "a2")
        self.stopped(LANGUAGE, "a2", WORDING)
        self.put(SPEC, "v2\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn(REPORT, prompt)
        self.assertIn(WORDING, prompt)

    def test_a_launch_notice_alone_is_no_report(self):
        self.put(SPEC, "v1\n")
        self.launch("sdlc:spec-reviewer", f"Document: {SPEC}\nReview this spec.", "a1")
        self.launch(LANGUAGE, f"Document: {SPEC}\nCheck the wording.", "a2")
        self.put(SPEC, "v2\n")
        self.assertRefused(self.check(), "stop and show the person")
        record = [p for p in self.saved() if not p.endswith("background-runs.json")]
        for path in record:
            with open(path, encoding="utf-8") as f:
                self.assertNotIn("async_launched", f.read())

    def test_a_background_agent_that_stops_with_no_report_is_no_report(self):
        self.put(SPEC, "v1\n")
        self.launch("sdlc:spec-reviewer", f"Document: {SPEC}\nReview this spec.", "a1")
        self.stopped("sdlc:spec-reviewer", "a1", "")
        self.language()
        self.put(SPEC, "v2\n")
        self.assertRefused(self.check(), "stop and show the person")

    def test_an_agent_the_relay_never_saw_start_changes_nothing(self):
        self.assertIsNone(self.stopped("sdlc:spec-reviewer", "a9", REPORT))
        self.assertIsNone(self.stopped("Explore", "a8", REPORT))
        self.assertEqual(self.saved(), [])
        self.put(SPEC, "v1\n")
        self.review()
        before = {p: open(p, encoding="utf-8").read() for p in self.saved()}
        self.assertIsNone(self.stopped("sdlc:spec-reviewer", "a7", "another report"))
        self.assertEqual({p: open(p, encoding="utf-8").read() for p in self.saved()
                          if not p.endswith("background-runs.json")}, before)
        self.put(SPEC, "v2\n")
        self.assertNotIn("another report", self.assertAllowed(self.check())["prompt"])

    def test_a_background_report_of_another_session_does_not_count(self):
        self.put(SPEC, "v1\n")
        self.launch("sdlc:spec-reviewer", f"Document: {SPEC}\nReview this spec.", "a1")
        self.stopped("sdlc:spec-reviewer", "a1", REPORT, session="other")
        self.language()
        self.put(SPEC, "v2\n")
        self.assertRefused(self.check(), "stop and show the person")

    def test_an_agent_that_stops_again_has_its_last_report_kept(self):
        # Another plugin's SubagentStop hook may keep an agent going; it then stops again.
        self.put(SPEC, "v1\n")
        self.launch("sdlc:spec-reviewer", f"Document: {SPEC}\nReview this spec.", "a1")
        self.stopped("sdlc:spec-reviewer", "a1", "an early line")
        self.stopped("sdlc:spec-reviewer", "a1", REPORT)
        self.language()
        self.put(SPEC, "v2\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn(REPORT, prompt)
        self.assertNotIn("an early line", prompt)

    def held(self):
        path = [p for p in self.saved() if p.endswith("background-runs.json")]
        if not path:
            return {}
        with open(path[0], encoding="utf-8") as f:
            return json.load(f)["stopped"]

    def test_a_foreground_run_leaves_no_report_held(self):
        # SubagentStop fires for foreground runs too, before their tool result.
        self.put(SPEC, "v1\n")
        review = f"Document: {SPEC}\nReview this spec."
        self.agent("PreToolUse", "sdlc:spec-reviewer", review)
        self.stopped("sdlc:spec-reviewer", "a1", REPORT)
        self.post("sdlc:spec-reviewer", review, {"status": "completed", "agentId": "a1",
                                                 "content": [{"type": "text", "text": REPORT}]})
        self.assertEqual(self.held(), {})

    def test_only_the_last_few_reports_are_held(self):
        self.put(SPEC, "v1\n")
        self.agent("PreToolUse", "sdlc:spec-reviewer", f"Document: {SPEC}\nReview this spec.")
        for n in range(8):
            self.stopped("sdlc:spec-reviewer", f"a{n}", REPORT)
        self.assertEqual(sorted(self.held()), ["a3", "a4", "a5", "a6", "a7"])

    def test_reviewer_or_language_checker_asked_to_run_in_the_background_is_allowed(self):
        self.put(SPEC, "v1\n")
        review, check = f"Document: {SPEC}\nReview.", f"Document: {SPEC}\nCheck the wording."
        self.assertStarted(self.launch("sdlc:spec-reviewer", review, "a1", run_in_background=True))
        self.assertStarted(self.launch(LANGUAGE, check, "a2", run_in_background=True))
        self.stopped("sdlc:spec-reviewer", "a1", REPORT)
        self.stopped(LANGUAGE, "a2", WORDING)
        self.put(SPEC, "v2\n")
        self.assertAllowed(self.check())

    def test_without_tool_use_ids_both_reports_still_count(self):
        self.put(SPEC, "v1\n")
        for when, agent, response in [("PreToolUse", "sdlc:spec-reviewer", None),
                                      ("PreToolUse", LANGUAGE, None),
                                      ("PostToolUse", "sdlc:spec-reviewer", REPORT),
                                      ("PostToolUse", LANGUAGE, WORDING)]:
            event = {"hook_event_name": when, "session_id": self.session, "tool_name": "Agent",
                     "tool_input": {"subagent_type": agent, "prompt": f"Document: {SPEC}\nGo."}}
            if response:
                event["tool_response"] = {"content": [{"type": "text", "text": response}]}
                self.assertIsNone(self.run_hook(event))
            else:
                self.assertStarted(self.run_hook(event))
        self.put(SPEC, "v2\n")
        self.assertAllowed(self.check())

    def test_no_refusal_asks_for_a_second_review(self):
        self.put(SPEC, "v1\n")
        for out in (self.check(), self.check(prompt="Check the corrections.")):
            reason = out["hookSpecificOutput"]["permissionDecisionReason"]
            self.assertNotIn("Run the review", reason)

    def test_a_part_started_again_after_a_run_with_no_report_joins_the_same_review(self):
        self.put(SPEC, "v1\n")
        prompt = f"Document: {SPEC}\nReview."
        self.assertAllowed(self.agent("PreToolUse", "sdlc:spec-reviewer", prompt, call="r1"))
        self.assertAllowed(self.agent("PreToolUse", LANGUAGE, prompt, call="l1"))
        self.assertIsNone(self.agent("PostToolUse", "sdlc:spec-reviewer", prompt, response=REPORT, call="r1"))
        # l1 never finishes; it is started again as l2.
        self.assertAllowed(self.agent("PreToolUse", LANGUAGE, prompt, call="l2"))
        self.assertIsNone(self.agent("PostToolUse", LANGUAGE, prompt, response=WORDING, call="l2"))
        self.put(SPEC, "v2\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn(REPORT, prompt)
        self.assertIn(WORDING, prompt)

    def test_the_newest_complete_review_outlasts_later_unfinished_ones(self):
        self.put(SPEC, "v1\n")
        self.review()
        for version in ("v2\n", "v3\n", "v4\n"):
            self.put(SPEC, version)
            self.language(wording="wording of " + version)
        self.put(SPEC, "v5\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn(REPORT, prompt)
        self.assertIn(WORDING, prompt)

    def test_a_saved_review_with_reports_of_the_wrong_type_counts_as_no_review(self):
        self.put(SPEC, "v1\n")
        self.review()
        for path in self.saved():
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"reviews": [{"text": "v1\n", "started": {"a": "reviewer", "b": "language"},
                                        "reports": {"spec-reviewer": 5, "language-checker": ["x"]}}]}, f)
        self.put(SPEC, "v2\n")
        self.assertRefused(self.check(), "No review")

    def test_a_correction_that_only_changes_spacing_still_counts(self):
        # In Markdown a blank line or an indent can be the correction.
        self.put(SPEC, "Intro\n- item\n")
        self.review()
        self.put(SPEC, "Intro\n\n- item\n")
        self.assertAllowed(self.check())

    def test_the_reviewers_copy_of_a_feedback_draft_is_the_one_kept(self):
        self.assertIsNone(self.agent("PreToolUse", LANGUAGE, feedback_request(DRAFT + " ")))
        self.assertIsNone(self.agent("PreToolUse", "sdlc:feedback-reviewer", feedback_request(DRAFT)))
        self.assertIsNone(self.agent("PostToolUse", LANGUAGE, feedback_request(DRAFT + " "), response=WORDING))
        self.assertIsNone(self.agent("PostToolUse", "sdlc:feedback-reviewer", feedback_request(DRAFT), response=REPORT))
        self.assertRefused(self.check(prompt=feedback_request(DRAFT)), "unchanged")

    def test_a_newer_review_missing_a_report_is_not_covered_by_an_older_one(self):
        self.put(SPEC, "v1\n")
        self.review()
        self.put(SPEC, "v2\n")
        self.review(report="", wording="second wording")
        self.put(SPEC, "v3\n")
        self.assertRefused(self.check(), "No review")

    def test_reports_of_agents_this_version_does_not_know_are_ignored(self):
        self.put(SPEC, "v1\n")
        self.review()
        for path in self.saved():
            with open(path, encoding="utf-8") as f:
                saved = json.load(f)
            saved["reviews"][0]["reports"]["old-reviewer"] = "old"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(saved, f)
        self.put(SPEC, "v2\n")
        self.assertAllowed(self.check())

    def test_a_check_with_nothing_saved_leaves_no_folder_behind(self):
        self.put(SPEC, "v1\n")
        self.check()
        self.agent("PostToolUse", "sdlc:correction-checker", f"Document: {SPEC}\nCheck.", response="ok")
        self.assertFalse(os.path.exists(os.path.join(self.data, "reviews")))

    def test_background_runs_are_not_refused_when_nothing_is_saved(self):
        self.put(SPEC, "v1\n")
        event = {"hook_event_name": "PreToolUse", "session_id": self.session, "tool_name": "Agent",
                 "tool_input": {"subagent_type": LANGUAGE, "prompt": f"Document: {SPEC}\nGo.",
                                "run_in_background": True}}
        self.assertTrue(self.assertAllowed(self.run_hook(event, data=False))["run_in_background"])

    def test_a_null_text_block_in_a_reply_never_blocks(self):
        self.put(SPEC, "v1\n")
        self.assertAllowed(self.agent("PreToolUse", "sdlc:spec-reviewer", f"Document: {SPEC}\nGo."))
        event = {"hook_event_name": "PostToolUse", "session_id": self.session, "tool_name": "Agent",
                 "tool_use_id": f"sdlc:spec-reviewer-Document: {SPEC}\nGo.",
                 "tool_input": {"subagent_type": "sdlc:spec-reviewer", "prompt": f"Document: {SPEC}\nGo."},
                 "tool_response": {"content": [{"type": "text", "text": None}]}}
        self.assertIsNone(self.run_hook(event))

    # Project threads: the report comes through a hand-back

    def post(self, agent, prompt, response):
        """Finish an agent run whose tool result is given whole."""
        return self.run_hook({"hook_event_name": "PostToolUse", "session_id": self.session,
                              "tool_name": "Agent", "tool_use_id": f"{agent}-{prompt}",
                              "tool_input": {"subagent_type": agent, "prompt": prompt},
                              "tool_response": response})

    def test_reports_handed_back_reach_the_checker_word_for_word(self):
        self.put(SPEC, "v1\n")
        review, check = f"Document: {SPEC}\nReview this spec.", f"Document: {SPEC}\nCheck the wording."
        self.agent("PreToolUse", "sdlc:spec-reviewer", review)
        self.post("sdlc:spec-reviewer", review, handed_back(REPORT))
        self.agent("PreToolUse", LANGUAGE, check)
        self.post(LANGUAGE, check, handed_back(WORDING))
        self.put(SPEC, "v2\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertIn("=== REVIEW REPORT ===\n" + REPORT + "\n=== END REVIEW REPORT ===", prompt)
        self.assertIn("=== WORDING REPORT ===\n" + WORDING + "\n=== END WORDING REPORT ===", prompt)
        self.assertNotIn("SubagentHandback", prompt)

    def test_a_hand_back_that_delivered_nothing_is_no_report(self):
        self.put(SPEC, "v1\n")
        review = f"Document: {SPEC}\nReview this spec."
        self.agent("PreToolUse", "sdlc:spec-reviewer", review)
        self.post("sdlc:spec-reviewer", review, {"handback": "withheld",
                                                 "content": [{"type": "text", "text": POINTER}]})
        self.language()
        self.put(SPEC, "v2\n")
        self.assertRefused(self.check(), "stop and show the person")

    # /feedback: the draft is never on disk

    def test_feedback_draft_is_taken_from_the_requests(self):
        self.review(agent="sdlc:feedback-reviewer", prompt=feedback_request(DRAFT))
        corrected = DRAFT.replace("line two", "line 2")
        prompt = self.assertAllowed(self.check(prompt=feedback_request(corrected)))["prompt"]
        self.assertIn("=== DOCUMENT AS REVIEWED: feedback draft ===\n" + DRAFT, prompt)
        self.assertIn("=== DRAFT ===\n" + corrected, prompt)
        self.assertIn(os.path.join(ROOT, "skills", "feedback", "references", "rubric.md"), prompt)
        self.assertNotIn("docs/brief.md", prompt)

    def test_unchanged_feedback_draft_is_refused(self):
        self.review(agent="sdlc:feedback-reviewer", prompt=feedback_request(DRAFT))
        self.assertRefused(self.check(prompt=feedback_request(DRAFT)), "unchanged")

    def test_feedback_review_without_a_draft_saves_nothing(self):
        self.review(agent="sdlc:feedback-reviewer", prompt="Document: feedback draft\nKind: bug\n")
        self.assertEqual(self.saved(), [])

    # When the checker is refused

    def test_checker_without_a_document_line_is_refused(self):
        self.assertRefused(self.check(prompt="Check the corrections."), "Document:")

    def test_checker_with_no_review_on_record_is_refused(self):
        self.put(SPEC, "v1\n")
        self.assertRefused(self.check(), "No review")

    def test_checker_before_the_review_finished_is_refused(self):
        self.put(SPEC, "v1\n")
        self.assertAllowed(self.agent("PreToolUse", "sdlc:spec-reviewer", f"Document: {SPEC}\nReview."))
        self.put(SPEC, "v2\n")
        self.assertRefused(self.check(), "No review")

    def test_checker_after_a_review_with_no_report_is_refused(self):
        self.put(SPEC, "v1\n")
        self.review(report="")
        self.put(SPEC, "v2\n")
        self.assertRefused(self.check(), "No review")

    def test_checker_on_an_unchanged_document_is_refused(self):
        self.put(SPEC, "v1\n")
        self.review()
        self.assertRefused(self.check(), "unchanged")

    def test_review_in_another_session_does_not_count(self):
        self.put(SPEC, "v1\n")
        self.review(session="other")
        self.put(SPEC, "v2\n")
        self.assertRefused(self.check(), "No review")

    # Clearing up

    def test_checker_finishing_deletes_only_its_documents_review(self):
        other = "docs/specs/payments.spec.md"
        self.put(SPEC, "v1\n")
        self.put(other, "p1\n")
        self.review()
        self.review(prompt=f"Document: {other}\nReview.")
        self.put(SPEC, "v2\n")
        self.put(other, "p2\n")
        prompt = f"Document: {SPEC}\nCheck."
        self.assertAllowed(self.check(prompt=prompt))
        self.assertIsNone(self.agent("PostToolUse", "sdlc:correction-checker", prompt, response="Result: PASS"))
        self.assertRefused(self.check(prompt=prompt), "No review")
        self.assertAllowed(self.check(prompt=f"Document: {other}\nCheck."))

    def test_a_review_survives_the_session_ending_so_a_resumed_session_can_check_it(self):
        # Issue #37: `claude --resume`, or a restarted container, brings the same session back.
        self.put(SPEC, "v1\n")
        self.review()
        self.assertIsNone(self.run_hook({"hook_event_name": "SessionEnd", "session_id": self.session}))
        self.put(SPEC, "v2\n")
        self.assertAllowed(self.check())

    def test_saving_a_review_deletes_another_sessions_reviews_once_they_are_a_month_old(self):
        self.put(SPEC, "v1\n")
        self.review(session="old")
        self.review(session="recent")
        month = time.time() - 31 * 24 * 60 * 60
        os.utime(os.path.join(self.data, "reviews", "old"), (month, month))
        self.review()
        self.assertFalse(os.path.exists(os.path.join(self.data, "reviews", "old")))
        self.assertTrue(os.path.exists(os.path.join(self.data, "reviews", "recent")))

    def test_nothing_is_left_once_the_checker_finishes(self):
        self.put(SPEC, "v1\n")
        self.review()
        self.put(SPEC, "v2\n")
        self.check()
        self.agent("PostToolUse", "sdlc:correction-checker", f"Document: {SPEC}\nCheck.", response="ok")
        self.assertEqual(self.saved(), [])

    # Several files named on one Document: line (ADR 0018)

    def multi(self, core="## Practices\nv1\n", topic="# Testing\nv1\n"):
        self.put("AGENTS.md", core)
        self.put(TOPIC, topic)

    def test_several_files_are_saved_and_handed_over_each_marked_with_its_path(self):
        self.multi()
        self.review(agent="sdlc:practices-reviewer", prompt=f"Document: {PAIR}\nReview.")
        self.put(TOPIC, "# Testing\nv2\n")
        prompt = self.assertAllowed(self.check(prompt=f"Document: {PAIR}\nCheck."))["prompt"]
        reviewed = prompt.split("=== DOCUMENT AS REVIEWED: ")[1].split("=== END DOCUMENT ===")[0]
        self.assertIn("=== FILE: AGENTS.md ===\n## Practices\nv1\n\n=== END FILE ===", reviewed)
        self.assertIn(f"=== FILE: {TOPIC} ===\n# Testing\nv1\n\n=== END FILE ===", reviewed)
        self.assertNotIn("v2", reviewed)
        self.assertIn(os.path.join(ROOT, "skills", "practices", "references", "rubric.md"), prompt)

    def test_a_change_to_any_one_of_the_files_lets_the_checker_start(self):
        self.multi()
        self.review(agent="sdlc:practices-reviewer", prompt=f"Document: {PAIR}\nReview.")
        self.put("AGENTS.md", "## Practices\nv2\n")
        self.assertAllowed(self.check(prompt=f"Document: {PAIR}\nCheck."))

    def test_the_checker_is_refused_when_none_of_the_files_changed(self):
        self.multi()
        self.review(agent="sdlc:practices-reviewer", prompt=f"Document: {PAIR}\nReview.")
        self.assertRefused(self.check(prompt=f"Document: {PAIR}\nCheck."), "unchanged")

    def test_the_order_of_the_names_does_not_matter(self):
        self.multi()
        self.review(agent="sdlc:practices-reviewer", prompt=f"Document: {PAIR}\nReview.", wording=None)
        self.language(prompt=f"Document: {TOPIC}, AGENTS.md\nCheck the wording.")
        self.put(TOPIC, "# Testing\nv2\n")
        self.assertAllowed(self.check(prompt=f"Document: {TOPIC},AGENTS.md\nCheck."))

    def test_a_file_missing_when_reviewed_is_marked_missing_and_still_reviewed(self):
        self.put("AGENTS.md", "## Practices\nv1\n")
        self.review(agent="sdlc:practices-reviewer", prompt=f"Document: {PAIR}\nReview.")
        self.put(TOPIC, "# Testing\nnew\n")
        prompt = self.assertAllowed(self.check(prompt=f"Document: {PAIR}\nCheck."))["prompt"]
        self.assertIn(f"=== FILE: {TOPIC} ===\n(missing)\n=== END FILE ===", prompt)

    def test_when_every_named_file_is_missing_the_review_is_refused_and_nothing_saved(self):
        self.assertRefused(self.agent("PreToolUse", "sdlc:practices-reviewer", f"Document: {PAIR}\nReview."),
                           "Can't find")
        self.assertEqual(self.saved(), [])

    def test_a_single_file_whose_name_holds_a_comma_is_one_document(self):
        odd = "docs/specs/a, b.spec.md"
        self.put(odd, "v1\n")
        self.review(prompt=f"Document: {odd}\nReview.")
        self.put(odd, "v2\n")
        prompt = self.assertAllowed(self.check(prompt=f"Document: {odd}\nCheck."))["prompt"]
        self.assertIn(f"=== DOCUMENT AS REVIEWED: {odd} ===\nv1\n\n=== END DOCUMENT ===", prompt)
        self.assertNotIn("=== FILE:", prompt)

    def test_a_single_path_is_handed_over_without_file_markers(self):
        self.put(SPEC, "v1\n")
        self.review()
        self.put(SPEC, "v2\n")
        prompt = self.assertAllowed(self.check())["prompt"]
        self.assertNotIn("=== FILE:", prompt)

    # Finding the repository (ADR 0022)

    def repository(self, name="invoice-tool"):
        """A git repository inside the folder Claude Code was started in."""
        top = os.path.join(self.project, name)
        os.makedirs(os.path.join(top, ".git"))
        return top

    def put_in(self, top, path, text):
        full = os.path.join(top, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)
        return full

    def test_a_full_path_from_a_folder_above_names_the_document_relative_to_its_repository(self):
        top = self.repository()
        full = self.put_in(top, SPEC, "v1\n")
        for agent in ("sdlc:spec-reviewer", LANGUAGE):
            with self.subTest(agent=agent):
                prompt = self.assertStarted(self.agent("PreToolUse", agent, f"Document: {full}\nReview this spec."),
                                            project=top)
                self.assertEqual(prompt.splitlines()[2:], ["Review this spec."])

    def test_a_review_from_a_folder_above_reaches_the_checker(self):
        top = self.repository()
        full = self.put_in(top, SPEC, "# Booking\n\nAs reviewed.\n")
        self.review(prompt=f"Document: {full}\nReview this spec.")
        self.put_in(top, SPEC, "# Booking\n\nCorrected.\n")
        prompt = self.assertStarted(self.check(prompt=f"Document: {full}\nCheck the corrections."), project=top)
        self.assertIn("=== REVIEW REPORT ===\n" + REPORT, prompt)
        self.assertIn(f"=== DOCUMENT AS REVIEWED: {SPEC} ===\n# Booking\n\nAs reviewed.\n", prompt)

    def test_a_relative_path_is_read_from_the_repository_line(self):
        top = self.repository()
        full = self.put_in(top, SPEC, "v1\n")
        self.review(prompt=f"Document: {full}\nReview this spec.")
        self.put_in(top, SPEC, "v2\n")
        rewritten = f"Document: {SPEC}\nRepository: {top}\nCheck the corrections."
        prompt = self.assertStarted(self.check(prompt=rewritten), project=top)
        self.assertEqual(prompt.count("Repository:"), 1)
        self.assertIn(f"=== DOCUMENT AS REVIEWED: {SPEC} ===\nv1\n", prompt)

    def test_the_review_and_the_check_name_the_same_document_however_it_is_given(self):
        self.put(SPEC, "v1\n")
        self.review(prompt=f"Document: {os.path.join(self.project, SPEC)}\nReview.")
        self.put(SPEC, "v2\n")
        self.assertStarted(self.check(prompt=f"Document: {SPEC}\nCheck."))

    def test_several_files_by_full_path_are_named_relative_to_their_repository(self):
        top = self.repository()
        agents = self.put_in(top, "AGENTS.md", "## Practices\n")
        topic = self.put_in(top, TOPIC, "# Testing\n")
        out = self.agent("PreToolUse", "sdlc:practices-reviewer", f"Document: {topic}, {agents}\nReview.")
        self.assertStarted(out, document=PAIR, project=top)

    def test_a_document_that_cannot_be_found_is_refused_for_every_review_agent(self):
        for agent in ("sdlc:spec-reviewer", LANGUAGE, "sdlc:correction-checker"):
            with self.subTest(agent=agent):
                out = self.agent("PreToolUse", agent, f"Document: {SPEC}\nReview this spec.")
                self.assertRefused(out, "Can't find docs/specs/booking.spec.md")
                self.assertIn("full path", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_files_in_two_repositories_are_refused(self):
        one = self.put_in(self.repository("one"), "AGENTS.md", "## Practices\n")
        two = self.put_in(self.repository("two"), TOPIC, "# Testing\n")
        self.assertRefused(self.agent("PreToolUse", "sdlc:practices-reviewer", f"Document: {one}, {two}\nReview."),
                           "different repositories")

    def test_a_missing_file_in_another_repository_is_refused(self):
        one = self.put_in(self.repository("one"), "AGENTS.md", "## Practices\n")
        missing = os.path.join(self.repository("two"), TOPIC)
        self.assertRefused(self.agent("PreToolUse", "sdlc:practices-reviewer", f"Document: {one}, {missing}\nReview."),
                           "outside")

    def test_a_report_still_counts_when_its_document_moved_while_the_agent_ran(self):
        top = self.repository()
        full = self.put_in(top, SPEC, "v1\n")
        started = self.assertStarted(self.agent("PreToolUse", "sdlc:spec-reviewer", f"Document: {full}\nGo.",
                                                call="r1"), project=top)
        os.remove(full)
        self.assertIsNone(self.agent("PostToolUse", "sdlc:spec-reviewer", started, response=REPORT, call="r1"))
        self.assertEqual(len(self.saved()), 1)
        with open(self.saved()[0], encoding="utf-8") as f:
            self.assertEqual(json.load(f)["reviews"][-1]["reports"]["spec-reviewer"], REPORT)

    def test_outside_any_git_repository_the_project_folder_stands_in(self):
        self.put(SPEC, "v1\n")
        self.assertStarted(self.agent("PreToolUse", "sdlc:spec-reviewer",
                                      f"Document: {os.path.join(self.project, SPEC)}\nReview."))

    def test_the_request_is_rewritten_even_when_nothing_is_saved(self):
        top = self.repository()
        full = self.put_in(top, SPEC, "v1\n")
        event = {"hook_event_name": "PreToolUse", "session_id": self.session, "tool_name": "Agent",
                 "tool_input": {"subagent_type": "sdlc:spec-reviewer", "prompt": f"Document: {full}\nGo."}}
        self.assertStarted(self.run_hook(event, data=False), project=top)

    def test_a_feedback_draft_is_left_as_it_is(self):
        self.assertIsNone(self.agent("PreToolUse", "sdlc:feedback-reviewer", feedback_request(DRAFT)))

    # Everything else is left alone

    def test_other_agents_and_tools_are_left_alone(self):
        self.put(SPEC, "v1\n")
        self.assertIsNone(self.agent("PreToolUse", "general-purpose", f"Document: {SPEC}\nGo."))
        self.assertIsNone(self.run_hook({"hook_event_name": "PreToolUse", "session_id": self.session,
                                         "tool_name": "Bash", "tool_input": {"command": "ls"}}))
        self.assertEqual(self.saved(), [])

    def test_malformed_input_never_blocks(self):
        self.assertIsNone(self.run_hook(None, raw="not json"))
        self.assertIsNone(self.run_hook(None, raw="[]"))
        self.assertIsNone(self.run_hook({"hook_event_name": "PreToolUse", "tool_name": "Agent",
                                         "tool_input": "oops"}))

    def test_help_describes_the_hook(self):
        done = subprocess.run([sys.executable, SCRIPT, "--help"], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0)
        self.assertIn("correction checker", done.stdout)


if __name__ == "__main__":
    unittest.main()
