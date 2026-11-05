# Changelog

What changed in each version of the plugin, newest first. Versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html), and this file follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Read the entry before you update
past a major version: it says what you need to change in your documents. Until 1.0.0, any
minor version may need such a change, and its entry says so.

## [0.26.0] - 2026-11-05

### Added

- `/sdlc:practices` suggests a new topic, Delivering work: how work is split, how big one plan
  may be, measured by what a person can review, how many finished builds may wait for review,
  and what done means. It leaves out ways of working that exist for people rather than agents,
  such as sprint length, estimates and pair programming. Branches and commits now also asks how
  long a branch may live and how often it is merged back.
- `/sdlc:plan` reads your practices. Where they say how work is split or how big one plan may be,
  it plans within that; when the work is bigger, it proposes splitting it into several plans and
  asks which to plan first. If you keep the work as one plan, the plan says why under Decisions,
  and the plan's reviewer checks this.
## [0.24.3] - 2026-11-05

### Fixed

- On Python 3.6, the plugin now warns you when a session starts, rather than
  letting its checks fail later with an unclear error. The README now gives the minimum
  version, Python 3.7.

## [0.24.2] - 2026-11-05

### Fixed

- A correction check now works when Claude Code runs the reviews in the background, which it can
  do even when a skill asks for the foreground. The plugin's hooks used to keep a review's report
  only from the Agent tool's result, which for a background run is just a launch notice, so the
  correction checker was refused. They now keep the report that arrives when the agent finishes,
  for every document skill and for `/sdlc:build`, and no longer refuse reviews started in the
  background.

## [0.24.1] - 2026-11-05

### Fixed

