#!/usr/bin/env python3
"""Hand a build's branch over: commit it, mark the plan Built if the reviews passed, and push.

`/build` runs this however the build ends. It:

1. refuses to run without a remote named `origin` whose default branch is known (`origin/HEAD`),
   on that default branch, or with no branch checked out;
2. commits everything not yet committed, with the message given, leaving out the stand-ins for
   the null device that Claude Code's sandbox puts in place on Linux (see uncommitted.py);
3. with --reviews-passed, sets the plan's status from `🟢 Ready to build` to `✅ Built` and its
   `date:`, the day its status last changed, to today's date on this machine, adding the line under
   the status if the plan has none, changing nothing else in the file, and commits that on its own. It writes the file itself, so the
   status hook, which refuses `✅ Built` from Claude, never sees it;
4. pushes the branch to `origin`;
5. writes the build's report file (docs/adrs/0033 and 0034) with scripts/run_report.py, outside the
   repository, even when it refused to start: Claude's own sections, read from stdin under the
   report's `## ` headings, then the four reports build_relay.py kept for this plan in this session
   (code review, security review, build review and correction check, each "No report kept." when
   there is none) and this script's own lines, word for word. Sections it can't use, such as one
   under a heading the report doesn't have, stop it before any step, changing nothing.

It prints what happened, one line per step, then the report file's path and the file as written.

Exit codes: 0 when every step that applied succeeded; 1 when a commit, the push or the report
file failed, or --reviews-passed was given for a plan that is not `🟢 Ready to build` (the plan is then left as it
is, and the rest still runs); 2 when it refused to start or could not use Claude's sections,
changing nothing in the repository.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uncommitted  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
import build_relay  # noqa: E402
import run_report  # noqa: E402

REVIEWS = (("Code review", "code"), ("Security review", "security"), ("Build review", "plan"),
           ("Correction check", "check"))
NO_REPORT = "No report kept."

READY, BUILT = "🟢 Ready to build", "✅ Built"
STATUS_LINE = re.compile(r"^status:[ \t]*(?P<value>[^\n#]*?)[ \t]*$", re.M)
# The key in any case and with a space before its colon, as the status hook reads it.
DATE_LINE = re.compile(r"^date[ \t]*:[ \t]*(?P<value>[^\n#]*?)[ \t]*(?:#[^\n]*)?$", re.M | re.I)


def today():
    """Today's date on this machine, as YYYY-MM-DD: the day the plan becomes Built."""
    return datetime.date.today().isoformat()


