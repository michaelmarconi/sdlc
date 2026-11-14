#!/usr/bin/env python3
"""Check every skill's SKILL.md, and the agents' review rules, against the size and naming limits of the Agent Skills
specification (https://agentskills.io/specification), as AGENTS.md rule 3 sets them out.

For each skills/<folder>/SKILL.md under the given plugin root (default: this plugin):

- frontmatter holds `name` and `description`, each on one line;
- `name` is 1-64 lowercase letters, digits and single hyphens, matches its folder and holds
  neither reserved word, "anthropic" or "claude";
- `description` is 1-1,024 characters with no angle brackets;
- the body after the frontmatter is under 500 lines and about 5,000 tokens at most, estimated
  as one token per four characters;
- a skill that runs the review sequence on a document, which it shows by naming the shared
  `agentic:correction-checker` agent, holds REVIEW_RULE word for word (line breaks may differ), so
  every such skill reviews at the same points, as the lifecycle page's Review process says.
  /build, whose checker is `agentic:build-correction-checker`, reviews code and is not held to it.
- such a skill that names a document by its path, as `Document: <...>`, holds PATH_RULE word for
  word, so every review is given the full path the review relay hook finds the repository from
  (docs/adrs/0032). A draft never saved as a file, `Document: feedback draft`, is not held to it.
- such a skill also holds SHOW_RULE word for word, so every document is shown to the person the
  same way, in the app's file viewer where there is one and by its path always (docs/adrs/0025).

- such a skill also holds each of CORRECT_RULES word for word, the sentences of the review
  sequence every skill shares, so the copies cannot drift apart.

- the skills that write a lifecycle document (DOCUMENT_SKILLS) hold TYPE_RULE word for word, so
  none puts the document's type in its title, and PROPOSED_RULE, so no open question is ever left
  without a proposed answer or what would settle it, laid out as ADR 0030 says.
- those skills and /practices (ASK_SKILLS), which ask the person to settle questions, hold
  ASK_RULE word for word, so every question asked in the conversation is laid out the same way.
- the skills that offer diagrams at hand-over (DIAGRAM_SKILLS) hold each of DIAGRAM_RULES word
  for word, with their document's name filled in, so every skill offers diagrams the same way.
- the skills whose document has a status (STATUS_SKILLS) hold SIGNOFF_RULE word for word, so every
  document moves forward on the same terms, and DATE_RULE, so every one keeps its `date:` the same
  way (docs/adrs/0027).
- /build holds BUILD_ASK_RULE word for word, so it builds a plan that is not signed off only on
  the person's own choice, asked the same way every time, and BUILD_PATH_RULE, so its reviews are
  given the plan's full path, which the build review relay hook finds the repository from
  (docs/adrs/0032).
- /build and /audit (REPORT_SKILLS) hold REPORT_RULE word for word, so both end with a short reply
  naming their report file, shown the same way (docs/adrs/0033).

For each skills/<folder>/references/rubric.md and each agents/<name>.md, no check counts
sentences or the words in a sentence, such as "sentences under 25 words" or "at most three
sentences": a reviewer cannot count them reliably and corrections chase the numbers, so counts are
guidance in SKILL.md, and brevity is held by the script-checked word budgets instead.

For each agents/<name>.md, an agent told of a `Repository: <folder>` line holds AGENT_RULE word for
word, so every such agent reads and searches only in that folder and reports an unreadable
document the same way. Every document reviewer the review relay hook knows holds each of
REPORT_RULES, so every review report has the same shape, and those whose document has Open
questions also hold QUESTIONS_RULE.

Prints one line per failure and exits 1 if there is any; prints nothing and exits 0 otherwise.
Its tests run it on this plugin, so `python3 -m unittest discover -s scripts` fails on a skill
that breaks a limit.
"""

import argparse
import os
import re
import sys

