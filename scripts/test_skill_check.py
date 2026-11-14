import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "skill_check.py")
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
from skill_check import (AGENT_RULE, ASK_RULE, BUILD_ASK_RULE, BUILD_PATH_RULE, REPORT_RULE, ASK_SKILLS, CORRECT_RULES, DOCUMENT_SKILLS, PATH_RULE, PROPOSED_RULE,  # noqa: E402
                         QUESTIONS_RULE, REPORT_RULES, REVIEW_RULE, SHOW_RULE,
                         SIGNOFF_RULE, STATUS_SKILLS, TYPE_RULE, DATE_RULE, DIAGRAM_SKILLS,
                         diagram_rules, holds)

DESCRIPTION = "Write a thing. Use whenever someone wants a thing."
STEPS = "\n\n".join(CORRECT_RULES)


def skill_md(name="demo", description=DESCRIPTION, body="# Demo\n\nDo the thing.\n"):
    return f"---\nname: {name}\ndescription: {description}\n---\n\n{body}"


class SkillCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def put_agent(self, name, text):
        path = os.path.join(self.tmp.name, "agents", name + ".md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)

    def put(self, folder, text):
        path = os.path.join(self.tmp.name, "skills", folder, "SKILL.md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)

    def check(self, root=None):
        return subprocess.run([sys.executable, SCRIPT, root or self.tmp.name],
                              capture_output=True, text=True)

    def assertFails(self, needle):
        done = self.check()
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn(needle, done.stdout)

    def test_valid_skill_passes_silently(self):
        self.put("demo", skill_md())
        done = self.check()
        self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_plugins_own_skills_pass(self):
        done = self.check(ROOT)
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_reviewing_skill_without_review_rule_fails(self):
        body = "# Demo\n\nStart the `agentic:correction-checker` agent.\n"
        self.put("demo", skill_md(body=body))
        self.assertFails("demo/SKILL.md: review rule missing")

    def test_reviewing_skill_with_review_rule_passes(self):
        rule = REVIEW_RULE.replace(" walk-through ends,", "\nwalk-through ends,")
        self.assertNotEqual(rule, REVIEW_RULE)
        body = f"# Demo\n\nStart the `agentic:correction-checker` agent.\n\n{STEPS}\n\n{rule}\n"
        self.put("demo", skill_md(body=body))
        done = self.check()
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_reworded_review_rule_fails(self):
        rule = REVIEW_RULE.replace("run the sequence once", "run the sequence each time")
        self.assertNotEqual(rule, REVIEW_RULE)
        body = f"# Demo\n\nStart the `agentic:correction-checker` agent.\n\n{STEPS}\n\n{rule}\n"
        self.put("demo", skill_md(body=body))
        self.assertFails("review rule missing")

    def test_build_checker_needs_no_review_rule(self):
        body = "# Demo\n\nStart the `agentic:build-correction-checker` agent.\n"
        self.put("demo", skill_md(body=body))
        self.assertEqual(self.check().returncode, 0)

    def test_skill_that_runs_no_review_needs_no_review_rule(self):
        self.put("demo", skill_md())
        self.assertEqual(self.check().returncode, 0)

    # Reviews find the document's repository (ADR 0032)

    def reviewing(self, document_line, extra=""):
        return (f"# Demo\n\nStart the `agentic:correction-checker` agent.\n\n{REVIEW_RULE}\n\n{STEPS}\n\n"
                f"```\n{document_line}\n```\n{extra}")

    def test_reviewing_skill_without_path_rule_fails(self):
        self.put("demo", skill_md(body=self.reviewing("Document: <the demo's full path>")))
        self.assertFails("demo/SKILL.md: path rule missing")

    def test_reviewing_skill_with_path_rule_passes(self):
        rule = PATH_RULE.replace(" the one ", "\nthe one ")
        self.assertNotEqual(rule, PATH_RULE)
        extra = f"{rule}\n\n{SHOW_RULE}\n"
        self.put("demo", skill_md(body=self.reviewing("Document: <the demo's full path>", extra)))
        done = self.check()
        self.assertEqual(done.returncode, 0, done.stdout)

    # Every document is shown the same way (ADR 0025)

    def test_skill_reviewing_a_document_without_the_show_rule_fails(self):
        body = self.reviewing("Document: <the demo's full path>", PATH_RULE)
        self.put("demo", skill_md(body=body))
        self.assertFails("demo/SKILL.md: show rule missing")

    def test_show_rule_wrapped_across_lines_passes(self):
        rule = SHOW_RULE.replace(" a fresh copy ", "\na fresh copy ")
        self.assertNotEqual(rule, SHOW_RULE)
        body = self.reviewing("Document: <the demo's full path>", f"{PATH_RULE}\n\n{rule}\n")
        self.put("demo", skill_md(body=body))
        done = self.check()
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_reworded_show_rule_fails(self):
        rule = SHOW_RULE.replace("never send them to a code-hosting site", "send them to GitHub")
        self.assertNotEqual(rule, SHOW_RULE)
        body = self.reviewing("Document: <the demo's full path>", f"{PATH_RULE}\n\n{rule}\n")
        self.put("demo", skill_md(body=body))
        self.assertFails("show rule missing")

    def test_the_first_wording_of_the_show_rule_fails(self):
        old = ("Show the person the document: if the app you run in can show them a file in a viewer, "
               "use it, and show a fresh copy after each change if what it shows is a copy; always "
               "name the document's full path; never send them to a website to read it.")
        body = self.reviewing("Document: <the demo's full path>", f"{PATH_RULE}\n\n{old}\n")
        self.put("demo", skill_md(body=body))
        self.assertFails("show rule missing")

    def test_a_draft_never_saved_needs_no_show_rule(self):
        self.put("demo", skill_md(body=self.reviewing("Document: feedback draft")))
        done = self.check()
        self.assertNotIn("show rule missing", done.stdout)

    def test_every_document_skill_holds_the_show_rule(self):
        holding = set()
        skills = os.path.join(ROOT, "skills")
        for name in os.listdir(skills):
            with open(os.path.join(skills, name, "SKILL.md"), encoding="utf-8") as f:
                if holds(f.read(), SHOW_RULE):
                    holding.add(name)
        self.assertEqual(holding, {"brief", "spec", "adr", "plan", "spike", "practices"})

    def test_a_draft_never_saved_needs_no_path_rule(self):
        self.put("demo", skill_md(body=self.reviewing("Document: feedback draft")))
        self.assertEqual(self.check().returncode, 0)

    def test_agent_given_a_repository_without_the_agent_rule_fails(self):
        self.put_agent("demo-reviewer", "---\nname: demo-reviewer\n---\n\nRead `Document: <path>` and `Repository: <folder>`.\n")
        self.assertFails("agents/demo-reviewer.md: repository rule missing")

    def test_a_document_reviewer_that_loses_the_agent_rule_fails(self):
        self.put_agent("plan-reviewer", "---\nname: plan-reviewer\n---\n\nYou review one plan.\n")
        self.assertFails("agents/plan-reviewer.md: repository rule missing")

    def test_agent_with_the_agent_rule_passes(self):
        rule = AGENT_RULE.replace(" It may ", "\nIt may ")
        self.put_agent("demo-reviewer", f"---\nname: demo-reviewer\n---\n\n{rule}\n")
        done = self.check()
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_every_agent_started_with_a_document_path_holds_the_agent_rule(self):
        agents = os.path.join(ROOT, "agents")
        holding = set()
        for name in os.listdir(agents):
            with open(os.path.join(agents, name), encoding="utf-8") as f:
                if AGENT_RULE in " ".join(f.read().split()):
                    holding.add(name[:-3])
        self.assertEqual(holding, {"spec-reviewer", "brief-reviewer", "adr-reviewer", "plan-reviewer",
                                   "spike-reviewer", "practices-reviewer", "language-checker",
                                   "correction-checker", "auditor", "audit-checker", "brief-checker"})

    def test_document_skill_without_type_rule_fails(self):
        self.put("spec", skill_md(name="spec"))
        self.assertFails("spec/SKILL.md: type rule missing")

    def test_document_skill_with_type_rule_passes(self):
        body = f"# Spec\n\n{TYPE_RULE}\n\n{PROPOSED_RULE}\n\n{ASK_RULE}\n\n{SIGNOFF_RULE}\n\n{DATE_RULE}\n"
        self.put("spec", skill_md(name="spec", body=body))
        done = self.check()
        self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_reworded_type_rule_fails(self):
        rule = TYPE_RULE.replace("never", "seldom")
        self.assertNotEqual(rule, TYPE_RULE)
        self.put("plan", skill_md(name="plan", body=f"# Plan\n\n{rule}\n"))
        self.assertFails("plan/SKILL.md: type rule missing")

    def test_other_skills_need_no_type_rule(self):
        self.put("feedback", skill_md(name="feedback"))
        self.put("audit", skill_md(name="audit", body=f"# Audit\n\n{REPORT_RULE}\n"))
        self.put("build", skill_md(name="build", body=f"# Build\n\n{BUILD_ASK_RULE}\n\n{BUILD_PATH_RULE}\n\n{REPORT_RULE}\n"))
        self.put("practices", skill_md(name="practices", body=f"# Practices\n\n{ASK_RULE}\n"))
        done = self.check()
        self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_the_document_skills_are_the_five_that_write_lifecycle_documents(self):
        self.assertEqual(sorted(DOCUMENT_SKILLS), ["adr", "brief", "plan", "spec", "spike"])

    # Shared review steps, proposed answers and sign-off

    def test_reviewing_skill_missing_a_shared_step_fails(self):
        steps = "\n\n".join(CORRECT_RULES[:3] + CORRECT_RULES[4:])
        body = f"# Demo\n\nStart the `agentic:correction-checker` agent.\n\n{REVIEW_RULE}\n\n{steps}\n"
        self.put("demo", skill_md(body=body))
        self.assertFails("demo/SKILL.md: review step rule 4 missing")

    def test_every_reviewing_skill_holds_every_shared_step(self):
        skills = os.path.join(ROOT, "skills")
        holding = set()
        for name in os.listdir(skills):
            path = os.path.join(skills, name, "SKILL.md")
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as f:
                    text = f.read()
                if all(holds(text, rule) for rule in CORRECT_RULES):
                    holding.add(name)
        self.assertEqual(holding, {"brief", "spec", "adr", "plan", "spike", "practices", "feedback"})

    def test_document_skill_without_proposed_rule_fails(self):
        self.put("brief", skill_md(name="brief", body=f"# Brief\n\n{TYPE_RULE}\n"))
        self.assertFails("brief/SKILL.md: proposed rule missing")

    def test_proposed_rule_gives_the_layout_the_hook_checks(self):
        for part in ("`### 1.", "`> **Proposed:**`", "`> **Why:**`", "two questions"):
            self.assertIn(part, PROPOSED_RULE)

    def test_asking_skill_without_ask_rule_fails(self):
        self.put("practices", skill_md(name="practices"))
        self.assertFails("practices/SKILL.md: ask rule missing")
        self.put("brief", skill_md(name="brief", body=f"# Brief\n\n{TYPE_RULE}\n\n{PROPOSED_RULE}\n"))
        self.assertFails("brief/SKILL.md: ask rule missing")

    def test_reworded_ask_rule_fails(self):
        rule = ASK_RULE.replace("last", "first")
        self.assertNotEqual(rule, ASK_RULE)
        self.put("practices", skill_md(name="practices", body=f"# Practices\n\n{rule}\n"))
        self.assertFails("practices/SKILL.md: ask rule missing")

    def test_build_without_the_build_ask_rule_fails(self):
        self.put("build", skill_md(name="build"))
        self.assertFails("build/SKILL.md: build-anyway rule missing")

    def test_build_with_the_build_ask_rule_passes(self):
        self.put("build", skill_md(name="build", body=f"# Build\n\n{BUILD_ASK_RULE}\n\n{BUILD_PATH_RULE}\n\n{REPORT_RULE}\n"))
        done = self.check()
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_reworded_build_ask_rule_fails(self):
        rule = BUILD_ASK_RULE.replace("Stop and settle them first", "Stop")
        self.assertNotEqual(rule, BUILD_ASK_RULE)
        self.put("build", skill_md(name="build", body=f"# Build\n\n{rule}\n\n{BUILD_PATH_RULE}\n"))
        self.assertFails("build/SKILL.md: build-anyway rule missing")

    # The build's reviews find the plan's repository (ADR 0032)

    def test_build_without_the_build_path_rule_fails(self):
        self.put("build", skill_md(name="build", body=f"# Build\n\n{BUILD_ASK_RULE}\n"))
        self.assertFails("build/SKILL.md: build path rule missing")

    def test_build_path_rule_wrapped_across_lines_passes(self):
        rule = BUILD_PATH_RULE.replace(" the hook ", "\nthe hook ")
        self.assertNotEqual(rule, BUILD_PATH_RULE)
        self.put("build", skill_md(name="build", body=f"# Build\n\n{BUILD_ASK_RULE}\n\n{rule}\n\n{REPORT_RULE}\n"))
        done = self.check()
        self.assertEqual(done.returncode, 0, done.stdout)

    # Build and audit end with a report file (ADR 0033)

    def test_build_and_audit_without_the_report_rule_fail(self):
        self.put("build", skill_md(name="build", body=f"# Build\n\n{BUILD_ASK_RULE}\n\n{BUILD_PATH_RULE}\n"))
        self.put("audit", skill_md(name="audit"))
        done = self.check()
        self.assertIn("build/SKILL.md: report rule missing", done.stdout)
        self.assertIn("audit/SKILL.md: report rule missing", done.stdout)

    def test_reworded_report_rule_fails(self):
        rule = REPORT_RULE.replace("never paste", "avoid pasting")
        self.assertNotEqual(rule, REPORT_RULE)
        self.put("audit", skill_md(name="audit", body=f"# Audit\n\n{rule}\n"))
        self.assertFails("audit/SKILL.md: report rule missing")

    def test_other_skills_need_no_report_rule(self):
        self.put("feedback", skill_md(name="feedback"))
        done = self.check()
        self.assertNotIn("report rule", done.stdout)

    def test_the_asking_skills_are_the_document_skills_and_practices(self):
        self.assertEqual(sorted(ASK_SKILLS), ["adr", "brief", "plan", "practices", "spec", "spike"])

    def test_status_skill_without_signoff_rule_fails(self):
        self.put("adr", skill_md(name="adr", body=f"# ADR\n\n{TYPE_RULE}\n\n{PROPOSED_RULE}\n\n{ASK_RULE}\n"))
        self.assertFails("adr/SKILL.md: sign-off rule missing")

    def test_brief_has_no_status_so_needs_no_signoff_rule(self):
        self.put("brief", skill_md(name="brief", body=f"# Brief\n\n{TYPE_RULE}\n\n{PROPOSED_RULE}\n\n{ASK_RULE}\n"))
        done = self.check()
        self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_reworded_signoff_rule_fails(self):
        rule = SIGNOFF_RULE.replace("does not count", "counts")
        self.assertNotEqual(rule, SIGNOFF_RULE)
        self.put("plan", skill_md(name="plan", body=f"# Plan\n\n{TYPE_RULE}\n\n{PROPOSED_RULE}\n\n{ASK_RULE}\n\n{rule}\n"))
        self.assertFails("plan/SKILL.md: sign-off rule missing")

    def test_status_skill_without_date_rule_fails(self):
        body = f"# ADR\n\n{TYPE_RULE}\n\n{PROPOSED_RULE}\n\n{ASK_RULE}\n\n{SIGNOFF_RULE}\n"
        self.put("adr", skill_md(name="adr", body=body))
        self.assertFails("adr/SKILL.md: date rule missing")

    def test_reworded_date_rule_fails(self):
        rule = DATE_RULE.replace("never", "seldom")
        self.assertNotEqual(rule, DATE_RULE)
        body = f"# Spike\n\n{TYPE_RULE}\n\n{PROPOSED_RULE}\n\n{ASK_RULE}\n\n{SIGNOFF_RULE}\n\n{rule}\n"
        self.put("spike", skill_md(name="spike", body=body))
        self.assertFails("spike/SKILL.md: date rule missing")

    def test_brief_needs_no_date_rule(self):
        self.put("brief", skill_md(name="brief", body=f"# Brief\n\n{TYPE_RULE}\n\n{PROPOSED_RULE}\n\n{ASK_RULE}\n"))
        done = self.check()
        self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_the_status_skills_are_the_four_with_a_status(self):
        self.assertEqual(sorted(STATUS_SKILLS), ["adr", "plan", "spec", "spike"])

    # Every skill that offers diagrams offers them the same way

    def adr_body(self, rules):
        return "# ADR\n\n" + "\n\n".join([TYPE_RULE, PROPOSED_RULE, ASK_RULE, SIGNOFF_RULE, DATE_RULE, *rules]) + "\n"

    def test_diagram_skill_with_every_diagram_rule_passes(self):
        self.put("adr", skill_md(name="adr", body=self.adr_body(diagram_rules("ADR"))))
        done = self.check()
        self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_diagram_skill_missing_a_diagram_rule_fails(self):
        for missing in range(len(diagram_rules("ADR"))):
            rules = [rule for i, rule in enumerate(diagram_rules("ADR")) if i != missing]
            self.put("adr", skill_md(name="adr", body=self.adr_body(rules)))
            self.assertFails(f"adr/SKILL.md: diagram rule {missing + 1} missing")

    def test_diagram_rules_name_the_skills_own_document(self):
        self.put("adr", skill_md(name="adr", body=self.adr_body(diagram_rules("plan"))))
        self.assertFails("adr/SKILL.md: diagram rule")

    def test_the_question_is_asked_word_for_word(self):
        self.assertIn("\"Would you like to add any of these diagrams to the ADR, or propose another?\"",
                      " ".join(diagram_rules("ADR")))

    def test_skills_that_offer_no_diagrams_need_no_diagram_rules(self):
        self.put("brief", skill_md(name="brief", body=f"# Brief\n\n{TYPE_RULE}\n\n{PROPOSED_RULE}\n\n{ASK_RULE}\n"))
        done = self.check()
        self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_every_diagram_skill_names_a_document_skill(self):
        self.assertTrue(set(DIAGRAM_SKILLS) <= set(DOCUMENT_SKILLS))

    # Every reviewer reports in the same shape

    def reviewer(self, *rules):
        return "---\nname: x\n---\n\n" + "\n\n".join(rules) + "\n"

    def test_reviewer_missing_a_report_rule_fails(self):
        self.put_agent("feedback-reviewer", self.reviewer(*REPORT_RULES[:2]))
        self.assertFails("agents/feedback-reviewer.md: report rule 3 missing")

    def test_reviewer_of_a_document_with_questions_needs_the_questions_rule(self):
        self.put_agent("brief-reviewer", self.reviewer(AGENT_RULE, *REPORT_RULES))
        self.assertFails("agents/brief-reviewer.md: questions rule missing")

    def test_reviewer_with_every_rule_passes(self):
        self.put_agent("brief-reviewer", self.reviewer(AGENT_RULE, *REPORT_RULES, QUESTIONS_RULE))
        done = self.check()
        self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_reviewers_without_open_questions_need_no_questions_rule(self):
        self.put_agent("practices-reviewer", self.reviewer(AGENT_RULE, *REPORT_RULES))
        self.put_agent("feedback-reviewer", self.reviewer(*REPORT_RULES))
        done = self.check()
        self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_no_skills_folder_passes(self):
        self.assertEqual(self.check().returncode, 0)

    def test_missing_frontmatter_fails(self):
        self.put("demo", "# Demo\n")
        self.assertFails("demo/SKILL.md: no frontmatter")

    def test_missing_name_fails(self):
        self.put("demo", f"---\ndescription: {DESCRIPTION}\n---\n\n# Demo\n")
        self.assertFails("name is missing")

    def test_name_must_match_folder(self):
        self.put("demo", skill_md(name="other"))
        self.assertFails("does not match its folder")

    def test_name_format(self):
        for bad in ["Demo", "de--mo", "-demo", "demo-", "de_mo"]:
            with self.subTest(bad=bad):
                self.put(bad, skill_md(name=bad))
                self.assertFails("lowercase letters, digits and single hyphens")

    def test_name_at_most_64_characters(self):
        self.put("a" * 65, skill_md(name="a" * 65))
        self.assertFails("over 64 characters")

    def test_name_may_be_64_characters(self):
        self.put("a" * 64, skill_md(name="a" * 64))
        self.assertEqual(self.check().returncode, 0)

    def test_name_has_no_reserved_word(self):
        for bad in ["claude-helper", "anthropic-tools"]:
            with self.subTest(bad=bad):
                self.put(bad, skill_md(name=bad))
                self.assertFails("reserved word")

    def test_missing_description_fails(self):
        self.put("demo", "---\nname: demo\n---\n\n# Demo\n")
        self.assertFails("description is missing")

    def test_description_at_most_1024_characters(self):
        self.put("demo", skill_md(description="a" * 1025))
        self.assertFails("over 1,024 characters")

    def test_description_may_be_1024_characters(self):
        self.put("demo", skill_md(description="a" * 1024))
        self.assertEqual(self.check().returncode, 0)

    def test_description_has_no_angle_brackets(self):
        self.put("demo", skill_md(description="Use for <thing> work."))
        self.assertFails("angle brackets")

    def test_quoted_description_is_measured_without_quotes(self):
        self.put("demo", skill_md(description='"' + "a" * 1024 + '"'))
        self.assertEqual(self.check().returncode, 0)

    # skill_md puts a blank line between the frontmatter and the body, which counts as a line.
    def test_body_under_500_lines(self):
        self.put("demo", skill_md(body="x\n" * 499))
        self.assertFails("500 lines")

    def test_body_of_499_lines_passes(self):
        self.put("demo", skill_md(body="x\n" * 498))
        self.assertEqual(self.check().returncode, 0)

    def test_body_about_5000_tokens(self):
        self.put("demo", skill_md(body=("word " * 20 + "\n") * 210))
        self.assertFails("5,000 tokens")

    def test_reports_every_failing_skill(self):
        self.put("one", skill_md(name="One"))
        self.put("two", "# Two\n")
        out = self.check().stdout
        self.assertIn("one/SKILL.md", out)
        self.assertIn("two/SKILL.md", out)

    def put_rubric(self, folder, text):
        path = os.path.join(self.tmp.name, "skills", folder, "references", "rubric.md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)

    def test_rubric_counting_words_per_sentence_fails(self):
        self.put("demo", skill_md())
        self.put_rubric("demo", "11. **Readable.** Sentences are under 25 words.\n")
        self.assertFails("demo/references/rubric.md: count rule")

    def test_rubric_counting_sentences_fails(self):
        self.put("demo", skill_md())
        self.put_rubric("demo", "4. **Question.** Names the choice in at most three sentences.\n")
        self.assertFails("count rule")

    def test_rubric_counting_sentences_per_paragraph_fails(self):
        self.put("demo", skill_md())
        self.put_rubric("demo", "11. Paragraphs at most 3 sentences.\n")
        self.assertFails("count rule")

    def test_rubric_count_wrapped_across_lines_fails(self):
        self.put("demo", skill_md())
        self.put_rubric("demo", "5. The reason follows in up to\n   two sentences.\n")
        self.assertFails("count rule")

    def test_rubric_word_budget_and_shape_rules_pass(self):
        self.put("demo", skill_md())
        self.put_rubric("demo", "The plain part, at most 500 words, is checked by a script.\n"
                                "2. **One story.** Story is one sentence.\n"
                                "3. Each requirement has exactly one rule sentence.\n")
        done = self.check()
        self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_other_wordings_of_a_count_fail(self):
        for wording in ("Each sentence is under 25 words.", "Sentences under twenty-five words.",
                        "No sentence over 25 words.", "At most 25 words per sentence.",
                        "Sentences shorter than 25 words.", "In one to three sentences.",
                        "In 3 sentences or fewer.", "In two or three sentences."):
            with self.subTest(wording=wording):
                self.put("demo", skill_md())
                self.put_rubric("demo", wording + "\n")
                self.assertFails("count rule")

    def test_reviewer_agent_counting_sentences_fails(self):
        self.put_agent("demo-reviewer", "Fail any sentence over 25 words.\n")
        self.assertFails("agents/demo-reviewer.md: count rule")

    def test_skill_md_may_give_counts_as_guidance(self):
        self.put("demo", skill_md(body="# Demo\n\nAim for sentences under 25 words.\n"))
        self.assertEqual(self.check().returncode, 0)

    def test_help(self):
        done = subprocess.run([sys.executable, SCRIPT, "--help"], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0)
        self.assertIn("agentskills.io", done.stdout)


if __name__ == "__main__":
    unittest.main()