- A correction check now works after the session ends and the same conversation carries on, as
  with `claude --resume` or a restarted cloud container. The plugin's hooks used to delete
  their saved reviews and build reports when a session ended, so the correction checker was
  refused. They now keep them, and delete any left unchanged for 30 days, the time after which
  Claude Code deletes the conversation itself. A resumed `/sdlc:build` session also keeps its
  branch guard. (#37)

## [0.24.0] - 2026-11-05

### Fixed

- Reviews now work when Claude Code is started in a folder other than the repository's, such as
  one holding several projects. Every skill that writes a document gives its reviewers the
  document's full path, and a plugin hook finds the repository from it, so each reviewer, the
  language checker and the correction checker read the document, and the documents they compare
  it with, from the right repository. A review of a document the hook can't find is refused, and
  an agent that still can't read its document reports an error, never a pass. `/sdlc:audit`'s
  agents follow the same rule.

## [0.23.1] - 2026-11-05

### Fixed

- `/sdlc:audit` no longer reports a clean result for documents it never read. Run from a folder
  other than the repository's, its agents used to look for the documents in the wrong place,
  find nothing and report no drift. Now every agent is given the repository's full folder, and
  an agent that still can't read its document reports an error, which the audit lists first as
  a document not checked. To audit a repository that isn't the folder you are in, name it, such
  as "audit the code in invoice-tool/".

## [0.23.0] - 2026-11-05

### Changed

- A brief or a spec can now have sections beyond the six it needs, such as "Safety and security"
  in a brief or "Security" in a spec, when you ask for them. The six must still all be there in
  their order, and Open questions stays last. Every other check applies to the new sections too,
  so they can't hold a feature list, a design or a guess, and a spec's requirements stay under
  Requirements. Before, the reviewer failed any section beyond the six.

## [0.22.0] - 2026-11-05

### Added

- `/sdlc:audit` finds drift, where the code and its documents no longer agree. A script checks
  every spec, ADR, plan and spike record as it stands: statuses, open questions, references,
  supersede pairs, ready plans and plans that build the same requirement. Then one fresh agent per
  `👍 Accepted` spec and ADR checks the code against it, and a second agent tries to disprove
  each drift it reports before you see it. Each finding comes with quotes of the document and the
  code, and a suggested correction and the skill that makes it. It can check the whole
  repository, the commits of a window (`last 7 days`, or `since <commit>`), or one named
  document, and it changes nothing in your repository, so it is safe to run as a scheduled
  routine. If your practices say what to do with its findings, such as filing issues, it does
  that once it has reported.

## [0.21.0] - 2026-11-04

### Added

- `/sdlc:spike` settles one unknown by a throwaway experiment. It writes a spike record in
  `docs/spikes/`: the question, the result that would answer it, the experiment and its code.
  Once the design is reviewed and you sign it off, it runs the experiment only through its run
  script, which writes each run's output into the record word for word. Then it writes the answer,
  has that reviewed too, and tells you which spec or ADR the answer belongs in. Experiments run
  in a fresh folder outside your repository, so your working tree is never touched. Secrets
  reach them only from Claude Code's environment, and are hidden in the recorded output.
- Spike records have their own statuses: `📝 Draft`, `🟢 Ready to run`, `💡 Answered` and
  `❔ Not answered`. The status hook enforces them. It also refuses any edit to a record's runs,
  and any change to a finished record.

### Changed

- `/sdlc:spec`, `/sdlc:adr`, `/sdlc:brief` and `/sdlc:plan` never refer to a spike record, so it
  can be deleted at any time. `/sdlc:spec` and `/sdlc:adr` can draft from a finished record, and
  state its evidence in their own words.

## [0.20.0] - 2026-11-04

### Changed

- Skills that write documents no longer review after every answer. While you walk through open
  questions, the review runs once when the walk-through ends, because no questions are left or
  you stop. A change you make or ask for at any other time is still reviewed once it is made. The lifecycle page's Review process says when a review
  runs, and a script check makes every such skill, including future ones, carry the same rule.
- The README says to install the plugin before starting the session you will use it in, since a
  plugin installed partway through a session only loads in the next one.

## [0.19.0] - 2026-11-04

### Added

- `/sdlc:practices` has a CI/CD topic. It asks where the pipeline is defined and what it runs,
  which checks are required, how to run them locally before pushing, what an agent does when a run
  fails (reproduce it, fix the cause, re-run at most once, never skip or disable a test), who may
  change the pipeline and how deployments start. Which CI service to use is left for
  `/sdlc:adr`.

### Fixed

- The `/sdlc:practices` overview reads the practices and the repository again each time, even
  later in a conversation, so it sees changes made outside it.
- `/sdlc:practices` no longer calls an answer recorded before the files are written.

## [0.18.0] - 2026-11-04

### Added

- `/sdlc:practices` records how your project does things, for coding agents to follow: the
  commands that set it up, run it and check the work, the rules an agent follows, and the files
  to read before a task. The essentials go in a `## Practices` section of `AGENTS.md`, and longer
  topics in files under `docs/practices/`. On its own it gives an overview of what is recorded,
  missing or out of step with the repository, and suggests where to start; with a topic, such as
  `/sdlc:practices testing`, it covers that topic alone. It reads the repository first and
  proposes what it finds, asks one question at a time, never writes a secret or makes a choice
  between technologies, and adds the line `@AGENTS.md` to `CLAUDE.md`, asking first if you
  already have one. Its changes are reviewed, corrected once and checked like every document.
- A hook refuses any edit by Claude that would take the Practices section past 50 lines or a
  practices topic file past 200, or that adds an `@` import to either.

### Changed

- One review can now cover several files at once, so a change to the Practices section and to a
  topic file is reviewed, corrected and checked together.

## [0.17.1] - 2026-11-04

### Added

- The plugin is released under the MIT licence, in `LICENSE`, so you may use, change and share
  it in your own and your clients' projects.

## [0.17.0] - 2026-11-04

### Changed

- `/sdlc:plan` writes a reviewer's decision that only you can make into the plan's Open
  questions, as `/sdlc:spec` and `/sdlc:adr` already do, so the plan cannot be marked
  `🟢 Ready to build` until you have settled it.
- The spec and brief reviewers now see the titles of your ADRs and plans, so they catch a
  reference to one by its title.
- The lifecycle rules now say an ADR may refer to any other ADR by number, as the ADR reviewer
  already allowed.

### Fixed

- The README and the `/plan` page no longer say a built plan is removed: it is kept for good, as
  the lifecycle says.
- The docs no longer describe `/audit` as working, or the language checker as part of
  `/sdlc:build`'s review.
- `/sdlc:spec`'s description no longer calls accepting a spec "ready to build".
- Smaller corrections across the README, the lifecycle rules and the skill pages, so they agree
  with each other and with the skills.

## [0.16.0] - 2026-11-04

### Changed

- `/sdlc:issue` is now `/sdlc:feedback`: same skill, new name. Type the `sdlc:` prefix, since in
  the terminal a bare `/feedback` is Claude Code's own command, which sends feedback to
  Anthropic. It still drafts and files a GitHub issue on the plugin's repository.

## [0.14.1] - 2026-11-04

### Fixed

- In a Claude project thread, the correction check failed every time: an agent's report reaches
  Claude there as a separate message, and the hooks that keep review reports saved only the
  tool's note saying where the report went. They now keep the report itself, for document
  reviews and for `/sdlc:build`'s reviews.

## [0.14.0] - 2026-11-04

### Added

- The design of `/sdlc:practices`, a skill not built yet, on its own page. It will record how a
  project does things, one topic at a time and whenever you need it: the essentials in a
  `## Practices` section of `AGENTS.md`, at most 50 lines, and longer topics in
  `docs/practices/`. `/sdlc:build` follows them.

### Changed

- The README and the lifecycle rules show the skills in three groups, each with its own small
  diagram: deciding what to build, building it, and skills used at any time.
- Recorded practices are the one thing the plugin writes outside the lifecycle's own documents,
  and only when you ask it to.

## [0.13.0] - 2026-11-04

### Added

- `/sdlc:build` builds one `🟢 Ready to build` plan on a branch of its own, tests first,
  requirement by requirement. It then has the work checked by three reviews side by side: Claude
  Code's own `/code-review` and `/security-review`, and a build reviewer that checks the work
  against the plan, its specs and ADRs. It corrects what they find once, has the corrections
  checked, and hands the branch back, committed and pushed. It never opens a pull request and
  never merges: verifying the software, opening a pull request and merging stay with you.
- `/sdlc:build` starts only in answer to the first message of a session, or the first after
  `/clear`, so a build always begins with a clean context. A plugin hook enforces this.
- Before starting, `/sdlc:build` checks that the plan is ready, that the specs and ADRs it names
  are still `👍 Accepted`, that nothing is uncommitted, that the repository has a remote named
  `origin` whose default branch git knows, and that `/code-review` and `/security-review` can
  run. It stops and says why if any check fails.
- While a build runs, a plugin hook refuses any commit or push to the default branch.
- `/sdlc:build` leans towards carrying on rather than asking. It corrects obvious defects, such
  as a crash on input no spec mentions, chooses error wording and exit codes, takes its own
  recommendation on choices that are easy to change later, and works out from the repository any
  practice that is not recorded, such as how to run the tests. Its summary lists each of these.
  It stops only for a real product choice or something hard to undo.
- A hand-over script commits what is left, marks the plan `✅ Built` when every review passed,
  and pushes the branch, reporting exactly what it did.

### Changed

- A `✅ Built` plan is kept as the record of what was built and how, and is never changed. Only
  `/sdlc:build`'s hand-over script sets `✅ Built`; the hook refuses it from anywhere else.
- The plugin is now tested on Opus 5.5 only. Its reviewers still run on Sonnet.

### What you need to change

- To use `/sdlc:build`, your repository needs a remote named `origin`. If `git` does not know
  its default branch, run `git remote set-head origin -a` once.

## [0.12.0] - 2026-11-03

### Changed

- Specs now have the statuses `📝 Draft` and `👍 Accepted`. A spec's status says whether you
  have accepted its text; it describes the document, never the software, because a status about
  the software would stop being true, without anyone noticing, as the code changes. To find out
  whether the software meets a spec, check the software against it. `/sdlc:spec` sets
  `👍 Accepted` when you sign a spec off, under the same rules `🟢 Ready to build` had, and any
  change returns it to `📝 Draft`.
- A plan can be `🟢 Ready to build` only when every spec it names is `👍 Accepted`.
- The hook refuses a new spec or plan written with another kind of document's status, such as a
  new spec written as `✅ Built`.

### What you need to change

- A spec that is `🟢 Ready to build` or `✅ Built` keeps that status until it is next changed,
  and the hook does not check it until then. Before `/sdlc:spec` can accept it, set it back to
  `📝 Draft`, then accept it again; a plan that names it cannot be `🟢 Ready to build` until it
  is `👍 Accepted`.

## [0.11.0] - 2026-10-29

### Added

- `/sdlc:plan` plans one piece of work before it is built. It finds the requirements of settled
  specs and the accepted ADRs the work builds, explores the code with Claude Code's own Explore
  and Plan helper agents, and settles each technical decision with you one at a time, proposing
  an answer and whether it belongs in the plan or in an ADR. Only then does it write a short plan
  in `docs/plans/YYYY-MM-DD-<title>.md`, have it reviewed and corrected once, and hand it to you.
  It never makes a technical decision for you, and it does not use Claude Code's plan mode.
- Plans have the statuses `📝 Draft`, `🟢 Ready to build` and `✅ Built`. The hook refuses
  `🟢 Ready to build` unless the plan has no open questions, every spec it names is
  `🟢 Ready to build` or `✅ Built` and holds each requirement it names, every ADR it names is
  `👍 Accepted`, and no other plan that is not `✅ Built` names the same requirement. Any change
  to a `🟢 Ready to build` plan returns it to `📝 Draft`. Only the build step will set
  `✅ Built`; until it exists, the hook refuses it.
- A plan reviewer agent checks each plan against the plan rubric, beside the language checker.

### Changed

- In a plan, as in an issue, the lifecycle's own terms such as "spec", "ADR" and the statuses
  count as plain words.
- The language checker no longer reads a document's frontmatter, whose wording the plugin fixes.

## [0.10.0] - 2026-10-29

### Changed

- ADRs now end with an Open questions section, as specs do. Whatever only you can settle, such
  as an option nobody named or why one was rejected, is written there instead of only being
  asked in the conversation. Your answer goes into the ADR and the question is removed.
- An ADR can be `👍 Accepted` only when its Open questions section is empty or says "None.". The
  hook refuses the change otherwise, and says so when the section is missing altogether. A
  `❌ Rejected` ADR may keep open questions.
- New ADR files are named `NNNN-<subject>.md`, where the subject is three to five words on what
  the decision is about, such as `0004-session-data-storage.md`. The title inside still states
  the decision.
- The lifecycle has a new principle: no document moves forward while it has open questions.

### Fixed

- The hook no longer counts the indented lines of a wrapped footnote after Open questions as
  open questions, which could block a spec or ADR from moving forward.

**This affects documents you already have.** A `📝 Draft` ADR written before this version has
no Open questions section, so it cannot be accepted until one is added, holding "None." if
nothing is open; that change needs a new review. ADRs that are already decided need nothing.
Renaming older ADR files to the new pattern is optional and done by hand, with `git mv`.

## [0.9.0] - 2026-10-29

### Changed

- Every document status now starts with an emoji: `📝 Draft`, `🟢 Ready to build`, `✅ Built`,
  `👍 Accepted`, `❌ Rejected` and `↪️ Superseded`. New specs and ADRs are written that way, and
  the plugin's pages name each status the same way.
- The plugin's hook now refuses a status written without its emoji, or with the wrong one, and
  says what to write instead. **This affects documents you already have.** A spec or ADR whose
  status is a bare word, such as `status: Accepted`, still counts as that status, but the next
  change Claude makes to it must also add the emoji. A change that only adds the emoji to the
  status line is always allowed, even on an ADR that is already decided. To bring every document
  over at once, ask Claude to add the emoji to each status line under `docs/specs/` and
  `docs/adrs/`.

## [0.8.1] - 2026-10-29

### Fixed

- On a computer without Python 3, the hook that checks spec and ADR status changes failed with
  only a warning, so Claude's edits to those documents went through unchecked. Such edits are
  now refused, with a message saying the plugin needs Python 3. Edits to any other file are not
  affected.

## [0.8.0] - 2026-10-29

### Added

- A language checker reads every document `/spec`, `/brief`, `/adr` and `/issue` write, at the
  same time as the skill's reviewer, and reports any words someone new to your project could not
  follow. The skill corrects what both reports find in its one round of corrections, and the
  correction checker checks those corrections too. The reasons, with the measurements behind
  them, are in this plugin's ADR 0013.
- A Plain words rule in the lifecycle page says what the checker holds documents to: computing
  terms are used freely, a term from your product's own field gets a footnote defining it where
  it first appears, and anything else a newcomer would not know, such as a team nickname or a
  figure of speech, is rewritten in plain words.

### Changed

- The brief's rubric no longer has its own plain words check, since the language checker now
  does that job for every skill.
- The note at the top of a new spec or ADR, and the prompt in the spec template's Problem
  section, are reworded in plain words.
- When a new spec conflicts with another spec, the hand-over names that spec and the rule that
  conflicts, since the spec itself cannot refer to it.

## [0.7.0] - 2026-10-28

### Changed

- `/spec`, `/brief`, `/adr` and `/issue` now take every document through a fixed review
  sequence: one review, one round of corrections, then a check of only those corrections by a
  shared correction checker. If the check fails, the skill stops and shows you its report rather
  than reviewing again. The reasons, with the measurements behind them, are in this plugin's
  ADRs 0010 and 0011.
- When the sequence ends, the skill gives you the review report, the check's report, the number
  of items left for you to settle, and then asks you about the first of them only. The reviewers'
  suggestions are listed separately as optional.
- `/adr` is also used when you ask to review or correct an existing ADR.

### Added

- A hook hands the correction checker the review report and the document as it was reviewed,
  word for word. It keeps them in the plugin's own data folder, outside your repository, and
  deletes them when the check is done or the session ends.
- A hook lets the plugin's skills and agents read the plugin's own files, such as a rubric,
  without asking you each time. It approves reads inside the plugin's folder only.

## [0.6.0] - 2026-10-27

### Added

- A new rule for the whole lifecycle: documents refer to one another only where neither end can
  go stale. A plan refers to the specs and ADRs it builds, and an ADR to the ADR it supersedes or
  that supersedes it. The brief, specs and ADRs never refer to one another in any way, whether
  by hyperlink, path or title, because either end can change or be deleted without the other
  being touched. The README and the summary Claude gets at the start of each session say so.
- The spec and brief rubrics have a References check, so their reviewers flag any such
  reference. When you ask `/spec` or `/brief` to add one, it leaves it out and tells you why.
  The brief still links to source material, such as a survey, as before.

### Changed

- A spec or brief you already have that refers to another lifecycle document now fails review
  the next time `/spec` or `/brief` changes it, which removes the reference. Nothing else in
  your documents needs to change.

## [0.5.0] - 2026-10-27

### Added

- `/adr` records one technical decision as an ADR (architecture decision record) in
  `docs/adrs/NNNN-<title>.md`, using the core of the MADR format: the context, the options
  considered and why each lost, the decision, its good and bad consequences, and a Confirmation
  saying what it applies to and how to check the code follows it. It drafts from your
  conversation, writes one ADR per decision, and has each one reviewed before you see it.
- ADRs move from Draft to Accepted or Rejected, and from Accepted to Superseded when a newer ADR
  replaces them. Only you can accept or reject an ADR: `/adr` asks you once the reviewed text is
  final.
- The status hook now covers ADRs too: it refuses status changes the lifecycle does not allow,
  and any edit to an ADR that is no longer a Draft, apart from marking it Superseded by an
  accepted replacement.

### Changed

- ADRs live in `docs/adrs/`, not `docs/decisions/`, and start as Draft rather than Proposed.

## [0.4.1] - 2026-10-27

### Added

- This changelog. Claude Code tells you when the plugin has updated but not what changed, so
  each version now has an entry here; the README's Update section points to it.

### Changed

- The plugin's versions follow Semantic Versioning: a fix is a patch, a new skill or new
  behaviour is a minor version, and a change that breaks documents you already have, or the
  lifecycle, is a major version. Until 1.0.0, a breaking change bumps the minor version and
  its entry says what breaks.

## [0.4.0] - 2026-10-27

### Added

- `/brief` writes or changes your product brief, `docs/brief.md`: the one short document that
  says what the product is, who it is for, why it exists and how you will know it works. It
  has a one-line summary and sections for Problem, Who it's for, Goals, Out of scope,
  Constraints and Open questions. Unlike a spec, a brief has no status.
- `/brief` drafts from what you have already said, reads only what you point it to, and asks
  before reading anything else. It gives the number of open questions and asks them one at a
  time, and it explains every acronym the first time it appears, title included.
- A brief reviewer checks the draft against the brief rubric before you see it. Where the
  brief links a document in your repo, the reviewer also checks the brief against it. Any
  remaining decisions are left to you.

## [0.3.0] - 2026-10-27

### Added

- `/issue` reports a bug or suggests an improvement in this plugin. It drafts the issue from
  the plugin's bug or improvement template, filling in Context with the plugin, Claude Code and
  operating system versions, and it can propose an eval case for the fix.
- Your project's details stay out of the issue: `/issue` paraphrases rather than quoting your
  repo, and replaces real names and code with stand-ins. An issue reviewer checks the draft
  before you see it.
- Nothing is filed until you approve the draft. `/issue` then files it with `gh`, as the
  GitHub account it showed you, or gives you a pre-filled link to submit yourself.

## [0.2.1] - 2026-10-27

### Added

- `/spec` writes or changes a spec with you: one living document per capability under
  `docs/specs/`, with sections for Problem, Goal, Scope, Requirements, Constraints and Open
  questions. Each requirement is one rule with Given/When/Then scenarios and a "Verified by:"
  line saying how it will be checked.
- `/spec` drafts from what you have already said and asks only about the gaps: it gives the
  number of open questions, then asks them one at a time. It keeps technical choices out of
  the spec and adds no behaviour you didn't ask for.
- A spec reviewer, which always runs on Sonnet, checks every draft against the spec rubric
  before you see it. It separates decisions only you can make, which block Ready to build,
  from suggestions, which don't. `/spec` fixes what it can and passes the rest to you.
- Spec statuses: Draft, Ready to build and Built. A spec becomes Ready to build only once you
  have seen its final text, it has no open questions and its review has passed. Built is
  reserved for `/build`, which isn't released yet.
- A session-start hook that gives Claude a short map of the lifecycle, only in repos that use
  it.
- A hook that refuses spec edits making a status change the lifecycle doesn't allow, such as
  skipping Draft or setting Ready to build while open questions remain.

## [0.1.1] - 2026-10-26

### Changed

- The README now explains the whole lifecycle for a reader starting with no context: the
  Planning steps (`/brief`, `/spec`, `/spike`, `/adr`, `/plan`), Building (`/build`) and
  `/audit`. Each skill has its own page under `docs/skills/`; for skills not yet released,
  that page is a placeholder.

## [0.1.0] - 2026-10-22

### Added

- The plugin and its own marketplace, so you can install it with
  `claude plugin marketplace add michaelmarconi/sdlc` and `claude plugin install sdlc@sdlc`.
  It has no skills yet.