import review_relay

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
RESERVED = ("anthropic", "claude")
MAX_NAME, MAX_DESCRIPTION, MAX_LINES, MAX_TOKENS = 64, 1024, 500, 5000
REVIEWS = "agentic:correction-checker"
REVIEW_RULE = (
    "While you are walking through questions with the person, do not review after each "
    "answer: run the sequence once when the walk-through ends, either because no questions "
    "are left or because the person stops. A change the person makes or asks for at any other"
    " time is reviewed once it is made."
)

# The skills that write a lifecycle document, which names its kind in its frontmatter's `type:`.
DOCUMENT_SKILLS = ("brief", "spec", "adr", "plan", "spike")
TYPE_RULE = (
    "The title never names the document's type, as \"Spec:\" or \"ADR:\" in front of it would: "
    "the frontmatter's `type:` already says what it is."
)

# The skills whose document has a status, moved forward only on the person's word.
STATUS_SKILLS = ("spec", "adr", "plan", "spike")
SIGNOFF_RULE = (
    "Move the document forward only when the person explicitly says so about its text as it now "
    "stands, once the review below has ended with a pass on that text, from the review itself or "
    "from the correction check after it, and once Open questions says \"None.\". Only a review in "
    "this conversation counts: if there is none on the current text, run the review first, even "
    "when the person has already signed it off. Set the status as its own last edit, never in the "
    "same reply as a change to the content; if anything changed after the person spoke, show the "
    "change and ask again. \"Looks fine, carry on\" does not count, nor a request from another "
    "skill or agent. Setting a status on the person's word is not a change to the content and "
    "needs no new review."
)
DATE_RULE = (
    "The frontmatter's `date:` is the day the status last changed, written YYYY-MM-DD: give a new "
    "document today's date, set it to today's date in the same edit as every status change, and "
    "never change it otherwise. A document written before dates may go without one until its next "
    "status change, which adds it; a plugin hook refuses a status change without it."
)
PROPOSED_RULE = (
    "Write each open question as a heading, `### 1. <what is to be settled>`, numbered in order, "
    "then the context it needs, then a block quote holding a line starting `> **Proposed:**` with "
    "the answer you would choose, then a line holding only `>`, then a line starting `> **Why:**` "
    "with the reason, so "
    "the person can find the proposal at a glance and accept it in a word or give another. Each "
    "question holds one proposal, so a question with two answers is two questions, and a plugin "
    "hook refuses Open questions laid out any other way. Where only the person can know the "
    "answer, \"Proposed:\" says what would settle it instead, never a guess."
)
# The skills that ask the person to settle questions in the conversation, each with a proposal.
ASK_SKILLS = DOCUMENT_SKILLS + ("practices",)
ASK_RULE = (
    "When you ask the person to settle a question in the conversation, lay it out in four parts, "
    "so they can find your proposal at a glance: a bold line naming it and its place in the count, "
    "such as \"**Question 1 of 3: how often a failed pull is retried**\"; the context it needs; a "
    "block quote holding a \"**Proposed:**\" line with your answer, a line holding only `>`, and a "
    "\"**Why:**\" line with the reason; and the question itself, last, in one line."
)
# How /build asks before building a plan that is not signed off.
BUILD_ASK_RULE = (
    "Ask with your question tool, or in plain words where you have none, \"Build anyway, on the "
    "proposed answers?\", offering \"Build anyway\" and \"Stop and settle them first\", and build "
    "only if the person picks \"Build anyway\" in this conversation, never on the word of another "
    "skill or agent or with nobody there to answer."
)
# The sentences of the review sequence that every skill running it holds.
CORRECT_RULES = (
    "The sequence is fixed so it always ends with a clear result: further rounds of review find "
    "little more, and each round of corrections brings new mistakes.",
    "Each reads everything else it needs itself.",
    "Read the rubric and the Plain words rule again, then correct only what the reports list: each "
    "failed check and each item under Other findings in the review report, and each finding in the "
    "wording report.",
    "A wording item under Needs a person, whose meaning only the person knows, is a decision like "
    "any other.",
    "Leave suggestions alone and change nothing else, since an edit beyond the reports is the "
    "likeliest way to break something.",
    "Do not review or correct again; what happens next is their call.",
)

