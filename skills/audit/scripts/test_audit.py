"""Tests for audit.py, run against lifecycle documents and git repositories made in temporary folders.

Every commit date is fixed through GIT_COMMITTER_DATE and every window is read against a fixed
--now, so no test depends on the clock (AGENTS.md rule 5).
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "audit.py")
sys.path.insert(0, HERE)
import audit  # noqa: E402
import status_check  # noqa: E402

GIT_ENV = dict(GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.com", GIT_COMMITTER_NAME="Test",
               GIT_COMMITTER_EMAIL="test@example.com", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
NOW = "2026-11-05T12:00:00+00:00"


def spec(status="👍 Accepted", requirements=("Import a statement",), open_questions="None.", extra="", old=False):
    body = "".join((f"### Requirement: {name}" if old else f"### {number}. {name}")
                   + "\n\nThe system SHALL do it.\n\n" for number, name in enumerate(requirements, 1))
    return (f"---\nstatus: {status}\ndate: 2026-11-01\n---\n\n# Statement import\n\n## Story\n\nS.\n\n## Requirements\n\n"
            f"{body}{extra}## Open questions\n\n- {open_questions}\n")


def adr(status="👍 Accepted", supersedes=None, superseded_by=None, open_questions="None.", extra=""):
    lines = [f"status: {status}", "date: 2026-11-01"]
    if supersedes:
        lines.append(f"supersedes: {supersedes}")
    if superseded_by:
        lines.append(f"superseded-by: {superseded_by}")
    return ("---\n" + "\n".join(lines) + "\n---\n\n# Keep amounts in cents\n\n## Question\n\nQ?\n\n## Decision\n\nChosen: cents.\n\n"
            f"## Background\n\nC.{extra}\n\n## How we'll check\n\nApplies to: money.\n\n1. A test.\n\n"
            f"## Open questions\n\n- {open_questions}\n\n## Technical detail\n\nNone.\n")


def plan(status="📝 Draft", specs=(("statement-import.spec.md", ("Import a statement",)),), adrs=(), open_questions="None."):
    spec_lines = "".join(f"- [Spec](../specs/{name})\n" + "".join(
        f"  - [{r}](../specs/{name}#{i}-{status_check.anchor_of(r)})\n" for i, r in enumerate(reqs, 1))
                         for name, reqs in specs) or "None.\n"
    adr_lines = ("| ADR | Decision |\n| --- | --- |\n" + "".join(
        f"| [{name[:4]}](../adrs/{name}) | Keep amounts in cents |\n" for name in adrs)) if adrs else "None.\n"
    return (f"---\nstatus: {status}\ndate: 2026-11-01\n---\n\n# Work\n\n## Specs\n\n{spec_lines}\n## ADRs\n\n{adr_lines}\n"
            f"## Decisions\n\nNone.\n\n## Plan\n\nDo it.\n\n## Open questions\n\n- {open_questions}\n")


def spike(status="📝 Draft", open_questions="None."):
    return (f"---\nstatus: {status}\ndate: 2026-11-01\n---\n\n# It can\n\n## Hypothesis\n\nIt can.\n\n## Open questions\n\n"
            f"- {open_questions}\n\n## Code\n\n## Runs\n")


class Project(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = os.path.join(self.tmp.name, "project")
        os.makedirs(self.project)

    def put(self, relative, text):
        path = pathlib.Path(self.project, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def git(self, *args, date="2026-11-01T12:00:00+00:00", cwd=None):
        env = {**os.environ, **GIT_ENV, "GIT_COMMITTER_DATE": date, "GIT_AUTHOR_DATE": date}
        return subprocess.run(["git", *args], cwd=cwd or self.project, env=env, check=True,
                              capture_output=True, text=True).stdout.strip()

    def init(self):
        self.git("init", "-q", "-b", "main")

    def commit(self, message="Change", date="2026-11-01T12:00:00+00:00"):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message, date=date)
        return self.git("rev-parse", "HEAD")

    def run_audit(self, *args):
        done = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True,
                              cwd=self.project, env={**os.environ, **GIT_ENV})
        return done

    def documents(self):
        done = self.run_audit("documents")
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def problems(self, check=None):
        found = self.documents()["problems"]
        return [p for p in found if check is None or p["check"] == check]

    def window(self, *words):
        return self.run_audit("window", *words, "--now", NOW)


class Documents(Project):
    def test_no_lifecycle_documents_says_so(self):
        out = self.documents()
        self.assertFalse(out["lifecycle"])
        self.assertEqual(out["accepted"], {"specs": [], "adrs": []})
        self.assertEqual(out["problems"], [])

    def test_accepted_specs_and_adrs_are_listed_and_others_are_not(self):
        self.put("docs/specs/statement-import.spec.md", spec())
        self.put("docs/specs/sub/refunds.spec.md", spec())
        self.put("docs/specs/exports.spec.md", spec(status="📝 Draft"))
        self.put("docs/adrs/0001-cents.md", adr())
        self.put("docs/adrs/0002-floats.md", adr(status="❌ Rejected"))
        self.put("docs/adrs/0003-old.md", adr(status="📝 Draft"))
        out = self.documents()
        self.assertTrue(out["lifecycle"])
        self.assertEqual(out["accepted"], {
            "specs": ["docs/specs/statement-import.spec.md", "docs/specs/sub/refunds.spec.md"],
            "adrs": ["docs/adrs/0001-cents.md"]})
        self.assertEqual(out["problems"], [])

    def test_a_brief_alone_is_a_lifecycle_with_nothing_accepted(self):
        self.put("docs/brief.md", "# Product\n\nWhat it is.\n")
        out = self.documents()
        self.assertTrue(out["lifecycle"])
        self.assertEqual(out["accepted"], {"specs": [], "adrs": []})

    def test_the_brief_is_named_when_there_is_one(self):
        self.assertIsNone(self.documents()["brief"])
        self.put("docs/brief.md", "# Product\n\nWhat it is.\n")
        self.assertEqual(self.documents()["brief"], "docs/brief.md")

    def test_the_brief_is_found_whatever_the_case_of_its_name(self):
        self.put("docs/Brief.md", "# Product\n\nWhat it is.\n")
        self.assertEqual(self.documents()["brief"], "docs/Brief.md")

    def test_a_status_without_its_emoji_or_unknown_is_a_problem(self):
        self.put("docs/specs/statement-import.spec.md", spec(status="Accepted"))
        self.put("docs/adrs/0001-cents.md", adr(status="Approved"))
        self.put("docs/plans/2026-11-01-work.md", plan(status="🟢 Built"))
        self.put("docs/spikes/2026-11-01-can-it.md", spike(status="Confirmed"))
        found = {p["document"]: p["detail"] for p in self.problems("status")}
        self.assertEqual(sorted(found), ["docs/adrs/0001-cents.md", "docs/plans/2026-11-01-work.md",
                                         "docs/specs/statement-import.spec.md", "docs/spikes/2026-11-01-can-it.md"])
        self.assertIn("`👍 Accepted`", found["docs/specs/statement-import.spec.md"])
        self.assertIn("`✅ Built`", found["docs/plans/2026-11-01-work.md"])

    def test_a_wrong_type_is_a_problem_but_a_missing_one_is_not(self):
        self.put("docs/brief.md", "---\ntype: Spec\n---\n\n# Product\n")
        self.put("docs/specs/statement-import.spec.md", spec().replace("status:", "type: ADR\nstatus:", 1))
        self.put("docs/adrs/0001-cents.md", adr())
        found = {p["document"]: p["detail"] for p in self.problems("type")}
        self.assertEqual(sorted(found), ["docs/brief.md", "docs/specs/statement-import.spec.md"])
        self.assertIn("`type: Spec`", found["docs/specs/statement-import.spec.md"])

    def test_a_missing_or_malformed_date_is_a_problem(self):
        self.put("docs/brief.md", "---\ntype: Brief\n---\n\n# Product\n")
        self.put("docs/specs/statement-import.spec.md", spec().replace("date: 2026-11-01\n", ""))
        self.put("docs/adrs/0001-cents.md", adr().replace("date: 2026-11-01", "date: <YYYY-MM-DD>"))
        self.put("docs/plans/2026-11-01-work.md", plan().replace("date: 2026-11-01", "date: 2026-02-30"))
        self.put("docs/spikes/2026-11-01-can-it.md", spike())
        found = {p["document"]: p["detail"] for p in self.problems("date")}
        self.assertEqual(sorted(found), ["docs/adrs/0001-cents.md", "docs/plans/2026-11-01-work.md",
                                         "docs/specs/statement-import.spec.md"])
        self.assertIn("has no `date:`", found["docs/specs/statement-import.spec.md"])
        self.assertIn("'<YYYY-MM-DD>'", found["docs/adrs/0001-cents.md"])

    def test_a_spec_in_the_old_layout_is_listed(self):
        self.put("docs/specs/statement-import.spec.md", spec(old=True))
        self.put("docs/specs/exports.spec.md", spec(status="📝 Draft", old=True))
        self.put("docs/specs/refunds.spec.md", spec())
        found = {p["document"]: p["detail"] for p in self.problems("layout")}
        self.assertEqual(sorted(found), ["docs/specs/exports.spec.md", "docs/specs/statement-import.spec.md"])
        self.assertIn("written for an earlier version of the agentic plugin; rework it with /spec",
                      found["docs/specs/statement-import.spec.md"])

    def test_a_ready_plan_on_an_old_layout_spec_says_so(self):
        self.put("docs/specs/statement-import.spec.md", spec(old=True))
        self.put("docs/plans/2026-11-01-good.md", plan(status="🟢 Ready to build"))
        found = {p["document"]: p["detail"] for p in self.problems("ready plan")}
        self.assertIn("written for an earlier version of the agentic plugin", found["docs/plans/2026-11-01-good.md"])

    def test_a_status_written_without_the_variation_selector_is_fine(self):
        self.put("docs/adrs/0001-cents.md", adr(status="↪ Superseded", superseded_by="0002"))
        self.put("docs/adrs/0002-new.md", adr(supersedes="0001"))
        self.assertEqual(self.problems(), [])

    def test_a_spec_with_a_status_specs_no_longer_have_is_a_problem(self):
        self.put("docs/specs/statement-import.spec.md", spec(status="🟢 Ready to build"))
        self.assertEqual(len(self.problems("status")), 1)

    def test_a_document_missing_its_status_is_a_problem_but_other_files_are_left_alone(self):
        self.put("docs/specs/statement-import.spec.md", "# Statement import\n")
        self.put("docs/adrs/0001-cents.md", "# Keep amounts in cents\n")
        self.put("docs/adrs/README.md", "# Our decisions\n")
        self.put("docs/plans/notes.md", "# Notes\n")
        found = sorted(p["document"] for p in self.problems("status"))
        self.assertEqual(found, ["docs/adrs/0001-cents.md", "docs/specs/statement-import.spec.md"])

    def test_open_questions_on_a_settled_document_are_a_problem(self):
        self.put("docs/specs/statement-import.spec.md", spec(open_questions="What about refunds?"))
        self.put("docs/specs/exports.spec.md", spec(status="📝 Draft", open_questions="Which format?"))
        self.put("docs/adrs/0001-cents.md", adr(open_questions="Which currency?"))
        self.put("docs/plans/2026-11-01-work.md", plan(status="🟢 Ready to build", open_questions="When?"))
        self.put("docs/spikes/2026-11-01-can-it.md", spike(status="🟢 Ready to run", open_questions="How?"))
        found = sorted(p["document"] for p in self.problems("open questions"))
        self.assertEqual(found, ["docs/adrs/0001-cents.md", "docs/plans/2026-11-01-work.md",
                                 "docs/specs/statement-import.spec.md", "docs/spikes/2026-11-01-can-it.md"])

    def test_open_questions_not_laid_out_are_listed(self):
        entry = ("### 1. Which format\n\nNobody has said.\n\n> **Proposed:** CSV.\n>\n"
                 "> **Why:** Every bank exports it.\n")
        self.put("docs/brief.md", "---\ntype: Brief\n---\n\n# Ledger\n\n## Open questions\n\n- Who pays?\n")
        self.put("docs/specs/statement-import.spec.md", spec(status="📝 Draft", open_questions="Which format?"))
        self.put("docs/specs/exports.spec.md", spec(status="📝 Draft").replace("- None.\n", entry))
        self.put("docs/adrs/0001-cents.md", adr(status="📝 Draft", open_questions="Which currency?"))
        self.put("docs/plans/2026-11-01-work.md", plan(open_questions="When?"))
        self.put("docs/spikes/2026-11-01-can-it.md", spike(open_questions="How?"))
        found = {p["document"]: p["detail"] for p in self.problems("question layout")}
        self.assertEqual(sorted(found), ["docs/adrs/0001-cents.md", "docs/brief.md", "docs/plans/2026-11-01-work.md",
                                         "docs/specs/statement-import.spec.md", "docs/spikes/2026-11-01-can-it.md"])
        self.assertIn("### 1.", found["docs/brief.md"])

    def test_proposed_and_why_run_together_are_listed(self):
        joined = ("### 1. Which format\n\nNobody has said.\n\n> **Proposed:** CSV.\n"
                  "> **Why:** Every bank exports it.\n")
        self.put("docs/specs/exports.spec.md", spec(status="📝 Draft").replace("- None.\n", joined))
        found = {p["document"]: p["detail"] for p in self.problems("question layout")}
        self.assertEqual(list(found), ["docs/specs/exports.spec.md"])
        self.assertIn("line holding only `>`", found["docs/specs/exports.spec.md"])

    def test_question_layout_is_not_listed_where_it_cannot_or_need_not_change(self):
        self.put("docs/adrs/0001-cents.md", adr(status="❌ Rejected", open_questions="Which currency?"))
        self.put("docs/specs/statement-import.spec.md", spec(open_questions="What about refunds?"))
        self.assertEqual(self.problems("question layout"), [])
        self.assertEqual(len(self.problems("open questions")), 1)

    def test_references_follow_the_references_rule(self):
        self.put("docs/brief.md", "# Product\n\nSee [import](specs/statement-import.spec.md).\n")
        self.put("docs/specs/statement-import.spec.md",
                 spec(extra="Amounts follow docs/adrs/0001-cents.md.\n\n"))
        self.put("docs/specs/exports.spec.md", spec(extra="Built by `2026-11-01-work.md`.\n\n"))
        self.put("docs/adrs/0001-cents.md", adr(extra=" Like ADR 0002, unlike [the old one](0002-floats.md)."))
        self.put("docs/adrs/0002-floats.md", adr(extra=" Unlike ADR 0001."))
        self.put("docs/plans/2026-11-01-work.md", plan(adrs=("0001-cents.md",)))
        self.put("docs/spikes/2026-11-01-can-it.md",
                 spike().replace("It can.\n\n## Open", "It can. For docs/specs/exports.spec.md, not "
                                 "docs/plans/2026-11-01-work.md.\n\n## Open"))
        found = sorted((p["document"], p["detail"]) for p in self.problems("references"))
        self.assertEqual([document for document, _ in found], [
            "docs/brief.md", "docs/specs/exports.spec.md",
            "docs/specs/statement-import.spec.md", "docs/spikes/2026-11-01-can-it.md"])
        self.assertIn("docs/plans/2026-11-01-work.md", dict(found)["docs/spikes/2026-11-01-can-it.md"])
        self.assertNotIn("exports.spec.md", dict(found)["docs/spikes/2026-11-01-can-it.md"])

    def test_an_adr_may_link_another_adr_but_no_other_document(self):
        self.put("docs/specs/exports.spec.md", spec())
        self.put("docs/adrs/0001-cents.md", adr())
        self.put("docs/adrs/0002-floats.md", adr(extra=" Builds on [ADR 0001](0001-cents.md)."))
        self.put("docs/adrs/0003-tax.md", adr(extra=" For [exports](../specs/exports.spec.md)."))
        found = sorted(p["document"] for p in self.problems("references"))
        self.assertEqual(found, ["docs/adrs/0003-tax.md"])

    def test_a_reference_in_frontmatter_comments_or_supersede_fields_is_fine(self):
        self.put("docs/adrs/0001-cents.md", adr(status="↪️ Superseded", superseded_by="0002"))
        self.put("docs/adrs/0002-new.md", adr(supersedes="0001"))
        self.assertEqual(self.problems("references"), [])

    def test_supersede_fields_must_agree_both_ways(self):
        self.put("docs/adrs/0001-a.md", adr(status="↪️ Superseded", superseded_by="0002"))
        self.put("docs/adrs/0002-b.md", adr())
        self.put("docs/adrs/0003-c.md", adr())
        self.put("docs/adrs/0004-d.md", adr(supersedes="0003"))
        self.put("docs/adrs/0005-e.md", adr(status="↪️ Superseded"))
        self.put("docs/adrs/0006-f.md", adr(supersedes="0009"))
        found = sorted(p["document"] for p in self.problems("supersede"))
        self.assertEqual(found, ["docs/adrs/0001-a.md", "docs/adrs/0004-d.md", "docs/adrs/0005-e.md",
                                 "docs/adrs/0006-f.md"])

    def test_a_draft_adr_naming_the_one_it_will_supersede_is_fine(self):
        self.put("docs/adrs/0001-a.md", adr())
        self.put("docs/adrs/0002-b.md", adr(status="📝 Draft", supersedes="0001"))
        self.assertEqual(self.problems("supersede"), [])

    def test_a_ready_plan_must_still_name_accepted_documents_and_existing_requirements(self):
        self.put("docs/specs/statement-import.spec.md", spec(requirements=("Import a statement",)))
        self.put("docs/specs/exports.spec.md", spec(status="📝 Draft"))
        self.put("docs/plans/2026-11-01-good.md", plan(status="🟢 Ready to build"))
        self.put("docs/plans/2026-11-02-draft-spec.md",
                 plan(status="🟢 Ready to build", specs=(("exports.spec.md", ("Import a statement",)),)))
        self.put("docs/plans/2026-11-03-gone.md",
                 plan(status="🟢 Ready to build", specs=(("statement-import.spec.md", ("Refunds",)),)))
        self.put("docs/plans/2026-11-04-draft.md",
                 plan(status="📝 Draft", specs=(("exports.spec.md", ("Refunds",)),)))
        found = {p["document"]: p["detail"] for p in self.problems("ready plan")}
        self.assertEqual(sorted(found), ["docs/plans/2026-11-02-draft-spec.md", "docs/plans/2026-11-03-gone.md"])
        self.assertIn("Refunds", found["docs/plans/2026-11-03-gone.md"])

    def test_two_unbuilt_plans_naming_one_requirement_overlap(self):
        self.put("docs/specs/statement-import.spec.md", spec())
        self.put("docs/plans/2026-11-01-a.md", plan())
        self.put("docs/plans/2026-11-02-b.md", plan(status="🟢 Ready to build"))
        self.put("docs/plans/2026-11-03-c.md", plan(status="✅ Built"))
        found = self.problems("overlap")
        self.assertEqual(len(found), 1)
        self.assertIn("Import a statement", found[0]["detail"])
        self.assertIn("2026-11-02-b.md", found[0]["detail"] + found[0]["document"])
        self.assertIn("2026-11-01-a.md", found[0]["detail"] + found[0]["document"])

    def test_overlap_includes_plans_on_other_branches_git_knows(self):
        self.init()
        self.put("docs/specs/statement-import.spec.md", spec())
        self.commit("Start")
        self.git("checkout", "-q", "-b", "other")
        self.put("docs/plans/2026-11-02-elsewhere.md", plan())
        self.commit("Plan elsewhere")
        self.git("checkout", "-q", "main")
        self.put("docs/plans/2026-11-01-here.md", plan())
        found = self.problems("overlap")
        self.assertEqual(len(found), 1)
        self.assertIn("other", found[0]["detail"])
        self.assertIn("2026-11-02-elsewhere.md", found[0]["detail"])

    def test_the_same_plan_on_several_branches_does_not_overlap_itself(self):
        self.init()
        self.put("docs/specs/statement-import.spec.md", spec())
        self.put("docs/plans/2026-11-01-here.md", plan())
        self.commit("Start")
        self.git("branch", "copy")
        self.assertEqual(self.problems("overlap"), [])

    def test_a_plan_built_on_another_branch_is_not_an_overlap_there(self):
        self.init()
        self.put("docs/specs/statement-import.spec.md", spec())
        self.put("docs/plans/2026-11-01-a.md", plan(status="✅ Built"))
        self.commit("Start")
        self.git("checkout", "-q", "-b", "old")
        self.put("docs/plans/2026-11-01-a.md", plan())
        self.commit("Old copy")
        self.git("checkout", "-q", "main")
        self.put("docs/plans/2026-11-02-b.md", plan())
        self.assertEqual(self.problems("overlap"), [])

    def test_built_plans_and_spike_records_are_listed(self):
        self.put("docs/plans/2026-11-01-a.md", plan(status="✅ Built", specs=()))
        self.put("docs/plans/2026-11-02-b.md", plan(specs=()))
        self.put("docs/spikes/2026-10-01-done.md", spike(status="💡 Confirmed"))
        self.put("docs/spikes/2026-10-02-gave-up.md", spike(status="❔ Not settled"))
        self.put("docs/spikes/2026-10-05-wrong.md", spike(status="🚫 Refuted"))
        self.put("docs/spikes/2026-10-03-open.md", spike(status="📝 Draft"))
        self.put("docs/spikes/2026-10-04-ready.md", spike(status="🟢 Ready to run"))
        out = self.documents()
        self.assertEqual(out["built_plans"], ["docs/plans/2026-11-01-a.md"])
        self.assertEqual(out["finished_spikes"], ["docs/spikes/2026-10-01-done.md", "docs/spikes/2026-10-02-gave-up.md",
                                                  "docs/spikes/2026-10-05-wrong.md"])
        self.assertEqual(out["unfinished_spikes"], [
            {"document": "docs/spikes/2026-10-03-open.md", "status": "📝 Draft", "date": "2026-10-03"},
            {"document": "docs/spikes/2026-10-04-ready.md", "status": "🟢 Ready to run", "date": "2026-10-04"}])

    def test_a_status_without_its_emoji_still_counts_for_what_is_checked(self):
        self.put("docs/specs/statement-import.spec.md", spec(status="Accepted"))
        out = self.documents()
        self.assertEqual(out["accepted"]["specs"], ["docs/specs/statement-import.spec.md"])
        self.assertEqual([p["check"] for p in out["problems"]], ["status"])

    def test_an_accepted_adr_naming_its_replacement_is_a_problem(self):
        self.put("docs/adrs/0001-a.md", adr(superseded_by="0002"))
        self.put("docs/adrs/0002-b.md", adr(supersedes="0001"))
        found = self.problems("supersede")
        self.assertEqual([p["document"] for p in found], ["docs/adrs/0001-a.md"])
        self.assertIn("`↪️ Superseded`", found[0]["detail"])

    def test_documents_never_change_the_working_tree(self):
        self.init()
        self.put("docs/specs/statement-import.spec.md", spec(status="Accepted"))
        self.commit("Start")
        self.documents()
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_a_project_folder_can_be_named(self):
        self.put("docs/specs/statement-import.spec.md", spec())
        done = subprocess.run([sys.executable, SCRIPT, "documents", "--project", self.project],
                              capture_output=True, text=True, cwd=self.tmp.name)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["accepted"]["specs"], ["docs/specs/statement-import.spec.md"])

    def test_documents_names_the_project_s_full_path_so_paths_can_be_made_whole(self):
        self.put("docs/specs/statement-import.spec.md", spec())
        done = subprocess.run([sys.executable, SCRIPT, "documents", "--project", self.project],
                              capture_output=True, text=True, cwd=self.tmp.name)
        self.assertEqual(json.loads(done.stdout)["root"], os.path.realpath(self.project))


class Window(Project):
    def setUp(self):
        super().setUp()
        self.init()
        self.put("docs/specs/statement-import.spec.md", spec())
        self.put("docs/adrs/0001-cents.md", adr())
        self.put("src/old.py", "x = 1\n")
        self.start = self.commit("Start", date="2026-10-01T12:00:00+00:00")

    def ok(self, *words):
        done = self.window(*words)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def refused(self, *words):
        done = self.window(*words)
        self.assertEqual(done.returncode, 1)
        self.assertEqual(done.stdout, "")
        return done.stderr

    def test_last_n_days_lists_files_changed_by_commits_in_it(self):
        self.put("src/early.py", "1\n")
        self.commit("Early", date="2026-10-20T12:00:00+00:00")
        self.put("src/late.py", "2\n")
        self.commit("Late", date="2026-11-01T12:00:00+00:00")
        out = self.ok("last", "7", "days")
        self.assertEqual(len(out["commits"]), 1)
        self.assertEqual(out["changed"], [{"status": "A", "path": "src/late.py"}])

    def test_since_a_commit_leaves_that_commit_out(self):
        self.put("src/a.py", "1\n")
        first = self.commit("A", date="2026-11-01T12:00:00+00:00")
        self.put("src/b.py", "2\n")
        self.commit("B", date="2026-11-02T12:00:00+00:00")
        out = self.ok("since", first[:10])
        self.assertEqual([c["path"] for c in out["changed"]], ["src/b.py"])

    def test_changed_renamed_and_deleted_files_are_listed(self):
        self.put("src/old.py", "x = 2\n")
        self.commit("Change", date="2026-11-01T12:00:00+00:00")
        os.rename(os.path.join(self.project, "src/old.py"), os.path.join(self.project, "src/new.py"))
        self.put("src/gone.py", "g\n")
        self.commit("Rename", date="2026-11-02T12:00:00+00:00")
        os.remove(os.path.join(self.project, "src/gone.py"))
        self.commit("Delete", date="2026-11-03T12:00:00+00:00")
        out = self.ok("since", self.start)
        found = {c["path"]: c for c in out["changed"]}
        self.assertEqual(found["src/new.py"], {"status": "R", "path": "src/new.py", "from": "src/old.py"})
        self.assertNotIn("src/old.py", found)
        self.assertEqual(found["src/gone.py"]["status"], "D")

    def test_a_file_added_then_renamed_in_the_window_is_listed_as_added_under_its_new_name(self):
        self.put("src/first.py", "a = 1\nb = 2\nc = 3\n")
        self.commit("Add", date="2026-11-01T12:00:00+00:00")
        os.rename(os.path.join(self.project, "src/first.py"), os.path.join(self.project, "src/second.py"))
        self.commit("Rename", date="2026-11-02T12:00:00+00:00")
        out = self.ok("since", self.start)
        self.assertEqual(out["changed"], [{"status": "A", "path": "src/second.py"}])

    def test_accepted_documents_whose_text_changed_are_named(self):
        self.put("docs/specs/statement-import.spec.md", spec(extra="More.\n\n"))
        self.put("docs/specs/exports.spec.md", spec(status="📝 Draft"))
        self.commit("Edit spec", date="2026-11-01T12:00:00+00:00")
        out = self.ok("last", "7", "days")
        self.assertEqual(out["changed_accepted_documents"], ["docs/specs/statement-import.spec.md"])

    def test_a_change_to_the_brief_in_the_window_is_named(self):
        self.put("docs/brief.md", "# Product\n\nWhat it is now.\n")
        self.commit("Edit brief", date="2026-11-01T12:00:00+00:00")
        self.assertTrue(self.ok("last", "7", "days")["brief_changed"])

    def test_renaming_or_deleting_the_brief_in_the_window_is_a_change_to_it(self):
        self.put("docs/brief.md", "# Product\n\nWhat it is.\n")
        self.commit("Add brief", date="2026-10-01T12:00:00+00:00")
        os.rename(os.path.join(self.project, "docs/brief.md"), os.path.join(self.project, "docs/old-brief.md"))
        self.commit("Move brief", date="2026-11-01T12:00:00+00:00")
        self.assertTrue(self.ok("last", "7", "days")["brief_changed"])
        os.remove(os.path.join(self.project, "docs/old-brief.md"))
        self.put("docs/brief.md", "# Product\n")
        self.commit("Back", date="2026-11-02T12:00:00+00:00")
        os.remove(os.path.join(self.project, "docs/brief.md"))
        self.commit("Delete brief", date="2026-11-03T12:00:00+00:00")
        self.assertTrue(self.ok("since", "HEAD~1")["brief_changed"])

    def test_a_window_that_leaves_the_brief_alone_says_so(self):
        self.put("docs/brief.md", "# Product\n\nWhat it is.\n")
        self.commit("Add brief", date="2026-10-01T12:00:00+00:00")
        self.put("src/main.py", "m\n")
        self.commit("Code", date="2026-11-01T12:00:00+00:00")
        self.assertFalse(self.ok("last", "7", "days")["brief_changed"])

    def test_work_merged_in_the_window_counts_even_if_its_commits_are_older(self):
        self.git("checkout", "-q", "-b", "feature")
        self.put("src/feature.py", "f\n")
        self.commit("Feature", date="2026-10-02T12:00:00+00:00")
        self.git("checkout", "-q", "main")
        self.put("src/main.py", "m\n")
        self.commit("Main", date="2026-10-03T12:00:00+00:00")
        self.git("merge", "-q", "--no-ff", "-m", "Merge feature", "feature", date="2026-11-02T12:00:00+00:00")
        out = self.ok("last", "7", "days")
        self.assertEqual([c["path"] for c in out["changed"]], ["src/feature.py"])

    def test_the_window_s_commits_are_listed_and_nothing_is_written(self):
        self.put("src/late.py", "print('changed')\n")
        late = self.commit("Late", date="2026-11-01T12:00:00+00:00")
        out = self.ok("last", "7", "days")
        self.assertEqual(out["commits"], [{"commit": late[:12], "date": "2026-11-01", "subject": "Late"}])
        self.assertEqual(self.git("status", "--porcelain", "--ignored"), "")
        self.assertFalse(os.path.exists(os.path.join(self.project, ".git", "agentic-audit")))

    def test_changes_that_are_not_utf_8_text_are_still_listed(self):
        with open(os.path.join(self.project, "src", "latin.txt"), "wb") as f:
            f.write("caf\u00e9\n".encode("latin-1"))
        self.commit("Latin-1", date="2026-11-01T12:00:00+00:00")
        out = self.ok("last", "7", "days")
        self.assertEqual([c["path"] for c in out["changed"]], ["src/latin.txt"])

    def test_window_names_the_project_s_full_path(self):
        self.assertEqual(self.ok("last", "7", "days")["root"], os.path.realpath(self.project))

    def test_a_window_with_no_commits_is_not_refused(self):
        out = self.ok("last", "3", "days")
        self.assertEqual((out["commits"], out["changed"]), ([], []))

    def test_a_file_name_that_is_not_ascii_is_listed_as_it_is(self):
        self.put("docs/specs/caf\u00e9.spec.md", spec())
        self.commit("Add", date="2026-11-01T12:00:00+00:00")
        out = self.ok("last", "7", "days")
        self.assertEqual(out["changed_accepted_documents"], ["docs/specs/caf\u00e9.spec.md"])

    def test_unreadable_words_are_refused(self):
        self.assertIn("last N days", self.refused("yesterday"))
        self.assertIn("last N days", self.refused("last", "week"))

    def test_an_unknown_commit_is_refused(self):
        self.assertIn("no commit", self.refused("since", "deadbeef"))

    def test_a_commit_not_on_this_branch_is_refused(self):
        self.git("checkout", "-q", "-b", "side")
        self.put("src/side.py", "s\n")
        side = self.commit("Side", date="2026-11-01T12:00:00+00:00")
        self.git("checkout", "-q", "main")
        self.assertIn("not on the checked-out branch", self.refused("since", side))

    def test_a_window_older_than_a_shallow_clone_is_refused(self):
        for day in ("2026-10-28", "2026-10-30", "2026-11-02"):
            self.put(f"src/{day}.py", "d\n")
            self.commit(day, date=f"{day}T12:00:00+00:00")
        clone = os.path.join(self.tmp.name, "clone")
        self.git("clone", "-q", "--depth", "2", "file://" + self.project, clone, cwd=self.tmp.name)
        def in_clone(*words):
            return subprocess.run([sys.executable, SCRIPT, "window", *words, "--now", NOW],
                                  capture_output=True, text=True, cwd=clone, env={**os.environ})
        self.assertEqual(in_clone("last", "4", "days").returncode, 0)
        refused = in_clone("last", "30", "days")
        self.assertEqual(refused.returncode, 1)
        self.assertIn("history", refused.stderr)
        self.assertEqual(in_clone("since", self.start).returncode, 1)

    def test_a_window_past_any_of_a_shallow_clones_cut_points_is_refused(self):
        # Cloned two commits deep from a merge, the history is cut in two places: on main at an
        # old commit, and on the merged branch at a recent one, which leaves 2026-11-01 out.
        self.put("src/main.py", "m\n")
        self.commit("Main", date="2026-10-01T12:00:00+00:00")
        self.git("checkout", "-q", "-b", "side", self.start)
        for day in ("2026-11-01", "2026-11-03"):
            self.put(f"src/{day}.py", "s\n")
            self.commit(day, date=f"{day}T12:00:00+00:00")
        self.git("checkout", "-q", "main")
        self.git("merge", "-q", "--no-ff", "-m", "Merge side", "side", date="2026-11-04T12:00:00+00:00")
        clone = os.path.join(self.tmp.name, "clone")
        self.git("clone", "-q", "--depth", "2", "file://" + self.project, clone, cwd=self.tmp.name)
        refused = subprocess.run([sys.executable, SCRIPT, "window", "last", "7", "days", "--now", NOW],
                                 capture_output=True, text=True, cwd=clone, env={**os.environ})
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn("history", refused.stderr)

    def test_outside_a_git_repository_a_window_is_refused(self):
        plain_folder = os.path.join(self.tmp.name, "plain")
        os.makedirs(plain_folder)
        done = subprocess.run([sys.executable, SCRIPT, "window", "last", "7", "days", "--now", NOW],
                              capture_output=True, text=True, cwd=plain_folder,
                              env={**os.environ, "GIT_CEILING_DIRECTORIES": self.tmp.name})
        self.assertEqual(done.returncode, 1)
        self.assertIn("git repository", done.stderr)

    def test_every_command_has_help(self):
        for command in ("documents", "window"):
            done = self.run_audit(command, "--help")
            self.assertEqual(done.returncode, 0)
            self.assertIn("Exit codes", done.stdout)


class Report(Project):
    """`start` and `report`: the audit's report file, with its agents' reports copied in."""

    def setUp(self):
        super().setUp()
        self.data = os.path.join(self.tmp.name, "data")
        self.put("docs/adrs/0001-cents.md", adr())
        self.put("docs/specs/statement-import.spec.md", spec(status="📝 Draft", extra="See ../adrs/0001-cents.md.\n"))
        sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
        import audit_relay
        self.relay = audit_relay

    def keep(self, agent, document, kind, text):
        path = self.relay.record_path(self.data, "s1")
        record = self.relay.load(path)
        self.relay.keep(record, {"agent": agent, "document": document, "kind": kind}, text)
        self.relay.save(path, record)

    def report(self, own="", *extra):
        done = subprocess.run([sys.executable, SCRIPT, "report", "--data", self.data, "--session", "s1",
                               "--now", NOW, *extra], input=own, capture_output=True, text=True,
                              cwd=self.project, env={**os.environ, **GIT_ENV})
        return done

    def written(self, done):
        self.assertEqual(done.returncode, 0, done.stderr)
        line = done.stdout.splitlines()[0]
        self.assertTrue(line.startswith("Report written: "), done.stdout)
        with open(line[len("Report written: "):], encoding="utf-8") as f:
            return line[len("Report written: "):], f.read()

    def test_agents_reports_word_for_word_under_their_headings(self):
        adr_path = os.path.join(os.path.realpath(self.project), "docs/adrs/0001-cents.md")
        auditor = "Drift:\n1. \"amounts in cents\" vs `float(x)` at a.py:3\n"
        self.keep("audit-picker", "", "", "Picked: docs/adrs/0001-cents.md")
        self.keep("auditor", adr_path, "", auditor)
        self.keep("audit-checker", adr_path, "AUDIT REPORT", "1. Confirmed")
        self.keep("brief-checker", os.path.join(self.project, "docs/brief.md"), "", "Contradicts: none")
        self.keep("audit-checker", adr_path, "BRIEF REPORT", "Rejected")
        path, text = self.written(self.report("## Drift\n\n1. ADR 0001: correct the code.\n", "--scope", "all"))
        self.assertTrue(path.endswith("2026-11-05-audit-all.md"))
        drift = text[text.index("## Drift"):text.index("## Contradicts the brief")]
        self.assertIn("1. ADR 0001: correct the code.", drift)
        self.assertIn("### Auditor: docs/adrs/0001-cents.md\n\n" + auditor, drift)
        self.assertIn("### Checker: docs/adrs/0001-cents.md\n\n1. Confirmed", drift)
        brief = text[text.index("## Contradicts the brief"):text.index("## Problems with the documents")]
        self.assertIn("Contradicts: none", brief)
        self.assertIn("Rejected", brief)
        checked = text[text.index("## Documents checked"):text.index("## Documents not checked")]
        self.assertIn("Picked: docs/adrs/0001-cents.md", checked)

    def test_documents_problems_written_by_the_script(self):
        _, text = self.written(self.report("", "--scope", "all"))
        problems = text[text.index("## Problems with the documents"):text.index("## Not built yet")]
        self.assertIn("docs/specs/statement-import.spec.md: references:", problems)

    def test_claude_names_corrections_beside_the_problems(self):
        _, text = self.written(self.report("## Problems with the documents\n\nRemove the link.\n", "--scope", "all"))
        problems = text[text.index("## Problems with the documents"):text.index("## Not built yet")]
        self.assertIn("Remove the link.", problems)
        self.assertIn("references:", problems)

    def test_scope_names(self):
        path, _ = self.written(self.report("", "--scope", "last 7 days"))
        self.assertTrue(path.endswith("2026-11-05-audit-last-7-days.md"))
        path, _ = self.written(self.report("", "--scope", "docs/adrs/0001-cents.md"))
        self.assertTrue(path.endswith("2026-11-05-audit-0001-cents.md"))

    def test_report_clears_the_record(self):
        self.keep("auditor", "x", "", "old")
        self.written(self.report("", "--scope", "all"))
        _, text = self.written(self.report("", "--scope", "all"))
        self.assertNotIn("old", text)

    def test_start_clears_the_record(self):
        self.keep("auditor", "x", "", "left from an audit that stopped")
        done = self.run_audit("start", "--data", self.data, "--session", "s1")
        self.assertEqual(done.returncode, 0, done.stderr)
        _, text = self.written(self.report("", "--scope", "all"))
        self.assertNotIn("left from an audit", text)

    def test_nothing_written_in_the_project(self):
        self.init()
        self.commit()
        self.written(self.report("## Drift\n\nNone.\n", "--scope", "all"))
        self.assertEqual(self.git("status", "--porcelain"), "")


if __name__ == "__main__":
    unittest.main()
