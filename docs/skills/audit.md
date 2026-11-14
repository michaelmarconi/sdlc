# `/audit`

`/audit` is the skill for finding drift: places where the code and its documents no longer
agree, and specs or ADRs that contradict the brief. It is not a step in the sequence of [the lifecycle](../../README.md); run it whenever you want
to know, or on a schedule. Read that page first for the documents, skills and agents it mentions.

## What drift is

A spec's status describes the document, never the software (see
[the lifecycle rules](../lifecycle.md#documents)). So once work is merged, nothing claims the
code still does what each spec says, or still follows each accepted ADR (architecture decision
record). Most work is checked when it is built: [`/build`](build.md)'s reviewer checks each build
against the specs its plan names, and against each accepted ADR whose How we'll check section, the
part saying what the decision applies to and how to check it, covers the code being changed.
Drift comes from everything else:

- code changed without `/build`, such as a quick correction or a teammate's change;
- a build that breaks a spec its plan didn't name;
- a document edited by hand or by a shell command, which the plugin's status hook, a check on
  each edit Claude makes to a document, never sees.

Drift is a finding, not a status. `/audit` reports each finding with a suggested correction, such
as changing the code or changing the document, and you choose which to make.

## What it checks

A run has two parts. The first is quicker and costs less.

**The documents, by script.** A script that ships with the plugin checks every lifecycle document
as it stands, with no AI involved, so this part takes seconds whatever the size of the
repository. It always checks every document, whatever window the run was given (see
[How much a run checks](#how-much-a-run-checks)), and Draft documents too:

- every status is one the lifecycle allows, with its emoji;
- every `type:` names the document's kind, as its folder does; a document without one is not a
  problem, since documents written before types gain one only when next edited;
- every spec, ADR, plan and spike record has a `date:`, the day its status last changed, written
  YYYY-MM-DD; one written before dates is listed, so it can be given one by hand;
- no accepted spec or ADR, no `🟢 Ready to build` plan and no `🟢 Ready to run` spike record has
  open questions;
- every open question is laid out as [the lifecycle page](../lifecycle.md#documents) shows; one
  written before that layout is listed, so it can be laid out again;
- no document links to another, or names its path, where
  [the references rule](../lifecycle.md#principles) does not allow it;
- each ADR named in a `supersedes:` field names it back in `superseded-by:`, and the other way
  round;
- no spec still heads its requirements `### Requirement: <name>`, as specs written for an earlier
  version of the plugin did; such a spec breaks nothing while left alone, but no plan naming it
  can be signed off until it is reworked with [`/spec`](spec.md) and accepted again, so the list
  shows how much rework there is before it is in the way;
- each `🟢 Ready to build` plan still names only accepted specs and ADRs, and only requirements
  that still exist, which catches a spec changed by hand after the plan was signed off;
- no two plans that are not `✅ Built` name the same requirement, including plans on other
  branches that git already knows, local or remote; `/audit` fetches nothing;
- `✅ Built` plans, and finished spike records (`💡 Confirmed`, `🚫 Refuted` or `❔ Not settled`), are listed,
  so you can decide whether to delete any; nothing refers to either, so deleting one leaves no
  other document wrong;
- spike records still `📝 Draft` or `🟢 Ready to run` are listed with their date, so a spike
  nobody finished is noticed.

**The code, by judgement.** One agent per `👍 Accepted` spec and per `👍 Accepted` ADR checks the
code against that one document. Draft specs and ADRs are left out, since their intent is not
settled, and so are `❌ Rejected` and `↪️ Superseded` ADRs and the project's recorded practices,
which are rules for how agents work rather than what the product does.

Each agent starts fresh, without your conversation, and reads only its document and the code that
document concerns, so it judges the code as it is, not as anyone meant it to be. All the agents
start at once, and `/audit` gathers their reports when every one has finished. If Claude Code
refuses to start more agents at once (by default it allows 20; the limit is Claude Code's, not
the plugin's), `/audit` starts the refused ones again once the others have reported. Each report
lists only the problems found, and how many requirements agree, so gathering many reports stays
small.

- For a spec, each requirement is reported as **agrees**, **contradicts**, or **not found**. A
  requirement the code contradicts is drift. A requirement not found is not drift: it is listed
  apart, as not built yet: for each spec, how many requirements were not found, and their names.
- For an ADR, the code its How we'll check section covers is checked against the decision, in the
  way each check names. Those checks are what is sometimes called an architecture fitness
  function: an objective check that the code keeps a property the architecture depends
  on.[^fitness] `/build` applies it to the code each build changes; `/audit` applies every one of
  them to the whole code.
- An ADR check that can only be made by running something, such as a test command, is
  listed apart as needing a run, with what to run; it is not reported as drift.
- Agents read the code and its tests; they run nothing. Whether the tests pass is the job of your
  continuous integration, the service that builds and tests every change; running the software
  itself and trying it from outside is [`/verify`](build.md#after-a-build)'s, and yours.

Every finding quotes the requirement or decision and the code that breaks it, with its file and
line, so you can judge it yourself.

**Each drift finding is checked**, as Claude Code's own `/code-review` checks what its
problem-finding agents report.[^codereview] For every document with drift findings, one more
fresh agent tries to disprove them, and says of each whether it is confirmed or rejected, with its
evidence. Only confirmed findings are reported as drift; rejected ones are listed briefly at the
end with the checking agent's reason, so a real finding dropped by mistake is still in front of
you. A document with no findings needs no checking agent, so this costs more only when there is
drift to check.

**The brief, by judgement.** When the project has a brief, one more agent reads it beside the
accepted specs and ADRs the run covers, without the code, and reports any that contradicts the
brief's goals, what it puts out of scope or its constraints, such as a spec for something the brief
says the product will not do. A spec or ADR that only adds detail the brief doesn't mention is
never reported: they always say more than the brief. Each document it names is checked by another
fresh agent, as drift is, and only confirmed contradictions are reported, with quotes of both. The
suggested correction is either side: change the spec or supersede the ADR to fit the brief, or
change the brief if your intent for the product has changed. The brief changes only when you say
so (see [the lifecycle rules](../lifecycle.md#principles)), so this is where a contradiction
appearing after a brief change comes to light. It costs one agent per run, plus one per document
it names.

`/audit` does not report code that no spec covers. Writing specs for an existing codebase happens
as work touches each part, not all at once.

## How much a run checks

The code part can check everything, or only what a window of time changed. The window is always
read on the branch you have checked out.

- `/agentic:audit` checks everything.
- `/agentic:audit last 7 days` checks the commits whose commit date falls in the last 7 days.
- `/agentic:audit since <commit>` checks the commits after that commit, not including it.
- `/agentic:audit <document>` checks one accepted spec or ADR.

A changed file is any file a window's commits added, changed, renamed or deleted, tests and
configuration included. For a window, one agent reads the changes beside the text of every
accepted spec and ADR, and picks the ones the changes could affect; every spec or ADR whose own
text changed in the window is picked too. Only those are checked, against the code and against the
brief, except that a window in which the brief changed checks every accepted spec and ADR against
it. Picking is a judgement and can
miss a document, so a window never replaces an occasional full run.

`/audit` keeps nothing between runs. Git already records what changed, and you, or the schedule,
give the window.

`/audit` stops and says why, without checking anything else, when:

- the window can't be read, the commit doesn't exist, or the history doesn't reach back far
  enough, as in a clone made with only recent history; it never falls back to a full run;
- the document you named doesn't exist or isn't `👍 Accepted`.

If Claude Code doesn't let it run the script, as can happen in a routine whose permissions don't
allow it, the run stops and says so, since without the script it can't tell which documents to
check.

When there is nothing to check, it says so: no lifecycle documents at all, none accepted, or no
changes in the window. The document checks still run in the last two cases.

## Running it on a schedule

A full audit takes longer and costs more as the number of documents grows, so it suits a slow
schedule rather than every change. For example, set up two Claude Code routines, prompts that
Claude Code runs on a schedule in your account:

- weekly: `/agentic:audit last 8 days`, a day longer than the gap between runs, so a late run leaves
  no gap;
- monthly: `/agentic:audit`, everything, to catch what the weekly runs missed.

The routine needs the plugin installed where it runs, as any session does. `/audit` itself adds
nothing to your repository.

## What you get

Findings come in this order, grouped by document within each part: any document the audit
couldn't read, which means the run is not complete, then drift, problems with the
documents, requirements not built yet, ADR checks that need a run, documents to consider
deleting, unfinished spike records, and last, findings the checking agent rejected. Each drift finding and each problem names its suggested correction, and
the skill that makes it:

- **Correct the code**, when the document is right: through [`/plan`](plan.md) and `/build`, or
  directly for a small correction;
- **Return the spec to `📝 Draft`** and change it, through [`/spec`](spec.md), when the code is
  right;
- **Supersede the ADR**, through [`/adr`](adr.md), when the decision no longer holds;
- for a problem with a document, the edit that corrects it.

The full report goes in a Markdown file, and Claude's reply is a few lines: the outcome, any
question for you, and the file's full path. The app shows you the file where it can. The file
holds Claude's sections, such as each finding with its suggested correction, and every agent's
report copied in word for word by the audit's script, so you read each finding exactly as its agent
gave it, quotes included. It is kept in the plugin's own data folder, outside your repository, at
`reports/<repository>/<date>-audit-<scope>.md`, until you delete it. For a routine, the reply is in
the routine's own session.

`/audit` changes nothing in your repository: no file, no status, no commit, just as Spec Kit's analysis step only
offers its corrections and never makes them.[^speckit] It writes no document, so its findings are
checked as described above rather than corrected. To delete a plan or spike record it listed, ask
Claude in the same session. If your project wants more done with the findings, such as filing
each one as an issue, record that in your [practices](practices.md): Claude follows them in the
session once `/audit` has replied.

[^fitness]: Neal Ford, Rebecca Parsons and Patrick Kua, *Building Evolutionary Architectures*,
    [chapter 2, Fitness Functions](https://oreilly.com/library/view/building-evolutionary-architectures/9781491986356/ch02.html).
[^codereview]: Claude Code documentation, [Review locally with /code-review](https://code.claude.com/docs/en/code-review-local).
[^speckit]: Spec Kit, a toolkit from GitHub for writing specs before code with an AI assistant,
    [the analyze command](https://github.com/github/spec-kit/blob/main/templates/commands/analyze.md):
    "STRICTLY READ-ONLY", and the person "must explicitly approve" any correction.