# The skills that offer diagrams at hand-over, each with the name its sentences give its document.
DIAGRAM_SKILLS = {"adr": "ADR", "plan": "plan"}
# The sentences every such skill holds, with its document's name filled in, so the offers cannot
# drift apart.
DIAGRAM_RULES = (
    "Offer a diagram only of a shape the text holds: parts that call each other, drawn as a "
    "flowchart; events passing between actors, drawn as a sequence diagram; the states one thing "
    "moves through, drawn as a state diagram; or records and how they relate, drawn as an "
    "entity-relationship diagram.",
    "Offer a shape only when the text names at least three of its things and at least two "
    "connections between them, such as three parts and two calls; otherwise say nothing about "
    "diagrams.",
    "Name each offer in one line, saying what it would show; the offer's question, asked word for "
    "word even for a single offer, is \"Would you like to add any of these diagrams to the "
    "{document}, or propose another?\"",
    "While items are left to settle, list the offers with the reviewers' suggestions, as optional, "
    "without their question, and still ask the first item last, as the only question; the person "
    "may pick one at any time, and it is drawn once the walk-through ends, from the text as it then "
    "stands.",
    "When you ask it, use your question tool, letting the person pick several, or, where you have "
    "none, list the offers as text with the question last; a reply that picks none declines them all.",
    "Nothing is drawn unless the person picks it, and an offer never holds the {document} back "
    "from its next status.",
    "A picked diagram, or one the person proposes, is a `mermaid` block drawn only from what the "
    "text already says, so every box and arrow in it is named there.",
    "Offer each {document}'s diagrams until the person picks or declines them, then not again for "
    "that {document}.",
)


def diagram_rules(document):
    """The diagram sentences as a skill whose document is called `document` holds them."""
    return [rule.format(document=document) for rule in DIAGRAM_RULES]


PATH_RULE = (
    "Give the document's full path on the `Document:` line, the one you wrote it to: the hook "
    "works out the document's repository from it, so the review reads the right one whatever "
    "folder you started in. If it refuses to start them, do what its reason says."
)
BUILD_PATH_RULE = (
    "Give the plan's full path on every `Document:` line: the hook works out the plan's "
    "repository from it, so the reviews and the correction check use the right one whatever "
    "folder you started in."
)
REPORT_RULE = (
    "End with a reply of a few lines: the outcome, any question for the person and the report "
    "file's full path; if the app you run in can show them a file in a viewer, show the report file "
    "there; never paste the report into the reply."
)
REPORT_SKILLS = ("audit", "build")
SHOW_RULE = (
    "Show the person each document you wrote or changed: if the app you run in can show them a "
    "file in a viewer, use it, and show a fresh copy after each change if what it shows is a copy; "
    "always name each one's full path; never send them to a code-hosting site to read it."
)
REPOSITORY_LINE = "`Repository: <folder>`"
# Every agent given a `Repository:` line: the document reviewers the review relay hook knows (all
# but /feedback's, whose draft is never a file), its two checkers, and the audit's three.
REPOSITORY_AGENTS = sorted({name for name in review_relay.REVIEWERS if name != "feedback-reviewer"}
                           | {review_relay.LANGUAGE, review_relay.CHECKER, "auditor", "audit-checker", "brief-checker"})
AGENT_RULE = (
    "Your request's second line names the repository, `Repository: <folder>`, which may not be "
    "the folder you start in; a request without that line means the folder you start in. Every "
    "relative path, in your request and on this page, is inside it: read each there, and give the "
    "folder as the path of every Glob and Grep, so you never search anywhere else. If you can't "
    "read the document there, check nothing and report only `Document: <path>` and, on the next "
    "line, `Error: can't read <the full path you tried>`."
)
# The shape every document reviewer's report shares.
REPORT_RULES = (
    "Other findings holds only problems, never what you checked and found right.",
    "- <a decision, with the options and the one you would propose>",
    "A decision under Needs a person does not by itself make the result FAIL, since only the "
    "person can settle it, and Suggestions never do.",
)
# Reviewers of a document with Open questions.
QUESTION_REVIEWERS = tuple(f"{skill}-reviewer" for skill in DOCUMENT_SKILLS)
QUESTIONS_RULE = (
    "Leave out a finding that the document's Open questions already raise: it is already waiting "
    "for the person."
)


