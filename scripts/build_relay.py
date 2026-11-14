#!/usr/bin/env python3
"""Hand the build's correction checker the three review reports and the commit they reviewed.

After its three reviews, /build corrects what they found, once, commits, and starts the
`build-correction-checker` agent. The checker needs the reports word for word, and the commit
the reviews saw, so it can read exactly what the corrections changed. A model copying the reports
could reword them, so this hook keeps them and adds them to the checker's request itself, as
review_relay.py does for documents.

Claude Code runs it on PreToolUse for the Agent tool, on PostToolUse for the Agent tool and a
subagent's SubagentHandback tool, and on SubagentStop. It acts only in a session where /build was allowed to start (recorded by
fresh_session.py), and keeps:

- the report of the agent that runs Claude Code's `/code-review`: an agent whose request's first
  line is `Document: <plan>` and whose second line starts `Run /code-review`;
- the report of the agent that runs `/security-review`: the same, with a second line that starts
  `Run /security-review`;
- the report of the `build-reviewer` agent, whose request's first line is `Document: <plan>`.

In a Claude project thread an agent's report is the one it handed back, not the tool's text,
which there only says where the report went. Each is kept with the commit checked out when it ran,
in the repository holding the plan its `Document:` line names, found as every hook finds one
(docs/adrs/0032, repository.py), so it works when the repositories sit one level below the session
folder, as in a Claude project thread. A report of a later commit, or of a plan in another
repository, starts a new set, so the checker only ever gets reports of one commit.

Before the `build-correction-checker` starts, it appends the three reports, the reviewed commit
and the rubric to read, between fixed `=== ... ===` lines, and approves the start. It refuses the
start, with a reason Claude sees, when the request has no `Document:` line, when any of the three
reports of the reviewed commit is missing, when no git repository holds the plan, or when nothing
has been committed since the reviews, or when the corrections were already checked, so they are
checked only once. Once the checker has run, its report is kept beside the three reviews, with the
plan they were of, and `kept_reports` hands all four to hand_over.py for the build's report file
(docs/adrs/0034). A review agent may run in the background, which Claude Code
can choose even when the skill asks for the foreground: its PostToolUse event then only says it
was launched, with its id, so the hook keeps the report from the event with that id that says
the agent finished: in auto mode its SubagentHandback call's PostToolUse, whose report is final,
and otherwise SubagentStop (see subagent_report.py). It holds a report that arrives first until the launch is seen. Records live in
$CLAUDE_PLUGIN_DATA/builds/<session>.json and are deleted once unchanged for 30 days (see
saved_records.py), not when the session ends, since a resumed session carries on. Anything else,
and any input it cannot read, is left alone.
"""

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys

try:
    import fcntl
except ImportError:  # Windows: run without the lock rather than fail every agent start.
    fcntl = None

import fresh_session
import repository
import saved_records
import subagent_report

ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RUBRIC = os.path.join(ROOT, "skills", "build", "references", "rubric.md")
CHECKER = "build-correction-checker"
# The agent types a review runs as. Both skill reviews run in an agent, never through the Skill
# tool: depending on the Claude Code version, /code-review run by the Skill tool either forks or
# runs inside the session and reports through a tool of its own, so its findings may never reach
# a hook (issue #79). An agent's report reaches it either way.
STOPPING = {"build-reviewer": ("plan",), "general-purpose": ("code", "security"), CHECKER: ("check",)}
PARTS = (("code", "CODE REVIEW REPORT"), ("security", "SECURITY REVIEW REPORT"),
         ("plan", "BUILD REVIEW REPORT"))


def repository_of(prompt, cwd):
    """The repository holding the plan the request's `Document:` line names (docs/adrs/0032)."""
    named, _ = first_lines(prompt)
    return repository.repository_of(named, base=cwd) if named else None


def head(folder):
    if not folder:
        return None
    try:
        result = subprocess.run(["git", "-C", folder, "rev-parse", "HEAD"], capture_output=True, text=True)
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def record_path(session, data=None):
    data = data if data is not None else os.environ.get("CLAUDE_PLUGIN_DATA")
    if not data:
        return None
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session)
    return os.path.join(data, "builds", safe + ".json")


@contextlib.contextmanager
def locked(session):
    """Hold the session's lock: the three reviews start and finish side by side.

    Untested, since only a race could show it and no test relies on timing (AGENTS.md rule 5)."""
    path = record_path(session)
    if not path or not fcntl:
        yield
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".lock", "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def load(session, data=None):
    try:
        with open(record_path(session, data), encoding="utf-8") as f:
            record = json.load(f)
    except (OSError, TypeError, ValueError):
        return None
    return record if isinstance(record, dict) and isinstance(record.get("reports"), dict) else None


