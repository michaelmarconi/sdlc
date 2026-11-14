#!/usr/bin/env python3
"""Keep the reports of /audit's agents, so `audit.py report` can put them in the audit's report
file word for word (ADR 0034).

Claude Code runs it on PostToolUse for the Agent tool and a subagent's SubagentHandback tool, and
on SubagentStop. It keeps the report of each `audit-picker`, `auditor`, `brief-checker` and
`audit-checker` agent, keyed by the agent's type, the document on its request's `Document:` line
(none for the picker) and, for a checker, which report it was given to check (`AUDIT REPORT` or
`BRIEF REPORT`), since one document can have both. An agent run again under the same key replaces
its earlier report. In a Claude project thread the report is the one the agent handed back. An
agent that runs in the background is kept from the event that says it finished, joined to its
launch by its id, as build_relay.py does (see subagent_report.py). A report that arrives before
its launch is held until the launch is seen; once an agent has handed its report back, a later
stop is left alone.

Records live in $CLAUDE_PLUGIN_DATA/audits/<session>.json and are deleted once unchanged for 30
days (see saved_records.py), or when `audit.py start` or `audit.py report` clears them. Without
$CLAUDE_PLUGIN_DATA nothing is kept. It changes no request, refuses nothing and prints nothing.
"""

import argparse
import contextlib
import json
import os
import re
import sys

try:
    import fcntl
except ImportError:  # Windows: run without the lock rather than fail every agent start.
    fcntl = None

import saved_records
import subagent_report
from build_relay import text_of

AGENTS = ("audit-picker", "auditor", "brief-checker", "audit-checker")
KINDS = ("AUDIT REPORT", "BRIEF REPORT")
HELD = 50  # an audit starts one auditor and one checker per document


def record_path(data, session):
    if not data:
        return None
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", str(session))
    return os.path.join(data, "audits", safe + ".json")


@contextlib.contextmanager
def locked(path):
    """Hold the record's lock: an audit's agents finish side by side.

    Untested, since only a race could show it and no test relies on timing (AGENTS.md rule 5)."""
    if not fcntl:
        yield
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".lock", "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            record = json.load(f)
    except (OSError, TypeError, ValueError):
        record = None
    if not isinstance(record, dict):
        record = {}
    for key in ("reports", "launched", "stopped", "final"):
        if not isinstance(record.get(key), dict):
            record[key] = {}
    return record


def save(path, record):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f)
    saved_records.prune(os.path.dirname(path))


def reports(data, session):
    """The session's kept reports, in the order they were first kept: [{agent, document, kind, text}]."""
    path = record_path(data, session)
    return list(load(path)["reports"].values()) if path else []


def clear(data, session):
    path = record_path(data, session)
    if path and os.path.exists(path):
        os.remove(path)


def agent_type(value):
    name = str(value or "").split(":")[-1]
    return name if name in AGENTS else None


def identity(tool_input):
    """{agent, document, kind} for an audit agent's request, or None for any other agent."""
    agent = agent_type(tool_input.get("subagent_type"))
    if not agent:
        return None
    prompt = tool_input.get("prompt") if isinstance(tool_input.get("prompt"), str) else ""
    first = prompt.strip().splitlines()[0] if prompt.strip() else ""
    document = first[len("Document:"):].strip() if first.startswith("Document:") else ""
    kind = next((k for k in KINDS if f"=== {k} ===" in prompt), "") if agent == "audit-checker" else ""
    return {"agent": agent, "document": document, "kind": kind}


def keep(record, who, text):
    if isinstance(text, str) and text.strip():
        key = "|".join((who["agent"], who["document"], who["kind"]))
        record["reports"].pop(key, None)
        record["reports"][key] = dict(who, text=text)


def finished(record, event):
    agent_id = event.get("agent_id")
    if not isinstance(agent_id, str) or not agent_id:
        return False
    handed = subagent_report.handed_back_report(event) is not None
    if record["final"].get(agent_id) and not handed:
        return False
    text = subagent_report.report(event)
    who = record["launched"].get(agent_id)
    if isinstance(who, dict):
        keep(record, who, text)
    else:
        subagent_report.hold(record["stopped"], agent_id, text, limit=HELD)
    if handed:
        record["final"][agent_id] = True
    return True


def returned(record, tool_input, response):
    who = identity(tool_input)
    if not who:
        return False
    launched = subagent_report.launched_id(response)
    if launched is None:
        record["stopped"].pop(str(subagent_report.agent_id(response)), None)
        keep(record, who, text_of(response))
    else:
        record["launched"][launched] = who
        held = record["stopped"].pop(launched, None)
        keep(record, who, held)
    return True


def handle(event):
    path = record_path(os.environ.get("CLAUDE_PLUGIN_DATA"), event.get("session_id") or "unknown")
    if not path:
        return
    if subagent_report.finished(event):
        if not agent_type(event.get("agent_type")):
            return
        with locked(path):
            record = load(path)
            if finished(record, event):
                save(path, record)
        return
    tool_input = event.get("tool_input")
    if (event.get("hook_event_name") != "PostToolUse" or event.get("tool_name") not in ("Agent", "Task")
            or not isinstance(tool_input, dict) or not identity(tool_input)):
        return
    with locked(path):
        record = load(path)
        if returned(record, tool_input, event.get("tool_response")):
            save(path, record)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        epilog=__doc__.split("\n\n", 1)[1] + "\nReads one hook event as JSON from stdin. Prints "
               "nothing. Always exits 0.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args(argv)
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    try:
        if isinstance(event, dict):
            handle(event)
    except Exception:  # never block a step over a fault in this hook
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
