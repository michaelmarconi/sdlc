---
# Change status only through the agentic plugin's skills, which check each change; a change made by hand is not checked.
type: ADR
status: 📝 Draft
date: 2026-11-14
---

# Copy every script's and agent's report into the report file by a script

## Question

How do the reports that scripts and Claude agents produce during a build[^build] or an audit[^audit]
get into the file holding its final report?

## Decision

Chosen: a script puts each script's and each Claude agent's report into the final report's file word for word: a script's own output
directly, and each agent's report from what hooks[^hook] saved while the agent ran. Claude writes only its own sections, such as the choices it made and what is left
to check. These reports can be long, and the person needs each one exactly as it was given, not Claude's version of it.

## Background

[ADR 0033](0033-end-of-run-report.md) puts the build's and the audit's full report in a file. Much
of that report is other parts' words: the account from the script that commits and pushes the build's branch, the reports of the three reviewers that check the build's code, and the findings of the audit's agents. Today Claude retells
them. [ADR 0011](0011-review-relay-hook.md) found that Claude sometimes rewords a long report it
copies, so reviews reach the agent that checks the corrections made after a review through a hook instead.
[ADR 0020](0020-spike-runs-written-by-script.md) has a script write each run of a throwaway experiment into its written record
for the same reason.

## Options

| Option | Outcome | Why |
| --- | --- | --- |
| Claude copies each report into the file, as the plugin's instructions for that step tell it to | Rejected | A long report could be reworded, and no step would notice |
| A script writes each report: its own output directly, agents' reports from what hooks saved | Chosen | Word for word every time, as for reviews and experiment runs |

## Consequences

- Good: the person reads every finding exactly as its agent or script gave it.
- Good: the build and the audit get their reports into the file the same way.
- Bad: the audit needs a hook to save its agents' reports, as the build already has, which is more code to keep.

## Out of scope

- Where the file goes and how it is shown, which [ADR 0033](0033-end-of-run-report.md) decides.
- What Claude writes in its own sections, which the plugin's instructions for each step already list.

## How we'll check

Applies to: any script or hook that saves an agent's report for the final report, or writes into the final report's file.

1. Test: unit tests check each report reaches the file byte for byte, under its own heading.
2. Test: in a sample build, the script's printed output shows the file holds the output of the script that pushes the branch, the three reviewers' reports and the report of the check on their corrections word for word.
3. Test: in a sample audit, the script's printed output shows the file holds each agent's report word for word.

## Open questions

- None.

## Technical detail

**Build.** The script that commits and pushes the build's branch at the end, the hand-over script, takes the report file's path. After its own steps, it adds its own
output, the three reviewers' reports, and the report of the check that the corrections were made, when corrections were made, each
under its own heading. The reviews come from the records the hook that saves each build review report already keeps in the
plugin's data folder; those records are then kept until the hand-over, not deleted once the
correction check has run.

**Audit.** A hook keeps the report of each audit agent (the agent that picks which documents to audit, the agents that check one document against the code, the agent that checks documents against the brief, and the agents that try to disprove their findings) in the plugin's data folder, keyed by session, as the hooks that save review reports do. A command of
the script the audit runs adds them to the report file, each as a subsection naming the agent and its
document, under the report heading it belongs to.

**Claude's part.** Claude gives the script its own sections, and the script writes them into the file
with the copied reports; Claude never edits the file.

[^build]: A build is the plugin's step that writes the code for one plan, tests first, has it reviewed by separate Claude agents, and hands the branch back.
[^audit]: An audit is the plugin's step that checks whether the code still agrees with the project's settled documents, using separate Claude agents.
[^hook]: A hook is a script Claude Code runs automatically at set moments, here each time a Claude agent finishes, including the agent that checks a build's corrections.
