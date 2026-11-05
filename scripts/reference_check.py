#!/usr/bin/env python3
"""Refuse a brief, spec or ADR that refers to material outside the lifecycle's own documents.

Claude Code runs this as a PreToolUse hook on Write, Edit and MultiEdit, from status_check.sh.
It reads the hook's JSON from stdin and, for the project's docs/brief.md, a *.spec.md under its
docs/specs/ or a *.md under its docs/adrs/ (the project being $CLAUDE_PROJECT_DIR, or the
current directory if unset), works out what the file would contain after the edit. It reads every
inline link and image, `[text](target)` or `[text](<target>)`, every reference definition,
`[name]: target`, every autolink, `<scheme:target>`, and every HTML `href` and `src` value,
outside code spans and fenced code blocks, and refuses the edit if it adds a target that is:

- an address with a scheme other than `http`, `https` or `mailto`, such as `file:`;
- an absolute path, or one starting `~`;
- a relative path that leaves the project;
- a relative path to a file under docs/ that is not a lifecycle document: the brief, a spec, an
  ADR, a plan or a spike record.

These documents stand on their own: what matters from material they were drafted from is stated
in their own words, and outside material is referred to only by a web link. Any other target,
such as a path to code, a folder, a `#heading` of the same document or a web link starting `//`,
is not checked. Which lifecycle documents may refer to which is left to the reviewers, as are
references by title, paths written as plain text and reference definitions whose target is on
the next line. A target the
document already held before the edit is not refused again, so a document written before this
check, or a decided ADR that can no longer be edited, can still be edited as the lifecycle allows.
An edit that can't be matched against the file is left to status_check.py, which runs first; a
Write is checked even when the file it replaces can't be read.
"""

import argparse
import json
import os
import re
import sys
from urllib.parse import unquote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import doc_references  # noqa: E402
import status_check  # noqa: E402

WEB = ("http", "https", "mailto")
ANGLE = re.compile(r"!?\[(?:[^\]\\]|\\.)*\]\(\s*<([^>\n]*)>")
AUTOLINK = re.compile(r"<([A-Za-z][A-Za-z0-9+.-]{1,31}:[^<>\s]*)>")
HTML = re.compile(r"""\b(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.IGNORECASE)


def is_brief(path):
    """True for docs/brief.md in the project, whatever the case."""
    return [part.lower() for part in status_check.project_parts(path)] == ["docs", "brief.md"]


def is_lifecycle_document(path):
    return (is_brief(path) or status_check.is_spec(path) or status_check.is_adr(path)
            or status_check.is_plan(path) or status_check.is_spike(path))


def targets(line):
    """Every link target on a line outside code spans: Markdown links, images and reference
    definitions, `<target>` forms of them, autolinks, and HTML `href` and `src` values."""
    bare = doc_references.CODE_SPAN.sub("", line)
    found = [target for target in doc_references.targets(line) if not target.startswith("<")]
    found += [m.group(1) for m in ANGLE.finditer(bare)]
    found += [m.group(1) for m in AUTOLINK.finditer(bare)]
    found += [m.group(1) if m.group(1) is not None else m.group(2) for m in HTML.finditer(bare)]
    return found


def problems(source, text):
    """Each target in the text that may not be referred to, with why, in order of appearance."""
    found = {}
    for _, line in doc_references.prose_lines(text or ""):
        for target in targets(line):
            wrong = problem(source, target)
            if wrong:
                found.setdefault(target, wrong)
    return found


def problem(source, target):
    """Why the target may not be referred to, or None if it may."""
    path = target.strip().partition("#")[0]
    if not path or path.startswith("//"):
        return None
    scheme = doc_references.SCHEME.match(path)
    if scheme:
        if scheme.group(0)[:-1].lower() in WEB:
            return None
        return "is not a web link"
    path = unquote(path)
    if path.startswith(("/", "~", "\\")):
        return "is outside the repository"
    full = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(source)), path))
    parts = status_check.project_parts(full)
    if parts[0] == os.pardir:
        return "is outside the repository"
    if path.endswith("/") or os.path.isdir(full):
        return None
    if parts[0].lower() == "docs" and not is_lifecycle_document(full):
        return "is a file under docs/ that is not a lifecycle document"
    return None


def check(payload):
    """Return the reason to refuse the tool call, or None to allow it."""
    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path", "")
    if not path:
        return None
    if is_brief(path):
        kind = "brief"
    elif status_check.is_spec(path):
        kind = "spec"
    elif status_check.is_adr(path):
        kind = "ADR"
    else:
        return None
    before = None
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                before = f.read()
        except (OSError, UnicodeDecodeError):
            if payload.get("tool_name") != "Write":
                return None
    after = status_check.after_edit(payload.get("tool_name"), tool_input, before)
    if after is None:
        return None
    old = problems(path, before)
    found = [f"- `{target}` {wrong}" for target, wrong in problems(path, after).items()
             if target not in old]
    if not found:
        return None
    return (
        f"{os.path.basename(path)}: the {kind} stands on its own, so it refers to outside material "
        "only by a web link. Material handed over in the conversation, kept outside the repository "
        "or under docs/ beside the lifecycle's documents can change or vanish without the "
        f"{kind} being touched. State what matters from it in the {kind}'s own words, remove "
        "these references and tell the person why:\n" + "\n".join(found)
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Input: the PreToolUse hook JSON on stdin. Output: nothing when allowed; the reason "
            "on stderr when refused. Exit codes: 0 allows the edit (including when the input "
            "cannot be read); 2 refuses it, and Claude Code shows Claude the reason."
        ),
    )
    parser.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    reason = check(payload) if isinstance(payload, dict) else None
    if reason:
        print(reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
