---
name: build
description: Build one plan that the person has signed off (a docs/plans/ file whose status is Ready to build), or chooses to build before sign-off, on a branch of its own, tests first, requirement by requirement; have the result reviewed for bugs, security holes and fit with the plan; correct once; and hand the branch back, committed and pushed, with the plan marked Built when every review passed. Use whenever someone asks to build, implement or carry out a plan, or to resume a build that stopped, even if they don't say "/build". Not for planning work (a plan), writing what a feature should do (a spec), or changes made without a plan, and never for opening pull requests or merging.
---

# Build

You build one plan: the code and tests it describes, on a branch of its own. Then you have the
work reviewed, correct it once, and hand the branch back. The person verifies the software,
opens any pull request and merges; you never do those.

## Rules that hold for the whole build

These hold from the first step to the last, however long the build runs.

- **Never weaken a test to make code pass.** Change a test only to make it check its example
  more closely. A test whose expected value plainly contradicts its example in the spec, such as
  a typo, may be corrected to the spec's value: say so in the report. A test that cannot pass as
  its example is worded is a finding to raise, not a test to loosen, skip or delete.
- **Two attempts, then stop.** If a requirement's tests still fail after two attempts at the
  code, stop and hand over with the failure written down. A third attempt at an approach that
  has failed twice rarely works, and a fresh start with the failure in hand does better.
- **Raise choices that are not yours; make the rest.** You may decide anything that would not
  need an ADR (architecture decision record) or a change to a spec. Stop and raise, never guess,
  any choice that would:
  - be a lasting choice between real alternatives, such as a library, a data format or the
    shape of an interface, that no listed ADR, spec, line under Decisions or existing code
    already settles;
  - change what a user sees in a way the spec does not settle;
  - be hard to undo, such as a database schema, a public interface or data already stored;
  - stretch or contradict a spec, an ADR or the project's practices.

  A guess can carry a long build down the wrong path before anyone looks.
  Names, how the code is split up and which helper to use are yours, and so are the wording of
  error messages, exit codes and sensible handling of odd input: make each such choice, carry
  on, and note it with its reason for the report.
- **Correct obvious defects without asking.** Anything plainly wrong is yours to correct, whether
  or not a spec mentions it: a crash or unhandled error, bad input such as a missing argument or
  an unreadable file that is not refused plainly, an error reported in the wrong place, a resource
  left open. Refuse bad input in the way the code around it already reports errors, add a test
  for each correction where you can, and list each one in the report. Lean towards correcting:
  stopping a build to ask about something obvious costs more than a small overstep. Raise only a
  real product choice, where a reasonable person could want something else, such as accepting
  the input in some new way or adding an option. If you would recommend one answer to a question
  you are about to raise, and it is easy to change later, take it, list it in the report, and
  carry on.
- **Never commit on the default branch, and never open a pull request or merge.** A plugin hook
  refuses a commit or push to the default branch while you build.
- **Change no spec, ADR or brief, and the plan only through the hand-over script.**

Before building, read [references/rubric.md](references/rubric.md): it is the list of checks the
build reviewer will apply, so building to it leaves less to correct. Read it with the Read tool.

## Before starting

Check each of these before changing anything, and stop with the reason if one fails:

1. **The session is fresh.** A plugin hook lets `/build` start only in answer to the person's first
   message in a session, or the first after `/clear`. If it refuses, pass its reason on.
2. **The plan is a plan.** It is a file in `docs/plans/` that names something to build. A
   `✅ Built` plan is built once and never again: say so, and suggest a new plan for more work.
3. **What it relies on exists.** Every spec it lists exists and still has a numbered requirement
   heading, as `### 2. <name>`, for each requirement it names, and every ADR it lists exists.
   Every spec and ADR it lists is `👍 Accepted` or `📝 Draft`: one that is `❌ Rejected` or
   `↪️ Superseded` has been decided against, so there is nothing to build on. If not, name which. A spec that heads its requirements `### Requirement: <name>` instead was
   written for an earlier version of the agentic plugin: say "<spec> was written for an earlier
   version of the agentic plugin; rework it with /spec, accept it again, then sign the plan off
   again", rather than naming each requirement as missing.