def built(text, match):
    """The plan's text with the status in `match` set to Built and its `date:` to today, adding the
    date line under the status line if the frontmatter has none."""
    end = text.find("\n---", 3)
    date = DATE_LINE.search(text, 4, end + 1)
    if date:
        dated = (date.start("value"), date.end("value"), today())
    else:
        line_end = text.index("\n", match.end("value")) + 1
        dated = (line_end, line_end, f"date: {today()}\n")
    for start, stop, value in sorted([(match.start("value"), match.end("value"), BUILT), dated], reverse=True):
        text = text[:start] + value + text[stop:]
    return text


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def current_branch(repo):
    result = git(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else None


def default_branch(repo):
    """The branch `origin/HEAD` names, or None when it is not set."""
    result = git(repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    return result.stdout.strip().split("/", 1)[-1] if result.returncode == 0 and result.stdout.strip() else None


def has_origin(repo):
    return git(repo, "remote", "get-url", "origin").returncode == 0


def frontmatter_status(text):
    """The status line's match inside the frontmatter, or None."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    match = STATUS_LINE.search(text, 4, end + 1)
    return match


def is_ready(value):
    # A plan written before the emoji holds the status by its words alone.
    words = re.sub(r"^[^\x00-\x7f]+ ?", "", value).replace("️", "")
    return words == "Ready to build"


def commit(repo, message, lines):
    # Leave out the stand-ins Claude Code's sandbox puts in place on Linux: git can't add them,
    # and one it can't add stops `git add -A` from adding anything.
    try:
        _, stand_ins = uncommitted.check(repo)
    except uncommitted.NotARepository as error:
        lines.append(f"Commit failed: {error}")
        return False
    added = git(repo, "add", "-A", "--", ":/", *(f":(top,exclude,literal){path}" for path in stand_ins))
    if added.returncode != 0:
        lines.append(f"Commit failed: {(added.stderr or added.stdout).strip()}")
        return False
    if git(repo, "diff", "--cached", "--quiet").returncode == 0:
        return None
    result = git(repo, "commit", "-q", "-m", message)
    if result.returncode != 0:
        lines.append(f"Commit failed: {(result.stderr or result.stdout).strip()}")
        return False
    sha = git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    lines.append(f"Committed {sha}: {message}")
    return True


def hand_over(repo, plan, message, reviews_passed):
    lines = []
    if not has_origin(repo):
        return 2, ["Refused: there is no remote named `origin` to push the branch to. Add one, then "
                   "hand over again. Nothing was changed."]
    default = default_branch(repo)
    if default is None:
        return 2, ["Refused: the default branch of `origin` is not known. Run "
                   "`git remote set-head origin -a`, then hand over again. Nothing was changed."]
    branch = current_branch(repo)
    if branch is None:
        return 2, ["Refused: no branch is checked out, so there is nothing to hand over. Nothing was changed."]
    if branch == default:
        return 2, [f"Refused: `{branch}` is the default branch, and a build never commits there. "
                   "Nothing was changed."]
    plan_path = os.path.join(repo, plan)
    if not os.path.isfile(plan_path):
        return 2, [f"Refused: the plan {plan} does not exist. Nothing was changed."]

    code = 0
    lines.append(f"Branch: {branch}")
    done = commit(repo, message, lines)
    if done is None:
        lines.append("Work: nothing new to commit.")
    elif done is False:
        code = 1

    with open(plan_path, encoding="utf-8") as f:
        text = f.read()
    match = frontmatter_status(text)
    status = match.group("value") if match else "no status"
    if reviews_passed and code == 0:
        if match and is_ready(status):
            with open(plan_path, "w", encoding="utf-8") as f:
                f.write(built(text, match))
            if commit(repo, f"Mark the plan {os.path.basename(plan)} as built", lines):
                lines.append(f"Plan: {plan} is now `{BUILT}`.")
            else:
                code = 1
        else:
            lines.append(f"Plan: {plan} is `{status}`, not `{READY}`, so it was not marked `{BUILT}`.")
            code = 1
    else:
        if reviews_passed:
            reason = "a commit failed"
        elif match and not is_ready(status):
            reason = f"it is not `{READY}`"
        else:
            reason = "the reviews have not all passed"
        lines.append(f"Plan: {plan} stays `{status}`, because {reason}.")

    result = git(repo, "push", "-q", "-u", "origin", branch)
    if result.returncode == 0:
        lines.append(f"Push: pushed {branch} to origin.")
    else:
        lines.append(f"Push: push failed: {(result.stderr or result.stdout).strip()}")
        code = 1
    return code, lines


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        epilog=__doc__.split("\n\n", 1)[1],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plan", required=True, help="the plan's path, relative to the repository")
    parser.add_argument("--message", required=True, help="the commit message for the work not yet committed")
    parser.add_argument("--reviews-passed", action="store_true",
                        help="every review of the build passed, so mark the plan Built")
    parser.add_argument("--repo", default=".", help="the repository (default: the current directory)")
    parser.add_argument("--report", required=True, choices=["-"],
                        help="`-`: read your own sections of the build's report from stdin, as Markdown "
                             "under the report's `## ` headings")
    parser.add_argument("--data", required=True, help='the plugin\'s data folder: "${CLAUDE_PLUGIN_DATA}"')
    parser.add_argument("--session", required=True, help='the session\'s id: "${CLAUDE_SESSION_ID}"')
    args = parser.parse_args(argv)
    repo = os.path.abspath(args.repo)
    try:
        own = run_report.parse("build", sys.stdin.read())
    except run_report.ReportError as error:
        print(f"Refused: your report's sections can't be used: {error}. Nothing was changed; correct "
              "them and hand over again.")
        return 2
    code, lines = hand_over(repo, args.plan, args.message, args.reviews_passed)
    kept = build_relay.kept_reports(args.data, args.session, args.plan, cwd=repo) or {}
    copied = {"What each review found": [(title, kept.get(part) or NO_REPORT) for title, part in REVIEWS],
              "The hand-over script's report": [("Output", "\n".join(lines))]}
    name = os.path.splitext(os.path.basename(args.plan))[0]
    try:
        _, report = run_report.write("build", name, repo, args.data, own, copied, date=today())
    except run_report.ReportError as error:
        report = [f"Report not written: {error}"]
        code = max(code, 1)
    print("\n".join(lines + [""] + report))
    return code


if __name__ == "__main__":
    sys.exit(main())