def save(session, record):
    path = record_path(session)
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f)
    saved_records.prune(os.path.dirname(path))


def for_commit(session, commit, folder, plan):
    record = load(session)
    if not record or record.get("commit") != commit or record.get("repository", folder) != folder:
        record = {"commit": commit, "repository": folder, "reports": {}, "started": {}}
    record.setdefault("started", {})
    record["plan"] = plan
    return record


def kept_reports(data, session, plan, cwd=None):
    """The reports kept for the session's build of `plan`, {part: text} with parts `code`,
    `security`, `plan` and `check`, for hand_over.py's report file; None when no record is kept or
    it is of another plan."""
    record = load(session, data)
    if not record or not plan or record.get("plan") != repository.full_path(plan, base=cwd):
        return None
    return {part: text for part, text in record["reports"].items() if isinstance(text, str)}


def clear(data, session):
    """Forget the session's build record once hand_over.py has copied its reports, so a later
    build in the same session never shows them as its own."""
    path = record_path(session, data)
    try:
        if path:
            os.remove(path)
    except OSError:
        pass


def first_lines(prompt):
    lines = prompt.strip().splitlines() if isinstance(prompt, str) else []
    named = lines[0][len("Document:"):].strip() if lines and lines[0].startswith("Document:") else None
    return named, (lines[1].strip() if len(lines) > 1 else "")


def part_of(tool_input):
    agent = str(tool_input.get("subagent_type") or "general-purpose").split(":")[-1]
    named, second = first_lines(tool_input.get("prompt"))
    if not named:
        return None
    if agent == "build-reviewer":
        return "plan"
    if agent == "general-purpose" and second.startswith("Run /security-review"):
        return "security"
    if agent == "general-purpose" and second.startswith("Run /code-review"):
        return "code"
    return None


def text_of(response):
    """The agent's report; one handed back in a Claude project thread, as review_relay.py."""
    if isinstance(response, dict):
        if "handback" in response or "handbackReport" in response:
            report = response.get("handbackReport")
            text = report.get("text") if isinstance(report, dict) else None
            return text if isinstance(text, str) else ""
        if isinstance(response.get("result"), str):
            return response["result"]
        blocks = response.get("content") or []
        return "".join(b.get("text") or "" for b in blocks if isinstance(b, dict))
    return response if isinstance(response, str) else ""


def refuse(reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def start_checker(session, tool_input, cwd, call="check"):
    prompt = tool_input.get("prompt") or ""
    named, _ = first_lines(prompt)
    if not named:
        return refuse("Start the build correction checker with `Document: <plan path>` as the "
                      "first line of its request, the same line the build reviewer was given.")
    record = load(session)
    if record and record.get("checked"):
        return refuse("The corrections have already been checked once, which is all a build gets. "
                      "Do not review or check again: stop and show the person the check's report.")
    missing = [title.lower().replace(" report", "") for part, title in PARTS
               if not record or part not in record["reports"]]
    if missing:
        return refuse(f"No {' or '.join(missing)} report of the reviewed commit is on record in this "
                      "session, so the corrections cannot be checked. Do not review again: stop "
                      "and show the person the reports you have and this reason.")
    # A record saved before the repository was kept beside the commit names none: the checker's
    # own `Document:` line names the same plan.
    folder = record.get("repository") or repository_of(prompt, cwd)
    current = head(folder)
    if record["commit"] is None or current is None:
        return refuse(f"There is no git repository holding {named}, so the commit the reviews saw "
                      "could not be recorded and the corrections cannot be checked. Do not review "
                      "again: stop and show the person this reason.")
    if current == record["commit"]:
        return refuse("Nothing has been committed since the reviews. Commit the corrections "
                      "first, then start the build correction checker.")
    try:
        with locked(session):
            fresh = load(session) or record
            runs(fresh, "started")[call] = "check"
            save(session, fresh)
    except OSError:  # the checker still gets the reports; only its own report goes unkept
        pass
    blocks = [f"=== {title} ===\n{record['reports'][part]}\n=== END {title} ==="
              for part, title in PARTS]
    extra = (f"\n\n=== REVIEWED COMMIT ===\nReviewed commit: {record['commit']}\n"
             "=== END REVIEWED COMMIT ===\n\n" + "\n\n".join(blocks) +
             f"\n\n=== FILES TO READ ===\nRubric: {RUBRIC}\n=== END FILES TO READ ===\n")
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                                   "updatedInput": dict(tool_input, prompt=prompt + extra)}}


