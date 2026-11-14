# Agent instructions

This repo is a Claude Code plugin that encodes a software development lifecycle. Read
[docs/lifecycle.md](docs/lifecycle.md) for the lifecycle itself. Claude gets that page at the
start of every session in a repository that uses the lifecycle, so a change to it changes what
Claude is told and needs the same care as a change to a skill. This file holds the rules for
building the plugin. They apply to every change. Where a rule names a number, it is a hard limit;
everything else is judgement.

## Principles

1. **Independent in spirit.** The plugin is the unit of distribution, not the skill. A skill
   does one job and never invokes or assumes a prior run of another of the plugin's skills,
   though it may use Claude Code's own skills and agents, such as `/code-review`; it may use a document
   another skill produces when one is present, but must work when it is not. Skills may share
   what the plugin provides: its agents, hooks, scripts and `docs/lifecycle.md`.
2. **Small.** Every word earns its place. Write only what Claude would not do unaided, and say it
   once: no restating a rule in a summary, checklist or table.
3. **Standard format.** Each skill is a folder that follows the
   [Agent Skills specification](https://agentskills.io/specification):
   - `skills/<name>/SKILL.md` with YAML frontmatter holding `name` and `description`.
   - `name`: 1–64 characters, lowercase letters, digits and single hyphens; matches the folder.
   - `description`: at most 1,024 characters; says what the skill does and when to use it.
   - Body under 500 lines and about 5,000 tokens.
   - `scripts/skill_check.py` checks these limits on every skill, and its tests run it on this
     plugin, so the script tests below fail on a skill that breaks one.
   - Optional `scripts/`, `references/` and `assets/`. References sit one level deep, and
     `SKILL.md` says when to read each one.
4. **Reviewed.** No agent checks its own work. Every skill that writes a document takes
   it through the review sequence that [docs/lifecycle.md](docs/lifecycle.md#review-process)
   describes, and [ADR 0010](docs/adrs/0010-correction-check.md)
   explains: review once, correct once, then check only the corrections. To build it into a
   skill:
   - A rubric at `skills/<name>/references/rubric.md`: a short list of named checks, each pass
     or fail. The skill reads it while writing and again before correcting; the reviewer reads
     it while checking.
   - A reviewer agent at `agents/<name>-reviewer.md`, with read-only tools (a reviewer of code
     may also run the commands its definition names). It starts fresh,
     reads the rubric through `${CLAUDE_PLUGIN_ROOT}`, and reads only the files its own
     definition names. It reports pass or fail for each check, quoting the evidence for each
     failure, then Other findings, Needs a person and Suggestions. It holds `REPORT_RULES` from
     `scripts/skill_check.py` word for word, and `QUESTIONS_RULE` too when its document has Open
     questions; the script checks both.
   - The skill starts the reviewer and the shared language checker
     (`agents/language-checker.md`, [ADR 0013](docs/adrs/0013-language-checker.md))
     side by side, then the shared correction checker (`agents/correction-checker.md`), each
     with a request whose first line is `Document: <path>`, the document's full path. The review
     relay hook (`scripts/review_relay.py`, [ADR 0011](docs/adrs/0011-review-relay-hook.md))
     reads that line to save the document before the review and both reports after it, and
     attaches them to the checker's request, so the skill never copies them. It also finds the
     document's repository ([ADR 0032](docs/adrs/0032-hook-repository-folder.md)), names the
     document relative to it and adds a `Repository: <folder>` second line, so a review started
     from another folder still reads the right one. The skill holds `PATH_RULE`, and each agent
     `AGENT_RULE`, from `scripts/skill_check.py` word for word; the script checks both. Add the new
     reviewer and its skill's files to the hook's `REVIEWERS` table. A document that must not
     be written to the working tree, such as `/feedback`'s draft, uses `Document: feedback draft` and
     carries the draft between `=== DRAFT ===` and `=== END DRAFT ===` lines.
   - The correct step reads the rubric and the Plain words rule again, corrects only what the
     reports list, turns each
     decision for the person into an open question, leaves suggestions alone and changes
     nothing else. A failed correction check stops and shows the person; there is never a
     second review of the skill's own corrections. The sentences every skill shares for these
     steps are `CORRECT_RULES` in `scripts/skill_check.py`, held word for word.
   - When the sequence runs again is the same for every such skill: each holds `REVIEW_RULE`
     from `scripts/skill_check.py` word for word, and the script fails a skill that names
     `agentic:correction-checker` without it.
   - The hand-over shows the person the document in the app's file viewer where there is one,
     always names its path and never sends them to a code-hosting site
     ([ADR 0025](docs/adrs/0025-document-review-display.md)): the skill holds `SHOW_RULE` from
     `scripts/skill_check.py` word for word, and the script checks it. The hand-over also gives
     the reports, the number of items the person must settle, and the first of them; suggestions
     are listed apart as optional.
   - A document with a status has an Open questions section, last apart from a spike record's
     Experiment, Code and Runs and an ADR's Technical detail, their technical parts, which follow
     it so the document reads plain first. The skill writes there
     whatever only the person can settle, each question laid out with its proposed answer in a block
     quote, as [ADR 0030](docs/adrs/0030-open-questions-layout.md) says (`PROPOSED_RULE`; questions
     asked in the conversation follow `ASK_RULE`), and never moves the document forward while the section holds anything, nor
     without the person's sign-off on the reviewed text (`SIGNOFF_RULE`). The status hook (`scripts/status_check.py`) refuses such a move
     for specs, ADRs, plans and spike records; a new document type with a status adds its rule there.
5. **Evaluated.** Every skill ships with evals under the plugin's `evals/`, in the case-folder
   layout that skill-creator writes and `claude plugin eval` runs. Write the rubric first, then
   the evals: each rubric check is also an eval assertion, so one rubric both tests the skill and
   reviews its output. Case folder names start with the skill's name (`<name>-<what-it-checks>`)
   so cases stay unique across the library. At minimum:
   - One case per distinct behaviour the skill promises.
   - Trigger cases for the description: prompts that should and should not invoke it.
   - Each case must pass with the skill and fail, or score clearly worse, without it. A case
     that passes either way tests nothing. Show this once, when the case is written, with a run
     without `--ablation none`; routine runs leave the comparison off (see Workflow). Two kinds of case are the exception: cases that
     should not trigger the skill, which pass without it by design, and guard cases for a
     rubric check Claude already meets unaided, which catch a change that breaks it. Name the
     guard's reason in its case.yaml.
   - Prefer a regex or tool check to a judge. A judge grader checks one claim, and states any
     fact it needs, such as what an input file said, since it sees only what it is focused on;
     judges given several claims at once split their votes on the same output.
   - **Never rely on timing.** No test or eval may depend on when something happens: no
     sleeps, waits, retries or racing another process for the right order. A result that
     depends on timing passes or fails by luck, so it proves nothing. If the only way to test
     a behaviour is by timing, leave it untested and say so in the case or test file.
6. **Built with skill-creator.** Create, change and tune skills, and their descriptions, with
   Anthropic's `skill-creator` skill, following its draft, eval, review and iterate loop.
7. **Deterministic where it earns its place.** Use a script only when it must be exact every
   time, as with the status rules, or when evals show Claude getting the job wrong or wasting
   effort on it. Otherwise leave it to Claude and the reviewer, whose judgement copes with cases
   a script can't foresee. A script lives in the skill's `scripts/`, or the plugin's `scripts/`
   when a hook runs it. Scripts are
   self-contained: standard-library Python (3.7 or later) or POSIX shell, no install step, no
   network unless the task needs it, and runnable on macOS, Linux and in Claude Code on the web.
   - **Test-driven.** Write a failing test before each behaviour. Tests use the standard-library
     `unittest` module and live beside the script as `scripts/test_<script>.py`.
   - **Documented.** Each script has a module docstring saying what it does, and every command
     has `--help` text covering its arguments, output and exit codes. `SKILL.md` names each
     command Claude should run and when.
8. **Fix with evidence, not rules.** A bug report becomes a failing eval case first, then the
   smallest change that makes it pass. Skills carry no incident logs, rationalization tables or
   red-flag lists: lessons live in evals, where they are checked, not in prose, where they
   accumulate. Issues raised with `/feedback` follow the same path: turn the issue into a failing
   case (starting from its proposed eval, if it has one), fix it with skill-creator, put
   `Fixes #<number>` in the fix's commit message, so GitHub closes the issue when the commit
   reaches main, and bump the version as the Workflow section says. An improvement to the
   lifecycle itself, rather than to one skill, is agreed first as a change to
   `docs/lifecycle.md`, or as an ADR when it is a decision about how the plugin is built.
9. **Explain, don't shout.** Give the reason behind an instruction instead of stacking MUST and
   NEVER. Reserve those words for hard limits.
10. **Safe by default.** A skill never commits, pushes, publishes, deletes or sends anything
   outside the working tree unless the user asks for it in that session. Running `/build` is
   that request for its commits and the push of its own branch; nothing ever merges.
11. **Generic.** Skills assume no particular language, framework, repo layout or host, beyond
    the lifecycle's own folders under `docs/`. Paths a skill writes to are stated in the skill
    and kept to a minimum.
12. **Tested on named models.** Skills don't set a model or effort, so they run on whatever the
    person's session uses. Reviewer agents set `model:` to a model alias (such as `sonnet`), so
    the judgement that gates a document stays consistent. The README names the models the evals
    pass on; when a model changes or one is added, rerun the evals on it before claiming it.
13. **Plain words.** Everything written for people in this repository follows the
    [Plain words](docs/lifecycle.md#plain-words) rule, as if the plugin had written it: the README,
    the pages under `docs/`, commit messages, pull request descriptions and Claude's replies while
    working here. Files written for Claude, such as a `SKILL.md`, a rubric or an agent, may use
    the lifecycle's own terms, since Claude reads them with the lifecycle page in hand.
14. **Statuses by their exact value.** A document status is its emoji and its word: `📝 Draft`,
    `🟢 Ready to build`, `✅ Built`, `👍 Accepted`, `❌ Rejected`, `↪️ Superseded`, `🟢 Ready to run`,
    `💡 Confirmed`, `🚫 Refuted` and `❔ Not settled`. The
    status line holds that value bare. Everywhere else, name a status in backticks with its emoji,
    exactly as the status line has it, so a reader can find it and copy it; never put an emoji in
    running prose. `scripts/test_status_names.py` catches a backticked status that is wrong, and
    the words of `🟢 Ready to build` and `🟢 Ready to run` left unformatted; the other words are
    ordinary English too,
    so those are yours to catch.

## This repository's own documents

This repository keeps its own brief, `docs/brief.md`, and its own ADRs in `docs/adrs/`, in the
formats the plugin's skills write and under the rules in [docs/lifecycle.md](docs/lifecycle.md).
It does not install the plugin into itself: they are written by hand, in conversation with the
maintainer. It keeps no specs, since each skill is already described by its `SKILL.md`, its rubric
and its page under `docs/skills/`, and no plans, since work in flight is planned in Claude Code's
plan mode.

- A lasting technical decision about how the plugin is built becomes a new ADR, written as Draft.
  The lifecycle's own rules stay in `docs/lifecycle.md`: they are the product, not decisions
  about building it.
- Each brief or ADR goes through the review sequence in
  [docs/lifecycle.md](docs/lifecycle.md#review-process), run by hand. Start an agent that follows
  `agents/brief-reviewer.md` or `agents/adr-reviewer.md`, and beside it one that follows
  `agents/language-checker.md`, each reading `${CLAUDE_PLUGIN_ROOT}` as this repository's root,
  and keep an exact copy of the document as reviewed. Correct once, then start an agent that
  follows `agents/correction-checker.md`. Without the plugin installed, no hook attaches the
  checker's blocks, so write both reports and the copy into a file outside the
  repository in the blocks the checker's definition names, and point the checker to that file.
  Agents are not allowed to save their reports as files, so copy each report into its file by a script, from
  Claude Code's record of the agent's run, never by retyping it, for the reason
  [ADR 0011](docs/adrs/0011-review-relay-hook.md) gives.
- Only the maintainer accepts or rejects an ADR, after reading its reviewed text. Each acceptance
  is its own commit that changes only the status.

## Repository layout

```
.github/
  ISSUE_TEMPLATE/      # bug and improvement templates; /feedback reads them from the plugin
.claude-plugin/
  plugin.json          # plugin manifest; version gates updates for users
  marketplace.json     # makes this repo installable as its own marketplace
skills/
  <name>/
    SKILL.md
    scripts/           # optional, deterministic helpers and their tests
    references/        # rubric.md (required for skills that write documents), others on demand
    assets/            # optional, templates and static files
evals/
  <name>-<case>/       # required, one folder per test case, run by `claude plugin eval`
evals-failed-check/    # cases for what a skill does when the correction check fails; see Workflow
agents/
  <name>-reviewer.md   # one reviewer per skill that writes documents
  language-checker.md  # checks the wording beside every reviewer, for every skill that writes a document
  correction-checker.md # checks the corrections after a review, for every skill that writes a document
  build-correction-checker.md # checks the corrections after a build's reviews
  auditor.md           # /audit: checks the code against one accepted spec or ADR
  audit-checker.md     # /audit: tries to disprove one auditor's drift findings, or the brief checker's
  brief-checker.md     # /audit: checks accepted specs and ADRs against the brief
  audit-picker.md      # /audit: picks the documents a window of commits could affect
hooks/
  hooks.json           # session map, status checks, the review relay, reads of the plugin's own files, fresh sessions for /build, the build branch guard, the build review relay, the audit report hook, the practices limits
scripts/               # scripts the hooks run, the skill, version, reference and status-name checks, and their tests
docs/
  adrs/                # this plugin's own architecture decision records
  brief.md             # this plugin's own brief
  lifecycle.md         # the lifecycle rules, for people and for Claude at session start
  skills/<name>.md     # one page per skill, linked from README.md
AGENTS.md              # this file
CHANGELOG.md           # what each version changed, for the people who use the plugin
README.md              # user-facing: what the plugin is, its skills, and how to install it
```

Nothing else belongs at the root without a reason recorded in the change that adds it.

## Workflow

- Work on a branch and open a pull request; it merges once every check below passes.
- Before merging, run `claude plugin validate . --strict` and fix every finding. It checks the
  manifests only; skill limits are checked by `scripts/skill_check.py` (rule 3).
- Run the script tests for each skill you changed:
  `python3 -m unittest discover -s skills/<name>/scripts`, and for the plugin's own scripts if
  you changed them or any skill: `python3 -m unittest discover -s scripts`. All must pass.
- Run the evals for each skill you changed, once per supported model, with Sonnet as judge:
  `claude plugin eval . --case '<name>-*' --model <model> --judge-model sonnet --scaffold --allow-tools Write Edit -j 4 --ablation none`;
  without the grant, cases that write documents can't pass. A case whose prompt allows WebSearch
  or WebFetch needs them in the grant too, or the tools are withheld and the case proves nothing.
  The same goes for Bash: a case whose `allowed_tools` include Bash (every audit and build case,
  some spike cases) needs `Bash` in the grant, here and in the failed-check command below. On
  Linux, Bash cases also need `bubblewrap` and `socat` installed. Where the temporary folder
  (`TMPDIR`) is `/tmp` or a folder under it, as in a cloud session, they fail with "read-only
  file system": the eval puts each run's folder there, and its sandbox blocks writes to `/tmp`.
  Run them with a temporary folder outside `/tmp` that exists and anyone can write to:
  `mkdir -p /srv/evaltmp && chmod 1777 /srv/evaltmp`, then
  `TMPDIR=/srv/evaltmp claude plugin eval . --case '<name>-*' --model <model> --judge-model sonnet --scaffold --allow-tools Write Edit Bash -j 4 --ablation none`.
  `--ablation none` turns off the no-plugin comparison runs, which show how much a skill adds
  but don't decide whether a case passes; turn it back on (drop the flag) to measure that, for
  example before 1.0. `-j 4` runs four cases at once.
  The supported models are those named in README.md; a change merges only if its cases pass
  on every one. Evals are billed model runs: run the ones you touched, never the whole suite
  unprompted.
- The correction checker is a model, so no ordinary case can make it fail on demand. The cases in
  `evals-failed-check/` run against a temporary copy of the plugin in which the stand-in agents
  in `evals-failed-check/agents/` replace the agents they are named after: each reviewer always
  reports a correctable failure, and the checker always fails with a known finding. The cases live outside `evals/` so the real plugin never runs them. If you
  change a skill's review sequence, run its case through the script that builds that copy:
  `python3 scripts/failed_check_evals.py --case '<name>-*' --model <model> --judge-model sonnet --scaffold --allow-tools Write Edit -j 4 --ablation none`.
- Bump `version` in `.claude-plugin/plugin.json` in any change that alters what users receive,
  since installed copies only update when the version string changes. Follow
  [Semantic Versioning](https://semver.org/spec/v2.0.0.html): patch for a fix, minor for a new
  skill or new behaviour, major for a change that breaks documents people already have or the
  lifecycle itself. Stay below 1.0.0 until someone other than the maintainer installs the
  plugin; until then a breaking change bumps the minor version, and its changelog entry says
  what breaks.
- Bump in the branch's last commit, after bringing main into the branch and just before merging,
  so branches never compete for the next number and the bump survives any way of merging. In
  that commit, add an entry headed `## [X.Y.Z] - YYYY-MM-DD` at the top of `CHANGELOG.md`,
  written for the people who use the plugin: what they get, and for a major version what they
  must change.
  Run `python3 scripts/version_check.py` in that commit, whatever else the change touched: it
  checks that the newest entry matches `plugin.json` and is newer than the entry below it;
  whether a change needed a bump at all is yours to judge.
- Add a skill to the table in `README.md`, and give it a page under `docs/skills/`, in the same
  change that adds it.
