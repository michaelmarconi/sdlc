# Changelog

What changed in each version of the plugin, newest first. Versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html), and this file follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Read the entry before you update
past a major version: it says what you need to change in your documents. Until 1.0.0, any
minor version may need such a change, and its entry says so.

## [0.51.0] - 2026-11-14

### Changed

- `/build` and `/audit` now hand back their full report as a Markdown file, beside a reply of a
  few lines naming it, instead of a long summary in the conversation
  ([#85](https://github.com/michaelmarconi/agentic-engineering/issues/85), ADRs 0033 and 0034).
  The file is kept in the plugin's data folder, under `reports/<repository>/`, or in a private
  folder in the system's temporary folder where that can't be written, and is shown in the app's
  file viewer where there is one.
- A script writes the file: Claude gives it only its own sections, and the script copies in, word
  for word, the hand-over script's output, the build's three review reports and the correction
  check's report, or each audit agent's report. A build that refuses before it starts, or an
  audit that stops before its first agent starts, writes no file: the reply says why.
- A new hook, `scripts/audit_relay.py`, keeps the audit agents' reports for the file, and the
  build's hook now keeps the review reports until the hand-over.
- `audit.py` has two new commands, `start` and `report`, and `hand_over.py` takes `--report`,
  `--data` and `--session`.

## [0.50.0] - 2026-11-14

### Fixed

- The plugin's hooks now find the git repository from the file they act on, so they work when
  Claude Code starts in a folder above the repository, as in a Claude project thread
  ([#84](https://github.com/michaelmarconi/agentic-engineering/issues/84), ADR 0032). Before,
  `/build`'s correction check was always refused there, because the commit the reviews saw
  could not be recorded; the hooks that check document statuses, references between documents
  and the size of recorded practices let changes through unchecked; and the lifecycle rules were
  not given to Claude at the start of the session.

### Changed

- `/build` gives the plan's full path on every review request, so the reviews and the
  correction check use the plan's repository whatever folder you started in.
- When no git repository holds the plan, the correction check is refused with that reason,
  instead of a reason about a commit.
- ADR 0032 supersedes ADR 0022: one shared rule, in `scripts/repository.py`, for every hook.

## [0.49.0] - 2026-11-12

### Changed

- `/build` lets you build a plan before it is signed off, if you choose to
  ([#77](https://github.com/michaelmarconi/agentic-engineering/issues/77)). When the plan, or a
  spec or ADR it lists, is `📝 Draft`, it no longer refuses. It runs its other checks, lists what
  isn't signed off, including the plan's open questions, and asks "Build anyway, on the proposed
  answers?". Pick "Build anyway" and it builds each open question's proposed answer, asking you
  any question that has none. Pick "Stop and settle them first" and it changes nothing. It never
  builds an unsigned plan without your answer in the conversation.
- A build before sign-off records in a commit what wasn't signed off and how each open question
  was answered, so the record is in git. No document's status changes: the plan stays
  `📝 Draft` until you settle it and sign it off, and a later `/build` on the branch marks it
  `✅ Built`.
- A spec or ADR that is `❌ Rejected` or `↪️ Superseded`, a missing one, or a missing requirement
  heading still stops the build, with no offer to build anyway.

## [0.48.0] - 2026-11-12

### Changed

- When a build can't start because the session isn't fresh, the message now says the plugin has
  no reliable way to start a new session for you, then gives the two steps: run `/clear`, then send
  `/agentic:build` with the plan's path. In a Claude project thread, which has no `/clear`, it says
  to open a new thread and send that command as its first message. Before, it only said to start a
  new session. The plugin never tries to start a session itself (ADR 0031).
- When you sign a plan off as `🟢 Ready to build`, `/plan` ends its reply with the same two steps,
  for that plan.

## [0.47.1] - 2026-11-12

### Fixed

- `/build` now always reaches its correction check after the code review finds something
  ([#79](https://github.com/michaelmarconi/agentic-engineering/issues/79)). It runs `/code-review`
  inside a `general-purpose` agent, as it already ran `/security-review`, so the review's report
  reaches the plugin's hook whatever way the Claude Code version runs the skill: forked into an
  agent of its own, or inside the session, reporting through a tool the hook never sees. The hook
  no longer reads the Skill tool's result.

## [0.47.0] - 2026-11-12

### Changed

- The brief now changes only when you decide the product's intent has changed. No skill proposes
  editing it to match a spec or ADR, and changing the brief edits no other document.
- `/spec` raises the brief only when a spec contradicts its Goals, Out of scope or Constraints,
  such as a rule for something the brief puts out of scope. Detail the brief doesn't mention is
  never raised. A contradiction becomes an open question in the spec with two answers: change the
  spec, or you change the brief. Once you settle it, it is not raised again. The spec rubric gains
  check 15, "Fits the brief".

### Added

- `/audit` checks accepted specs and ADRs against the brief, with one new agent, `brief-checker`,
  that reads documents only. A second agent tries to disprove each contradiction before it is
  reported under "Contradicts the brief", with quotes of both and both corrections named. A window
  in which the brief changed checks every accepted spec and ADR against it.
- The audit script's `documents` command reports the brief's path as `brief`, and `window` reports
  `brief_changed`.

## [0.46.0] - 2026-11-12

### Changed

- A spike record's plain part now has two word limits: at most 600 words for the design, written
  before the runs, and 400 for the verdict, its Finding, Next steps, Results and Surprises, written
  after them. One 600-word limit used to cover both, so a design close to it left the verdict no
  room. The status hook checks both at every move forward, and `spike.py words` reports both.
- In a spike record, the lifecycle's own terms, such as "spec" and "ADR", count as plain words, as
  they already did in issues, plans and practices, so the template's `- Spec:` and `- ADR:` lines no
  longer fail the wording check.
- A spike record's Inputs are only files the run keeps a copy of. A site or service the experiment
  talks to, such as the one it tests, is not an input, since the run script downloads every input
  before the run starts and an address that can't simply be downloaded stopped the run.
- The verdict review judges only what can still change after the runs: the verdict, and the title,
  Code and Open questions. The design was reviewed and signed off before the runs and is fixed, so a
  finding about it could never be corrected and left the record unable to finish.

### What you need to change

- Nothing in finished spike records. A record that is not finished and holds more than 400 words in
  its Finding, Next steps, Results and Surprises must shorten them before it moves on.

## [0.44.1] - 2026-11-12

### Fixed

- An open question's **Proposed:** and **Why:** lines could show as one line, because without a
  line holding only `>` between them Markdown joins them into one paragraph. The skills now write
  that line, the status hook refuses Open questions without it, and `/audit` lists documents that
  lack it. To correct a document, add a line holding only `>` between the two lines.

## [0.44.0] - 2026-11-11

### Changed

- Every open question in a brief, spec, ADR, plan or spike record is now a numbered heading,
  `### 1. <what is to be settled>`, then the context it needs, then a block quote holding one
  `> **Proposed:**` line with the answer and one `> **Why:**` line with the reason, so the
  proposal is easy to spot. Each question holds one proposal: a question with two answers becomes
  two questions. ADR 0030 records the choice.
- The status hook refuses an edit that adds or changes Open questions in any other layout, naming
  the entry and what is wrong. An edit that leaves Open questions as they were is allowed, so older
  documents can still be edited.
- When a skill asks you to settle a question in the conversation, it shows a bold line such as
  "**Question 1 of 3: …**", the context, the same Proposed and Why quote, and the question itself
  last. This covers `/brief`, `/spec`, `/adr`, `/plan`, `/spike` and `/practices`.

### Added

- `/audit`'s document check lists each document whose Open questions are not in the new layout,
  leaving out documents that are never edited again, such as an accepted ADR or a built plan.

### What you need to change

- Nothing at once. A document written before this keeps its old Open questions until they next
  change; the change then has to bring the whole section into the new layout. Run `/audit` for the
  list of documents to bring over.

## [0.43.1] - 2026-11-11

### Fixed

- When `/plan`'s correction moves a Decisions line to Open questions, its "Proposed:" keeps the
  decision as the person agreed it. It sometimes proposed a different decision instead, so
  answering "yes" reversed what had been agreed. Any doubt about the decision now goes in the
  question's text. Nothing in your documents needs to change.

## [0.43.0] - 2026-11-11

### Added

- `/plan` offers diagrams at the hand-over, the same way `/adr` does: a flowchart of parts that
  call each other, a sequence diagram of events between actors, a state diagram or an
  entity-relationship diagram, each only when the plan's text names at least three of its things
  and two connections between them. It asks "Would you like to add any of these diagrams to the
  plan, or propose another?", draws nothing you don't pick, and never holds a plan back from
  `🟢 Ready to build`. A picked diagram is a `mermaid` block after the Plan section's opening
  paragraph; the plan rubric's new check 13 fails any box or arrow its text does not hold, and
  check 7 (no code) allows it. Only a `📝 Draft` plan gets the offer.

### Changed

- `/adr` and `/plan` ask the diagram offer's question word for word even when they offer a single
  diagram, and share more of the offer's wording, checked by the plugin's skill check.
- The ADR and plan reviewers fail a diagram's arrow unless the text says that one thing calls,
  sends to or is read by the other; naming both is not enough. Nothing in your documents needs to
  change.

## [0.42.2] - 2026-11-11

### Fixed

- `/build` no longer refuses to start on Linux with Claude Code's sandbox on. The sandbox puts
  stand-ins for `/dev/null` in place of files it protects, such as `.bashrc` and
  `.claude/settings.json`, and git lists them as untracked, so `/build` took them for
  uncommitted work. A new script, `uncommitted.py`, lists what is uncommitted and leaves those
  stand-ins out.
- The hand-over no longer drops the build's last work there. Git can't add the stand-ins, and one
  it can't add stopped the hand-over from adding anything, so the branch was pushed without the
  work and no error was shown. It now leaves the stand-ins out, and reports a failed add.

## [0.42.1] - 2026-11-11

### Fixed

- The plan reviewer no longer fails a plan's Decisions lines whose reason nobody needs once the
  work is built, such as a test's data or the order of the steps, by asking for the comment
  wording. Rubric check 5 now passes a line that only follows a spec, an ADR, the practices or
  existing code, and asks five questions of every other line in order, stopping at the first yes:
  must later work follow it (an ADR), does a user or caller rely on it (the spec), does every
  piece of work do it this way (the practices), would someone changing the code need the reason
  (a comment beside the code), or otherwise nobody. In a trial on seeded plans, false alarms fell
  from 22 of 39 to 1, with the same catches. A line that fails only for lacking the comment wording
  now gains that wording in the correction instead of moving to Open questions. Nothing in your
  documents needs to change.

## [0.42.0] - 2026-11-11

### Added

- `/adr` offers diagrams of the chosen option. Once Decision says "Chosen:", each hand-over
  offers one line per diagram the text has enough for (at least three parts, actors,
  states or records and two connections between them), drawn as a flowchart, sequence diagram,
  state diagram or entity-relationship diagram. While questions are open the offers sit with the
  optional suggestions; once none are left, it asks "Would you like to add any of these diagrams to
  the ADR, or propose another?". Nothing is drawn unless picked. A picked diagram is a
  `mermaid` block in Decision, after the reason, drawn only from what the text says; rubric check
  18 has the reviewer check every box and arrow against the text.
- A `mermaid` diagram in an ADR's Decision does not count towards the 500 words of the plain part.
- The offer's sentences are shared in `scripts/skill_check.py`, so `/plan` can hold the same ones.

## [0.41.0] - 2026-11-11

### Changed

- ADR and spike reviews no longer count sentences. A sentence over 25 words, a paragraph of more
  than three sentences, a Question or Hypothesis over three sentences, or a reason for the choice
  over two no longer fails a review or a correction check. The reviewer checks instead that each
  paragraph makes one point and that a newcomer can follow every sentence in one reading, quoting
  any sentence that fails. The counts stay in `/adr` and `/spike` as a guide for the writer, and a
  reviewer may list a long sentence only as a suggestion. The word limits for the plain part, 500
  for an ADR and 600 for a spike record, are unchanged and still checked by script. Nothing in
  your documents needs to change.

## [0.39.1] - 2026-11-11

### Fixed

- When a plan's review fails a Decisions line on rubric check 5, `/plan`'s correction moves the
  line to Open questions, naming the ADR, spec change or practice it belongs in, instead of
  rewording it in place, which left the decision in the plan.

## [0.39.0] - 2026-11-11

### Changed

- `/plan` keeps a decision under Decisions only if nobody needs its reason once the work is
  built. A decision later work must follow goes to an ADR, one a user or caller relies on, such
  as what a tool returns, to the spec, and one every piece of work follows, such as how a check by
  hand runs, to practices: each as an open question naming that document. A decision whose
  reason only someone changing the code later needs stays, saying `/build` leaves the reason as a
  comment beside the code, and `/build` and its reviewer now see that the comment is there. Plan
  rubric check 5 goes through Decisions line by line with the same test.
  **Change needed:** a plan that is not `✅ Built` may now fail its next review on a Decisions
  line that passed before; move such a line to Open questions as the review says, or add the
  comment wording to a line whose reason only someone changing the code needs.

## [0.38.0] - 2026-11-11

### Changed

- A plan lists each requirement as a link to its heading in the spec, nested beneath the spec,
  as `  - [Reply to all](../specs/mail.spec.md#2-reply-to-all)`, in place of
  `  - Requirement: Reply to all`, and lists its ADRs as a `| ADR | Decision |` table, with the
  ADR's number as the link and its title beside it. The hook checks each anchor is the one GitHub
  gives the heading, and each title is the ADR's own, and names the right one when it is not.
  **Change needed:** a plan that is not `✅ Built` and still uses `- Requirement:` lines or ADR
  bullets is refused at sign-off with a message saying how to rewrite it; `/plan` rewrites those
  sections with its next edit, and `/audit` lists a `🟢 Ready to build` plan in the old layout
  until it is rewritten. Built plans are never checked, so they need nothing.
- In practices, the marks `/practices` ends a practice with, "(default)" and "(not set up yet)",
  count as plain words, so the language checker no longer reports them.

## [0.37.1] - 2026-11-11

### Fixed

- In auto mode, as in the Claude desktop app, a review agent that Claude Code ran in the
  background could lose its report, so the correction checker was refused with "No review ...
  is on record". The agent hands its report back as it finishes, and the plugin read it from the
  agent's transcript, which may not hold it yet. The plugin now takes the report from the
  hand-back itself, for document reviews and for /build's reviews. When the correction checker is
  refused for a missing report, the reason now names which report is missing.

## [0.37.0] - 2026-11-11

### Changed

- In practices, the Practices section of `AGENTS.md` and the files under `docs/practices/`, the
  lifecycle's own terms such as "spec", "ADR" and the statuses count as plain words, as they
  already did in an issue or a plan, since agents that follow the lifecycle read them. The
  plugin's commands, such as `/agentic:build`, now count as plain in all three.

## [0.36.0] - 2026-11-10

### Changed

- The plugin is now called `agentic`, for Skills for Agentic Engineering, and its skills are
  `/agentic:<name>`, such as `/agentic:spec`. Its repository is now
  `michaelmarconi/agentic-engineering`, and new installs come from the `michaelmarconi` catalog:
  `claude plugin marketplace add michaelmarconi/marketplace`, then
  `claude plugin install agentic@michaelmarconi`.
- New documents carry "Change status only through the agentic plugin's skills" as their comment
  line. Documents that say "sdlc" there need no change.

### If you installed `sdlc@sdlc`

1. Finish any review, build or spike in progress first: the plugin's saved records of them are kept
   under the old name and are not carried over.
2. Run `claude plugin marketplace update sdlc`. This rewrites `sdlc@sdlc` to `agentic@sdlc` in your
   settings, including a repository's `.claude/settings.json`, which you then commit.
3. Run `claude plugin install agentic@sdlc`, adding `--scope project` if you installed it that way.
4. Use `/agentic:<name>` from now on, and change any notes or scheduled commands that use the old
   `sdlc` prefix.

If step 2 cannot reach the catalog, run `claude plugin marketplace remove sdlc` and install from
the new catalog as above instead, adding `--scope project` if you installed it that way, and
commit the settings change. Moving to the new catalog later is described in the README. Never
enable both `agentic@sdlc` and `agentic@michaelmarconi`.

## [0.35.0] - 2026-11-10

### Changed

- `/sdlc:adr` no longer lets a choice rest on something nobody has tried. When the conversation says
  the choice depends on such a claim, such as "this only works if the provider sends events in
  order", the claim becomes the first open question, proposing a spike to test it, instead of being
  left under Out of scope "to be proven in the build". It stays open until the spike's finding comes
  back; a refuted claim opens the choice again. Only if you choose to go ahead without a spike does
  the ADR record the claim as untested at your word, under Consequences. Caveats you mention stay
  under Out of scope as limits.
- `/sdlc:spike` sends a finding that settles an ADR's open question to that ADR.

## [0.34.0] - 2026-11-10

### Changed

- Every spec, ADR, plan and spike record carries `date:` in its frontmatter: the day its status
  last changed, written YYYY-MM-DD. The skills write today's date into a new document and set it
  in the same edit as every status change, `/sdlc:build` sets it when it marks a plan `✅ Built`,
  and the status hook refuses a new document or a status change without today's date, any other
  change to the date, and a date after today. An ADR's date, which had no stated meaning, now
  means the same, so superseding an ADR also sets its date (ADR 0027, which supersedes ADR 0012;
  who approved a change is still recorded by the pull request).
- `/sdlc:audit` lists each spec, ADR, plan or spike record with no `date:` or a malformed one.
- The spec and plan reviewers keep the frontmatter's `#` line, as the ADR and spike reviewers do.

### Upgrading

- Documents written before this version have no date, and nothing breaks: they may be edited as
  before, and the next status change adds today's date. To give one its real date now, add a
  `date:` line by hand or with any edit, using the day of its last status change from git; adding
  a date is allowed even to an accepted ADR, a built plan or a finished spike record. `/sdlc:audit`
  lists the documents still without one.

## [0.33.0] - 2026-11-10

### Changed

- No open question is ever left bare. In a brief, ADR, plan or spike record, as already in a spec,
  each open question ends with "Proposed:" and the answer the skill would choose, so you can accept
  it in a word, or, where only you can know, what would settle it. In a brief, a proposal rests
  only on what you said. Each rubric gains a check for it.
- `/sdlc:build` and its reviewer read your practices where `/sdlc:plan` does: the Practices section
  of both `AGENTS.md` and `CLAUDE.md`, and the topic files they name, even when `CLAUDE.md` does not
  import `AGENTS.md`.
- A plan is temporary: once `✅ Built` it is frozen, and you may delete it whenever nobody needs it.
- Every skill whose document has a status signs it off on the same terms, and `/sdlc:spec` now asks
  whether to accept a spec once nothing is left to settle. Every document reviewer reports in the
  same shape, with Suggestions kept apart.
- Plans, like briefs, specs and ADRs, state handed-over material in their own words rather than
  referring to it. The hook that refuses a hyperlink or path to such material now checks plans and
  spike records too, as well as the brief, specs and ADRs (ADR 0026, which supersedes ADR 0023).
- The spike reviewer and plan reviewer read every title their references check needs.
- `/sdlc:adr` says how a draft written in the old layout is brought to the current one.

### Upgrading

- A brief, ADR, plan or spike record whose open questions have no "Proposed:" now fails its review
  the next time it is reviewed. Nothing else changes until then: the skill adds the proposals in
  its next edit.

## [0.32.0] - 2026-11-10

### Changed

- Specs have a new layout. A one-sentence Story, "When <situation>, <who> wants to <do
  something>, so they can <outcome>", replaces Problem and Goal; In scope and Out of scope replace
  Scope. Requirements are numbered headings, as `### 2. Reply to all`; the number is only for
  reading, and plans still name a requirement by its name alone. Each example is a two-column
  table headed `| Example | <name> |` with Given, When, Then and And rows, and How we'll check
  replaces Verified by.
- The spec rubric adds three checks: the first requirement states the outcome the story asks for,
  a spec covers one capability, and every open question proposes an answer. A rule's subject is
  something someone can see, never an internal step.
- `/sdlc:spec` plays the story and scope back for your yes before it drafts requirements, unless
  you asked it to write the spec straight away, and offers to split a story that holds two
  capabilities. It never writes a default it chose as a rule: that goes into Open questions as its
  proposed answer. It asks what happens when each requirement cannot be met, and settles words
  whose meaning is plain from the product without asking.
- The status hook refuses a plan line that gives a requirement's number, and refuses to accept a
  spec with no numbered requirement.

### Upgrading

- A spec written for an earlier version, with Problem, Goal and Scope sections and
  `### Requirement:` headings, breaks nothing while left alone. But a plan naming it cannot be
  signed off as Ready to build, and `/sdlc:build` will not start on such a plan, until the spec is
  reworked: the next edit `/sdlc:spec` makes to it brings it to the new layout and checks, keeping
  what it says and the requirement names, and asks about anything the new checks need. That edit
  returns an accepted spec to Draft, so accept it again, then sign the plan off again. The hook,
  `/sdlc:plan` and `/sdlc:build` each say this plainly, and `/sdlc:audit` lists every spec still
  in the old layout, so you can see the rework before it is in the way. Briefs, ADRs, plans and
  spike records need no change.

## [0.31.0] - 2026-11-10

### Added

- Every lifecycle document says what kind of document it is in a `type:` field, the first in its
  frontmatter: `Brief`, `Spec`, `ADR`, `Plan` or `Spike`. The brief gains frontmatter holding
  only `type: Brief`. Titles no longer name the type, as "Spec:" or "ADR:" in front of them
  would; each document skill says so in the same sentence.
- The status hook refuses an edit that gives a document the wrong `type:` for its folder, a new
  document without one, or that takes an existing one away. `/sdlc:audit` reports a wrong
  `type:`.

### Changed

- Documents written before this version need no change by hand: each gains `type:` on its next
  edit through its skill. A decided document, such as an accepted ADR, a built plan or a
  finished spike record, may keep lacking it for good; adding it is always allowed and counts
  as no other change, so an old accepted ADR can still be superseded.

## [0.30.0] - 2026-11-09

### Changed

- Every skill that writes a document shows it to you the same way when it hands it over: in your
  Claude app's file viewer where there is one, so you can select lines in it to comment on, and
  always by its full path. It never sends you to a code-hosting site, such as GitHub, to read it. In a
  claude.ai project thread, where the viewer shows a copy, a fresh copy follows each change.
  See ADR 0025.
- The plugin's skill check fails a document skill that does not hold this sentence word for word.

## [0.29.0] - 2026-11-09

### Changed

- An ADR that names an earlier ADR links the number to that ADR's file, such as
  `[ADR 0001](0001-example-subject.md)`, so a reader can click through. The ADR rubric fails a
  bare number, and the template shows the linked form. The `supersedes:` and `superseded-by:`
  fields still hold bare numbers.
- The plugin's reference check refuses an ADR edit that adds a link to an ADR file that does not
  exist, matched by its exact name.

### Fixed

- `/sdlc:audit` no longer reports an ADR that links to another ADR as a references problem.

## [0.28.0] - 2026-11-08

### Changed

- ADRs are written to be read by people first, keeping the spirit of MADR. An ADR reads from
  plain to technical: Question, Decision, Background, Options, Consequences, Out of scope, How
  we'll check and Open questions, with the exact mechanism, rules and evidence under Technical
  detail at the foot. The part above Technical detail is at most 500 words; `adr.py words`
  counts it, and the status hook refuses to accept a longer ADR.
- `/sdlc:adr` writes the Question first and leaves Decision as "Not chosen yet; see Open
  questions." until you choose. Once you have, Decision opens with "Chosen:" and names the option
  in full, so it makes sense on its own; the status hook refuses to accept an ADR whose Decision
  does not. Options is a table saying of each option whether it was chosen or rejected, and why.
- A limit, an untested assumption or a decision left for later goes once under Out of scope, not
  under Consequences. An ADR that bundles two decisions is split by the skill rather than asked
  about.
- How we'll check replaces Confirmation. `/sdlc:audit`, `/sdlc:plan` and `/sdlc:build` read How
  we'll check, Decision and Technical detail, and still read Confirmation and Decision Outcome in
  ADRs accepted before this version.

### What you need to change

- ADRs already accepted need nothing: they keep working as they are. A draft ADR in the old
  layout, with Decision Outcome and Confirmation, cannot be accepted until it is re-laid from the
  new template; `/sdlc:adr` can do this for you.

## [0.27.0] - 2026-11-08

### Changed

- Spike records are written to be read by people first. A record now tests a hypothesis, a claim
  the experiment confirms or refutes, rather than answering a question, and reads from plain to
  technical: the hypothesis and the finding at the top, then How we'll know, Out of scope, How the
  test works, Risks and safeguards, Results and Surprises, with the experiment's detail, its code
  and its runs at the foot. The part above Experiment is at most 600 words; `spike.py words`
  counts it, and the status hook refuses to move a longer record forward.
- The Finding opens with Confirmed, Refuted or Not settled and then says what was found in full,
  so it makes sense on its own, never a bare "Yes" or "No". Results lists every run in a table,
  saying which runs count. The status hook refuses a finishing status the Finding does not open
  with.
- The finished statuses are now `💡 Confirmed`, `🚫 Refuted` and `❔ Not settled`, replacing
  `💡 Answered` and `❔ Not answered`. Where it goes is now Next steps.

### What you need to change

- Spike records written before this version use the old sections and statuses, which the hooks,
  the run script and `/sdlc:audit` no longer recognise. Rewrite any you keep in the new layout
  from the template, or delete them once their finding has reached its spec or ADR.

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
## [0.25.0] - 2026-11-05

### Changed

- The brief, specs and ADRs now stand on their own. They refer to outside material only by a
  web link, and never, by hyperlink, path or title, to material handed over in the conversation
  (such as a requirements document, notes or a ticket), to anything outside the repository, or to
  a file under `docs/` that is not a lifecycle document. What matters from such material is
  stated in the document's own words. `/sdlc:brief`, `/sdlc:spec` and `/sdlc:adr` leave such a
  reference out and say why, and their reviewers check for it.
- The brief rubric's "Links back it" check is gone, so the brief reviewer no longer reads the
  documents a brief links to. A brief that links to a file under `docs/` that is not a lifecycle
  document fails its References check: restate what matters from that file in the brief.

### Added

- A hook refuses any edit that adds such a hyperlink or path to a brief, spec or ADR, and names
  each one (ADR 0023). A reference the document already held is not refused again, so older
  documents and decided ADRs can still be edited as the lifecycle allows.

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
