"""Write the report file a build or an audit ends with (ADRs 0033 and 0034).

`hand_over.py` and `audit.py report` use this module; it has no command of its own. A report is
one Markdown file with one `##` heading per item the skill lists, in that order. Claude's own
sections arrive as Markdown under those headings, and the reports of scripts and agents arrive as
text that goes into the file word for word, as `###` subsections under the heading they belong to.
A heading only a script fills cannot come from Claude, so Claude cannot write its own version of a
copied report.

The file goes in <data>/reports/<repository>/<date>-<kind>-<name>.md, where <data> is the plugin's
data folder. When that folder is empty or can't be written, as in the plugin's own test runs, the
file goes in `agentic-reports-<user id>` in the system's temporary folder instead, which only this
user can open, and the lines printed for Claude say so. A second report of the same name on the
same day gets `-2`, `-3` and so on: no report is ever overwritten, and none is deleted.

The lines printed for Claude give the file's path first, then the headings, each copied report's
length, and the file as written, between fixed `===` lines, so the run's own record shows exactly
what the person will read.
"""

import os
import re
import tempfile

HEADINGS = {
    "build": [
        "What was built",
        "Built before sign-off",
        "Tests and lint",
        "Choices",
        "Defects corrected",
        "What each review found",
        "The hand-over script's report",
        "Left for you to check",
    ],
    "audit": [
        "Documents checked",
        "Documents not checked",
        "Drift",
        "Contradicts the brief",
        "Problems with the documents",
        "Not built yet",
        "ADR checks that need a run",
        "Documents to consider deleting",
        "Unfinished spike records",
        "Rejected findings",
    ],
}
# Headings only a script fills: Claude's text under one is refused.
COPIED_ONLY = {
    "build": {"The hand-over script's report"},
    "audit": set(),
}
NOTHING = "Nothing to report."
HEADING = re.compile(r"^## (?P<title>.+?)[ \t]*$")


class ReportError(Exception):
    """The report can't be written as asked; the message says why."""


def safe(name):
    """`name` with every run of characters not safe in a file name made one hyphen."""
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name)
    name = re.sub(r"\.{2,}", "-", name)
    name = re.sub(r"-{2,}", "-", name).strip("-.")
    return name or "report"


def writable(folder):
    try:
        os.makedirs(folder, exist_ok=True)
        os.rmdir(tempfile.mkdtemp(dir=folder))
        return True
    except OSError:
        return False


def fallback_root():
    """The folder used when the data folder can't be written: only this user can open it, so other
    users can neither read a report nor put anything in its place."""
    return os.path.join(tempfile.gettempdir(), f"agentic-reports-{os.getuid()}")


def private(root):
    try:
        os.makedirs(root, mode=0o700, exist_ok=True)
        info = os.lstat(root)
    except OSError as error:
        raise ReportError(f"neither the plugin's data folder nor {root} can be written ({error})")
    if not os.path.isdir(root) or os.path.islink(root) or info.st_uid != os.getuid() \
            or info.st_mode & 0o077:
        raise ReportError(f"{root} is not a folder only you can open; delete it and run again")
    return root


def report_folder(data, repository):
    """The folder for this repository's reports, and whether it is the fallback."""
    name = safe(os.path.basename(os.path.normpath(repository)))
    if data:
        folder = os.path.join(os.path.abspath(data), "reports", name)
        if writable(folder):
            return folder, False
    folder = os.path.join(private(fallback_root()), name)
    if not writable(folder):
        raise ReportError(f"{folder} can't be written")
    return folder, True


def parse(kind, text):
    """Claude's sections, {heading: text}, from Markdown under `## <heading>` lines.

    Raises ReportError for text before the first heading, a heading the kind doesn't list, a
    heading only a script fills, or a heading given twice."""
    sections, current, lines = {}, None, []

    def close():
        if current is not None:
            sections[current] = "\n".join(lines).strip("\n")

    for line in text.splitlines():
        match = HEADING.match(line)
        if not match:
            if current is None and line.strip():
                raise ReportError(f"text before the first heading: {line.strip()[:60]!r}")
            lines.append(line)
            continue
        close()
        title = match.group("title")
        if title not in HEADINGS[kind]:
            raise ReportError(f"unknown heading {title!r}; the headings are: " + "; ".join(HEADINGS[kind]))
        if title in COPIED_ONLY[kind]:
            raise ReportError(f"{title!r} is filled by the script, not written by you")
        if title in sections:
            raise ReportError(f"heading {title!r} given twice")
        current, lines = title, []
    close()
    return sections


def render(kind, own, copied):
    parts = []
    for heading in HEADINGS[kind]:
        body = []
        if own.get(heading, "").strip():
            body.append(own[heading].strip("\n") + "\n")
        for title, text in copied.get(heading, []):
            body.append(f"### {title}\n\n{text}" + ("" if text.endswith("\n") else "\n"))
        parts.append(f"## {heading}\n\n" + ("\n".join(body) if body else NOTHING + "\n"))
    return "\n".join(parts)


def write(kind, name, repository, data, own, copied, date):
    """Write the report and return (path, the lines to print for Claude).

    `own` is Claude's {heading: text}; `copied` is {heading: [(title, text), ...]}, each text
    written word for word."""
    unknown = [h for h in copied if h not in HEADINGS[kind]]
    if unknown:
        raise ReportError(f"unknown heading {unknown[0]!r}")
    folder, fell_back = report_folder(data, repository)
    base = f"{date}-{kind}-{safe(name)}"
    text = render(kind, own, copied)
    number = 1
    while True:
        path = os.path.join(folder, base + (f"-{number}" if number > 1 else "") + ".md")
        try:
            with open(path, "x", encoding="utf-8") as f:
                f.write(text)
            break
        except FileExistsError:
            number += 1
    lines = [f"Report written: {path}"]
    if fell_back:
        lines.append("The plugin's data folder could not be written, so the report is in a folder only you can open.")
    lines.append("Headings: " + "; ".join(HEADINGS[kind]))
    for heading in HEADINGS[kind]:
        for title, body in copied.get(heading, []):
            lines.append(f"Copied: {title} ({len(body)} characters)")
    lines += ["", "=== THE REPORT AS WRITTEN ===", text.rstrip("\n"), "=== END OF THE REPORT ==="]
    return path, lines
