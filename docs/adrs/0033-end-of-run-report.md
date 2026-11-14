---
# Change status only through the agentic plugin's skills, which check each change; a change made by hand is not checked.
type: ADR
status: 📝 Draft
date: 2026-11-14
---

# Write the build and audit reports to a file in the plugin's data folder, with a short reply

## Question

Where does the full report at the end of a build[^build] or an audit[^audit] go, so the person[^person]
can come back to it later?

## Decision

Chosen: the build and the audit each end in three steps, so the reply is enough to act on and the
repository gains nothing:

- they write their full report to a Markdown file in the plugin's data folder[^data], or, where that
  cannot be written, in a folder only this user can open inside the system's temporary folder, as
  the plugin's experiment step already does;
- they show the file as [ADR 0025](0025-document-review-display.md) shows a document;
- they reply with a short note: the outcome; for a build, its branch and whether the plan's[^plan]
  status was set to `✅ Built`; any question for the person; and the file's full path.

## Background

A build ends by telling the person eight things, such as the tests run and what each review found.
An audit's report is as long. Neither skill says
where the report goes, so it arrives as one long chat reply that is hard to skim, keep or share, and in a
Claude project thread[^thread] it hides the outcome.

## Options

| Option | Outcome | Why |
| --- | --- | --- |
| One long chat reply, as now | Rejected | Hard to skim, keep or share, and hides the outcome in a project thread |
| A file in the person's repository | Rejected | The plugin writes there only the project's planning documents and working rules |
| A file in the temporary folder Claude Code gives each conversation | Rejected | Each app names that folder differently, so no skill can state the path |
| A file in the plugin's data folder, and a short reply | Chosen | One stated place outside the repository, already used by the plugin to save review reports |

## Consequences

- Good: the person reads the outcome in a few lines.
- Good: build and audit end the same way.
- Bad: the folder is deep in the home folder, so the person relies on the viewer or the path.
- Bad: when Claude Code runs on a remote machine, the file is lost when that machine is discarded.

## Out of scope

- How the scripts' and agents' reports get into the file, which [ADR 0034](0034-report-copied-by-script.md) decides.
- Deleting old report files: they are kept until the person deletes them.
- The plugin's other steps, such as writing a decision record, whose hand-over is the document they wrote.

## How we'll check

Applies to: how the build and the audit hand their final report to the person.

1. Test: a sample build ends with a new report file in the plugin's data folder, nothing new in the repository, and a reply under 150 words naming the file's full path.
2. Test: a sample audit does the same.
3. Inspection: both skills state the same folder and naming for the file.

## Open questions

- None.

## Technical detail

**The folder and name.** `${CLAUDE_PLUGIN_DATA}/reports/<repository>/<date>-build-<plan>.md` for a
build and `<date>-audit-<scope>.md` for an audit, where `<repository>` is the repository folder's
name, `<date>` is YYYY-MM-DD, `<plan>` is the plan file's name without `.md`, and `<scope>` is
`all` for every document, the range of commits checked, or the checked document's file name, with
any character not safe in a file name made a hyphen. A second run on the same day adds `-2`, `-3` and so
on rather than overwriting. The plugin's own test runs block the data folder, so there the file goes
in `agentic-reports-<user id>` in the system's temporary folder, made so only that user can open it,
and the reply says so.

**The file.** One heading per item the skill already lists for its report, in that order.

**The reply.** Under 150 words: the outcome; for a build, the branch and whether the plan was marked built; any
question for the person; the file's full path. The file is shown by the sentence
[ADR 0025](0025-document-review-display.md) puts in every document skill: in a Claude project thread
that means attaching a copy, and in the command line, giving the path.

[^build]: A build is the plugin's step that writes the code for one plan, tests first, has it reviewed by separate Claude agents, and hands the branch back.
[^audit]: An audit is the plugin's step that checks whether the code still agrees with the project's accepted specifications and decision records, using separate Claude agents.
[^person]: The person is whoever is working with Claude and the plugin on the project.
[^data]: The plugin's data folder is a folder Claude Code gives each plugin in the person's home folder, outside every repository, and keeps between sessions.
[^plan]: A plan is the plugin's document that sets out one piece of work to build.
[^thread]: A Claude project thread is one conversation inside a project in the Claude app, where each piece of work gets a thread of its own.
