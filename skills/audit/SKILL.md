---
name: audit
description: Find drift, where the code and its lifecycle documents no longer agree. A script checks every spec, ADR, plan and spike record as it stands, and one fresh agent per accepted spec and ADR checks the code against it, one more checks them against the brief, with each drift finding checked again before it is reported with a suggested correction. Covers the whole repository, the commits of a window such as "last 7 days" or "since" a commit, or one named document, and changes nothing. Use whenever someone wants to know whether the code still does what the specs say or follows the ADRs, to check for drift or out-of-date documents, or to run a scheduled audit, even if they don't say "audit". Not for reviewing one change or pull request, for security or dependency checks, or for running tests.
---

# Audit

An audit finds drift: places where the code no longer does what a `👍 Accepted` spec says, or no
longer follows a `👍 Accepted` ADR. It also finds accepted specs and ADRs that contradict the
brief. It reports what it finds and changes nothing in the repository, so the person chooses each
correction. Before you start, read
[references/rubric.md](references/rubric.md) with the Read tool: it is the list of checks the
audit's output must meet.

The audit script does every exact check. Run it with Bash, from the repository's root, or with
`--project <folder>` when the repository is not the folder you are in, such as when the person
names it:

```
python3 "${CLAUDE_SKILL_DIR}/scripts/audit.py" <command> ...
```

- `documents` checks every lifecycle document and lists the accepted specs and ADRs. Run it in
  every audit.
- `window <words>` lists a window's commits and the files they changed, and writes nothing. Run
  it before anything else when the person gives a window.

- `start` clears what the plugin kept of an earlier audit's agents in this session. Run it first
  in every audit, before any agent starts:
  `python3 "${CLAUDE_SKILL_DIR}/scripts/audit.py" start --data "${CLAUDE_PLUGIN_DATA}" --session "${CLAUDE_SESSION_ID}"`.
- `report` writes the report file, as Report says.

`documents` and `window` print JSON. If a command exits with 1, or Claude Code doesn't let it run, as in a routine
whose permissions don't allow it, stop and give the person the reason: without the script you
can't tell which documents to check. Never work its checks out yourself instead.

## What to check

Read what the person asked for:

- nothing more than an audit: every accepted spec and ADR;
- `last N days` or `since <commit>`: a window, read on the checked-out branch;
- a document's path: that one spec or ADR.

For a window, run `window` first. If it refuses, stop with its reason: check nothing, not even
the documents, and never fall back to a full audit. Then run `documents` in every case. For a
named document, if it is not among `documents`' accepted specs and ADRs, stop and say why: it
doesn't exist, or it isn't `👍 Accepted` and so states no settled intent. Report nothing else,
not even problems `documents` found: the person asked about that one document only.

Say so plainly and go straight to the findings when there is nothing for agents to check: when
`lifecycle` is false there are no lifecycle documents at all, and nothing more to report; when
no spec or ADR is accepted, or a window holds no commits, the document checks are still the
findings.

For a window, start the `agentic:audit-picker` agent with this request, filled from `window`'s
output and listing every accepted spec and ADR under `Documents:`, one per line:

```
Repository: <root, as window prints it>
Commits:
<commit> <date> <subject>
...
Changed:
<status> <path>, or R <path> from <old path>
...
Documents:
<path>
...
```

The documents to check are those it picks, and every one `window` lists under
`changed_accepted_documents`, whose own text changed. If that leaves none, say the window's
changes touch no accepted document; when `brief_changed` is true and `documents` names a `brief`,
still check every accepted spec and ADR against it, as below. If the picker reports an `Error:`, stop and give the person
the error: the window was not checked, and a full audit is no substitute for it.

## Check the code

Start one `agentic:auditor` agent per document to check, all in the foreground and all in one
message, so they run side by side. Give each this request, exactly as shown:

```
Document: <the document's path, as documents lists it>
Repository: <root, as documents prints it>
```

Never start one for any other document.

In the same message, when `documents` names a `brief`, start one `agentic:brief-checker` agent,
which checks documents against the brief, not the code. Give it the documents to check: for a full
audit, every accepted spec and ADR; for a window, every one if `window`'s `brief_changed` is true,
since a changed brief can contradict documents nothing else touched, and otherwise the ones being
audited; for a named document, that one. Start none when there is no brief or no document to give
it.

```
Document: <brief, as documents prints it>
Repository: <root, as documents prints it>
Documents:
<path>
...
```