def runs(record, key):
    """The record's background runs: `launched` maps an agent's id to its call, and `stopped`
    holds the report of an agent that finished before its launch was seen."""
    if not isinstance(record.get(key), dict):
        record[key] = {}
    return record[key]


def keep(record, call, part, report):
    if record["started"].get(call) == part and report.strip():
        record["reports"][part] = report


def agent_stopped(session, event):
    """A background review agent finished, by handing its report back or by stopping: keep its
    report, or hold it until its launch is seen while a review of its kind has no report yet. The
    launch's note is kept, so if the agent stops again, as when another hook kept it going, its
    last report is the one kept. A hand-back ends the agent's run, so once its report is in, a later
    stop, whose last message is then at most a line written beside the hand-back, is left alone."""
    agent_id = event.get("agent_id")
    parts = STOPPING.get(str(event.get("agent_type") or "").split(":")[-1])
    if (not isinstance(agent_id, str) or not agent_id or not parts
            or not fresh_session.building(session) or not record_path(session)):
        return None
    handed = subagent_report.handed_back_report(event) is not None
    with locked(session):
        record = load(session)
        if not record or not isinstance(record.get("started"), dict):
            return None
        launched, stopped = runs(record, "launched"), runs(record, "stopped")
        final = runs(record, "handed_back")
        if final.get(agent_id) and not handed:
            return None
        call = launched.get(agent_id)
        if isinstance(call, str):
            keep(record, call, record["started"].get(call), subagent_report.report(event))
        elif any(p in record["started"].values() and p not in record["reports"] for p in parts):
            # More room than review_relay.py holds: /code-review starts a dozen agents of its own,
            # all general-purpose, whose stops must not push out a review's held report.
            subagent_report.hold(stopped, agent_id, subagent_report.report(event), limit=50)
        else:
            return None
        if handed:
            final[agent_id] = True
        # Marks matter only while the agent's launch or held report is on record.
        for old in [k for k in final if k not in launched and k not in stopped]:
            del final[old]
        save(session, record)
    return None


def returned(record, call, part, response):
    """Keep the report an agent's tool result carries, or note its background launch."""
    agent_id = subagent_report.launched_id(response)
    if agent_id is None:
        report = text_of(response)
        runs(record, "stopped").pop(str(subagent_report.agent_id(response)), None)
    else:
        launched, stopped = runs(record, "launched"), runs(record, "stopped")
        report = stopped.pop(agent_id, None)
        launched[agent_id] = call  # so a later report of the agent is kept too
        if not isinstance(report, str):
            report = ""
    keep(record, call, part, report)


def handle(event):
    session = str(event.get("session_id") or "unknown")
    when = event.get("hook_event_name")
    if subagent_report.finished(event):
        return agent_stopped(session, event)
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    tool = event.get("tool_name")
    checker = str(tool_input.get("subagent_type") or "").split(":")[-1] == CHECKER
    if tool in ("Agent", "Task") and checker:
        if when == "PreToolUse":
            return start_checker(session, tool_input, event.get("cwd"), str(event.get("tool_use_id") or "check"))
        if when == "PostToolUse":
            # One correction check per review: a second would follow a second round of corrections.
            # The record stays, with the check's report, for the hand-over's report file.
            with locked(session):
                record = load(session)
                if record:
                    record["checked"] = True
                    returned(record, str(event.get("tool_use_id") or "check"), "check",
                             event.get("tool_response"))
                    save(session, record)
        return None
    if not fresh_session.building(session) or not record_path(session):
        return None
    if tool not in ("Agent", "Task"):
        return None
    part = part_of(tool_input)
    if not part:
        return None
    call = str(event.get("tool_use_id") or part)
    with locked(session):
        if when == "PreToolUse":
            folder = repository_of(tool_input.get("prompt"), event.get("cwd"))
            commit = head(folder)
            kept = load(session)
            if commit is None and kept and kept.get("commit"):
                # A review whose plan no repository holds must not wipe the others' reports.
                folder, commit = kept.get("repository", folder), kept["commit"]
            named, _ = first_lines(tool_input.get("prompt"))
            record = for_commit(session, commit, folder, repository.full_path(named, base=event.get("cwd")))
            record["started"][call] = part
            save(session, record)
        elif when == "PostToolUse":
            record = load(session)
            if not record or not isinstance(record.get("started"), dict):
                return None
            returned(record, call, part, event.get("tool_response"))
            save(session, record)
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        epilog=__doc__.split("\n\n", 1)[1] + "\nReads one hook event as JSON from stdin. Prints a "
               "PreToolUse decision as JSON, or nothing. Always exits 0.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args(argv)
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    try:
        out = handle(event) if isinstance(event, dict) else None
    except Exception:  # never block a step over a fault in this hook
        out = None
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