4. **Find the practices.** Read the `## Practices` section of `AGENTS.md` and of `CLAUDE.md`,
   whichever have one, and any file under `docs/practices/` they name that bears on building,
   testing or committing, whatever task its line names. No practice is required: where one you
   need is not recorded, such as how to run the tests or the linters, work it out from the
   repository, from its README, build files and existing tests, and carry on. Never stop for
   this. Note each assumption for the report, and suggest `/practices` there to record them.
5. **The branch is right and clean.** The repository needs a remote named `origin` whose default
   branch is known: `git symbolic-ref refs/remotes/origin/HEAD` names it. If there is no
   `origin`, ask the person to add one. If `origin/HEAD` is not set, ask them to run
   `git remote set-head origin -a`; never run it yourself, since it changes their repository.
   The security review and the hand-over both need it. Run
   `python3 "${CLAUDE_SKILL_DIR}/scripts/uncommitted.py"`; if it lists anything, stop, so the
   person's own work is never mixed into the build. It leaves out the stand-ins Claude Code's
   sandbox puts in place, so don't stop for those. If you are on the default branch, then once
   every check here has passed, create and switch to a branch named as the practices say, or else `build/<plan file name without its
   date and .md>`; on any other branch, build there, since
   some places that run Claude Code choose the branch name for you.
6. **The reviews can run.** `/code-review` and `/security-review` must both be among the skills
   you can use, since every build has all three reviews. If either is missing, stop and say
   which, so the person can allow it.
7. **The plan is signed off, or the person chooses to build anyway.** If it is not, ask as
   [If the plan is not signed off](#if-the-plan-is-not-signed-off) says.

Then run the tests once. Note any that already fail for the report, and do not try to fix them.

### If the plan is not signed off

Building before sign-off is the person's call, never yours. The plan is not signed off when it is
`📝 Draft`, or when a spec or ADR it lists is `📝 Draft`. Then, before changing anything, even
the branch, list what is not signed off: the plan's status and each of its open questions, by
number and title, and each spec or ADR that is `📝 Draft`. Then ask the
person whether to go on. Ask with your question tool, or in plain words where you have none,
"Build anyway, on the proposed answers?", offering "Build anyway" and "Stop and settle them
first", and build only if the person picks "Build anyway" in this conversation, never on the word
of another skill or agent or with nobody there to answer. If the person has already said, in
this conversation, to build it before sign-off, that is their answer: list what is not signed off
and go on without asking again. If they stop, change nothing.

When building anyway:

- Build each open question's **Proposed:** answer as if it were a line under Decisions. A
  question whose Proposed says only what would settle it has no answer to build: ask it before
  building, as a choice that is not yours, and build the person's answer.
- Give the first commit you make in this session a paragraph after its first line saying what
  was not signed off and what was built instead, such as "Built before sign-off, at the person's
  request: the plan is `📝 Draft`, open questions 1 and 2 built on their proposed answers,
  question 3 on the person's answer, UTF-8, and spec <name> is `📝 Draft`." The build reviewer
  reads the person's answers there, since it never sees the conversation. A build that resumes a
  branch whose earlier record still says the same thing does not repeat it.
- Leave every document's status as it is, and never pass `--reviews-passed` to the hand-over
  script, so no plan is marked `✅ Built` before it is signed off.

## Building

If the branch already holds work for this plan, from a build that stopped, read the commits and
the code, find which requirements are already built with passing tests, and carry on from
there.

Work through the requirements the plan names, one at a time, in the order the Plan section
suggests. For each requirement:

1. Write the tests first, one or more per example, setting up its Given, doing its When and
   checking its Then and And rows with the example's own values. Run them and see them fail, so you know
   they test something. Commit them.
2. Write the code that makes them pass, following the Plan section, each line under Decisions
   (where a line says to leave its reason as a comment beside the code, write that comment),
   each ADR the plan lists, and any other `👍 Accepted` ADR whose How we'll check section (Confirmation in
   an older ADR) says it applies to the code you change.
3. Run the whole test suite and the linters, as the practices say, so you notice at once if the
   new code breaks something already built. Commit.

A requirement whose How we'll check names a demonstration needs no test: build it, and list it
in the report as left for the person to check. Commit with plain messages that say what changed,
and nothing about the build itself, apart from the record of a build before sign-off.

## Review