Claude Code limits how many agents run at once; if it refuses some, start those again the same
way once the others have reported, until every agent has a report.

Then, for each report that has no `Error:` line and whose Drift section is not "None.", start one `agentic:audit-checker` agent,
all in one message, with this request. Copy the auditor's report between the markers exactly as
it came, since the person judges each finding by its quotes:

```
Document: <the document's path>
Repository: <root, as documents prints it>
=== AUDIT REPORT ===
<the report>
=== END AUDIT REPORT ===
```

For each document the brief checker names under Contradictions, start one `agentic:audit-checker`
agent in that same message, with its contradictions copied exactly as they came:

```
Document: <the document's path>
Repository: <root, as documents prints it>
=== BRIEF REPORT ===
Brief: <brief, as documents prints it>
<that document's contradictions>
=== END BRIEF REPORT ===
```

A document the brief checker lists under Not read was not checked against the brief, and if the brief
checker reports an `Error:`, no document was.

A report, an auditor's, the brief checker's or a checker's, with an `Error:` line checked nothing: never count it
as no drift, or its findings as rejected. A drift finding is
reported as drift only once its checker confirms it.

## Report

However the audit ends, finished or stopped for a reason above, end with a report file. The plugin
copies every agent's report into it word for word, so the person can read each finding exactly as
its agent gave it; you write only your own sections, as Markdown under these `##` headings, in
this order, leaving out any you have nothing for:

1. `## Documents checked`: for a full audit or a named document, the documents audited. For a
   window, the picker's report is added for you.
2. `## Documents not checked`: each document whose auditor or checker reported an `Error:`, or the
   brief checker could not read, and the brief itself if the brief checker reported an `Error:`, with
   the error, saying the audit is not complete until it is run again where the document can be
   read. If the audit stopped, say why here.
3. `## Drift`: each confirmed finding, named by its document and the auditor's number for it, with
   its suggested correction. The auditors' and checkers' reports, with their quotes, are added
   under it for you, so do not repeat the quotes.
4. `## Contradicts the brief`: each confirmed contradiction, named the same way, with its suggested
   correction. Only the person decides which side moves.
5. `## Problems with the documents`: the edit that corrects each problem; the problems `documents`
   found are added for you.
6. `## Not built yet`: for each spec, how many requirements were not found, and their names.
7. `## ADR checks that need a run`: each, with what to run.
8. `## Documents to consider deleting`: the `✅ Built` plans and finished spike records. Nothing
   refers to either, so deleting one leaves no other document wrong.
9. `## Unfinished spike records`: each `📝 Draft` or `🟢 Ready to run` one, with its date.
10. `## Rejected findings`: each, briefly, with the checker's reason.

Give your sections to the script on standard input, with `--scope` set to `all`, the window's
words, or the named document's path:

```
python3 "${CLAUDE_SKILL_DIR}/scripts/audit.py" report --scope "<scope>" --data "${CLAUDE_PLUGIN_DATA}" --session "${CLAUDE_SESSION_ID}" <<'EOF'
## Drift

...
EOF
```

It prints the file's path first. If it refuses a heading, correct your sections and run it again.
Never write or edit the file yourself.

Name a suggested correction, and the skill that makes it, for each drift finding, each
contradiction and each problem:

- **Correct the code**, when the document is right: through `/plan` and `/build`, or directly for
  a small correction;
- **Return the spec to `📝 Draft`** and change it, through `/spec`, when the code is right;
- **Supersede the ADR**, through `/adr`, when the decision no longer holds;
- for a contradiction with the brief, either one: change the spec through `/spec`, or supersede
  the ADR through `/adr`, to fit the brief; or change the brief through `/brief`, when the
  person's intent for the product has changed;
- for a problem with a document, the edit that corrects it.

End with a reply of a few lines: the outcome, any question for the person and the report file's full path; if the app you run in can show them a file in a viewer, show the report file there; never paste the report into the reply.

Make none of them. The audit writes, edits and deletes nothing in the repository, sets no status
and makes no commit, so the person chooses every correction. If they then ask for one, such as
deleting a plan it listed, that is a new request.

Once you have replied, look in the project's practices, in `AGENTS.md`, `CLAUDE.md` and any files
under `docs/practices/`, for what to do with an audit's findings, such as filing each as an issue
or posting a summary, and do it. That is not a correction: the person asked for it when they
recorded the practice, and it changes nothing in the repository.