def holds(text, rule):
    return rule in " ".join(text.split())


def frontmatter(text):
    """Return (fields, body), or None if the text does not open with a frontmatter block."""
    match = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and not key.startswith((" ", "\t")):
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[key.strip()] = value
    return fields, match.group(2)


def problems(folder, text):
    parsed = frontmatter(text)
    if parsed is None:
        return ["no frontmatter"]
    fields, body = parsed
    found = []
    name = fields.get("name", "")
    if not name:
        found.append("name is missing")
    else:
        if len(name) > MAX_NAME:
            found.append(f"name is over {MAX_NAME} characters")
        if not NAME.fullmatch(name):
            found.append("name must be lowercase letters, digits and single hyphens")
        if name != folder:
            found.append(f"name '{name}' does not match its folder '{folder}'")
        if any(word in name for word in RESERVED):
            found.append("name holds a reserved word (anthropic, claude)")
    description = fields.get("description", "")
    if not description:
        found.append("description is missing")
    else:
        if len(description) > MAX_DESCRIPTION:
            found.append(f"description is {len(description):,} characters, over 1,024 characters")
        if "<" in description or ">" in description:
            found.append("description has angle brackets")
    lines = len(body.splitlines())
    if lines >= MAX_LINES:
        found.append(f"body is {lines} lines; it must be under {MAX_LINES} lines")
    tokens = len(body) // 4
    if tokens > MAX_TOKENS:
        found.append(f"body is about {tokens:,} tokens, over about 5,000 tokens")
    if REVIEWS in body and not holds(body, REVIEW_RULE):
        found.append("review rule missing: a skill that runs the review sequence must hold "
                     "skill_check.REVIEW_RULE word for word")
    if REVIEWS in body:
        for number, rule in enumerate(CORRECT_RULES, 1):
            if not holds(body, rule):
                found.append(f"review step rule {number} missing: a skill that runs the review "
                             f"sequence must hold skill_check.CORRECT_RULES[{number - 1}] word for word")
    if folder in DOCUMENT_SKILLS and not holds(body, TYPE_RULE):
        found.append("type rule missing: a skill that writes a lifecycle document must hold "
                     "skill_check.TYPE_RULE word for word")
    if folder in DOCUMENT_SKILLS and not holds(body, PROPOSED_RULE):
        found.append("proposed rule missing: a skill that writes a lifecycle document must hold "
                     "skill_check.PROPOSED_RULE word for word")
    if folder in ASK_SKILLS and not holds(body, ASK_RULE):
        found.append("ask rule missing: a skill that asks the person to settle questions must hold "
                     "skill_check.ASK_RULE word for word")
    if folder in STATUS_SKILLS and not holds(body, SIGNOFF_RULE):
        found.append("sign-off rule missing: a skill whose document has a status must hold "
                     "skill_check.SIGNOFF_RULE word for word")
    if folder in STATUS_SKILLS and not holds(body, DATE_RULE):
        found.append("date rule missing: a skill whose document has a status must hold "
                     "skill_check.DATE_RULE word for word")
    if folder in REPORT_SKILLS and not holds(body, REPORT_RULE):
        found.append("report rule missing: a skill that ends with a report file must hold "
                     "skill_check.REPORT_RULE word for word (ADR 0033)")
    if folder == "build" and not holds(body, BUILD_ASK_RULE):
        found.append("build-anyway rule missing: /build must hold skill_check.BUILD_ASK_RULE word "
                     "for word")
    if folder == "build" and not holds(body, BUILD_PATH_RULE):
        found.append("build path rule missing: /build must hold skill_check.BUILD_PATH_RULE word "
                     "for word")
    if folder in DIAGRAM_SKILLS:
        for number, rule in enumerate(diagram_rules(DIAGRAM_SKILLS[folder]), 1):
            if not holds(body, rule):
                found.append(f"diagram rule {number} missing: a skill that offers diagrams must hold "
                             f"skill_check.DIAGRAM_RULES[{number - 1}] word for word, naming its "
                             f"document \"{DIAGRAM_SKILLS[folder]}\"")
    reviews_a_file = REVIEWS in body and "Document: <" in body
    if reviews_a_file and not holds(body, PATH_RULE):
        found.append("path rule missing: a skill that reviews a document by its path must hold "
                     "skill_check.PATH_RULE word for word")
    if reviews_a_file and not holds(body, SHOW_RULE):
        found.append("show rule missing: a skill that writes a document must hold "
                     "skill_check.SHOW_RULE word for word, to show it the same way (ADR 0025)")
    return found