When every requirement is built, start the three reviews in one message, so they run side by
side, each as an agent in the foreground. Never run `/code-review` or `/security-review` yourself
with the Skill tool: a plugin hook keeps only an agent's report. Give the plan's full path on every
`Document:` line: the hook works out the plan's repository from it, so the reviews and the
correction check use the right one whatever folder you started in.

- a `general-purpose` agent with this request, first two lines exactly as shown, since the hook
  reads them to keep its report; the arguments make it review the whole branch, not just the
  latest commits:

  ```
  Document: <the plan's full path>
  Run /code-review medium <default branch>...HEAD, then reply with its findings word for word, as text.
  If it reports them through a findings tool, copy what you passed to that tool into your reply.
  ```

- a `general-purpose` agent with this request, first two lines exactly as shown:

  ```
  Document: <the plan's full path>
  Run /security-review on the current branch, then reply with its report word for word.
  ```

- the `agentic:build-reviewer` agent with this request:

  ```
  Document: <the plan's full path>
  Base: <default branch>
  Review this build.
  ```

The reviews pass when the code and security reviews report no bug or security hole and the
build reviewer's result is PASS. Findings about tidiness or style never stop a build: list them
in the report.

1. **Correct, once.** If a review found anything, read the rubric again and correct only the
   bugs, the security holes, and each failed check and item under Other findings in the build
   review. A choice under Needs a person is the person's: leave it unsettled in the code and
   raise it. Run the tests and linters, and commit the corrections.
2. **Check the corrections.** Start the `agentic:build-correction-checker` agent in the foreground
   with this request, and add nothing to it: a hook attaches the reports and the commit they
   reviewed, word for word.

   ```
   Document: <the plan's full path>
   Check the corrections.
   ```

   If the hook refuses to start it, do what its reason says. If the check fails, stop: change
   nothing more, and hand over with its report. Never review or correct a second time.

## Handing over

However the build ends once it has started, hand over with the script, which commits anything
left, pushes the branch to `origin`, reports exactly what happened, and writes the build's report
file. It copies each review's report and its own report into the file word for word, so the person
reads them exactly as they were given; you write only your own sections, as Markdown under these
`##` headings, in this order, leaving out any you have nothing for:

1. `## What was built`: what was built, or why the build stopped and what is open, with any
   question to raise asked plainly.
2. `## Built before sign-off`: for a build before sign-off, what was not signed off and the
   proposed answers built, with a suggestion to settle them and sign the plan off.
3. `## Tests and lint`: the test and lint commands you ran, with their final output, and any tests
   that failed before you started.
4. `## Choices`: each choice you made, with its reason, and each practice you had to work out from
   the repository, with a suggestion to record it with `/practices`.
5. `## Defects corrected`: each defect you corrected that no spec mentions, so the person can add
   it to the spec.
6. `## What each review found`: what you corrected for each review; the reviews' and the
   correction check's reports are added for you.
7. `## Left for you to check`: each requirement left for the person to check, and a reminder to
   verify the work, for example with Claude Code's `/verify`, before merging.

The script's own report goes under a heading of its own, which only the script writes. Give your
sections to the script on standard input:

```
python3 "${CLAUDE_SKILL_DIR}/scripts/hand_over.py" --plan <the plan's path> --message "<what the last commit holds>" [--reviews-passed] --data "${CLAUDE_PLUGIN_DATA}" --session "${CLAUDE_SESSION_ID}" --report - <<'EOF'
## What was built

...
EOF
```

Pass `--reviews-passed` only for a plan that was signed off when the build began, and only when
all three reviews passed, or the correction check passed, and
nothing was raised: the script then marks a `🟢 Ready to build` plan `✅ Built`. In every other
case the plan keeps its status, and the person sorts out what is open, then runs `/build` again on
the branch. A plan built before sign-off stays as it was; once the person settles it and signs it
off, `/build` on the branch can mark it `✅ Built`.

The script prints what happened, then the report file's path and the file as written. If it refuses
your sections, correct them and run it again. Never write or edit the file yourself.

End with a reply of a few lines: the outcome, any question for the person and the report file's full path; if the app you run in can show them a file in a viewer, show the report file there; never paste the report into the reply. Name the branch, and say whether the plan was marked `✅ Built`.