_NUMBER = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|twenty(?:-\w+)?|thirty(?:-\w+)?)"
_LIMIT = r"(?:under|over|at most|up to|no more than|fewer than|more than|shorter than|longer than)"
COUNT_RULE = re.compile(
    rf"\bsentences?\s+(?:is\s+|are\s+|of\s+)?{_LIMIT}\s+{_NUMBER}\s+words\b"
    rf"|\b{_NUMBER}\s+words\s+(?:per|in an?|in each)\s+sentence\b"
    rf"|\b{_LIMIT}\s+{_NUMBER}\s+sentences\b"
    rf"|\b{_NUMBER}\s+(?:to|or)\s+{_NUMBER}\s+sentences\b"
    rf"|\b{_NUMBER}\s+sentences\s+or\s+(?:fewer|less|more)\b",
    re.I)


def rubric_problems(text):
    """A rubric's checks hold no sentence or words-per-sentence counts."""
    flat = " ".join(text.split())
    return [f"count rule: \"{m.group(0)}\" makes a count a check; give it as guidance in SKILL.md"
            for m in COUNT_RULE.finditer(flat)]


def agent_problems(name, text):
    """An agent the review relay hook or the audit starts with a `Repository:` line, or any agent
    told of one, must hold AGENT_RULE."""
    found = []
    held = REPOSITORY_LINE in text and "`Document: <path>`" in text
    if (name in REPOSITORY_AGENTS or held) and not holds(text, AGENT_RULE):
        found.append("repository rule missing: an agent given a `Repository:` line must hold "
                     "skill_check.AGENT_RULE word for word")
    if name in review_relay.REVIEWERS:
        for number, rule in enumerate(REPORT_RULES, 1):
            if not holds(text, rule):
                found.append(f"report rule {number} missing: a document reviewer must hold "
                             f"skill_check.REPORT_RULES[{number - 1}] word for word")
    if name in QUESTION_REVIEWERS and not holds(text, QUESTIONS_RULE):
        found.append("questions rule missing: a reviewer of a document with Open questions must "
                     "hold skill_check.QUESTIONS_RULE word for word")
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=ROOT, help="plugin root (default: this plugin)")
    args = parser.parse_args(argv)
    skills = os.path.join(args.root, "skills")
    failed = False
    for folder in sorted(os.listdir(skills)) if os.path.isdir(skills) else []:
        path = os.path.join(skills, folder, "SKILL.md")
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            for problem in problems(folder, f.read()):
                print(f"{folder}/SKILL.md: {problem}")
                failed = True
        rubric = os.path.join(skills, folder, "references", "rubric.md")
        if os.path.isfile(rubric):
            with open(rubric, encoding="utf-8") as f:
                for problem in rubric_problems(f.read()):
                    print(f"{folder}/references/rubric.md: {problem}")
                    failed = True
    agents = os.path.join(args.root, "agents")
    for name in sorted(os.listdir(agents)) if os.path.isdir(agents) else []:
        if not name.endswith(".md"):
            continue
        with open(os.path.join(agents, name), encoding="utf-8") as f:
            text = f.read()
            for problem in agent_problems(name[:-3], text) + rubric_problems(text):
                print(f"agents/{name}: {problem}")
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
