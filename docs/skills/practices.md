# `/practices`

`/practices` is the skill for recording how your project does things, so that a coding agent
building it works the way your team does: the commands it uses to check its work, the rules it
follows, and where to find more detail. It is part of [the SDLC](../../README.md) but not one of
its steps: you run it whenever you need it. Read that page first for the documents, skills and
agents it mentions.

## What practices are

Practices are the facts and habits an agent needs to work on the project without asking: how to
set it up, run it and test it, how branches and commits are named, what must pass before work is
merged, how it is released. They are the same for every piece of work, so they are written down
once rather than in each plan. They are grouped by topic, such as testing, security or releasing.

Practices are written for coding agents, such as Claude. Your README, contributing guide and other
documents for people stay yours.

A choice between real alternatives, such as which language, test framework or library to use, is
not a practice: it is a technical decision, so it belongs in an [ADR](adr.md) (architecture
decision record), where its reasons are kept and only you accept it. The practice then just says
how to use what was chosen, such as the command that runs the tests.

Because the agents doing the work follow them, the topics leave out ways of working that exist
for people rather than agents, such as sprint length, estimates or pair programming. What
carries over is how work is split and how big each piece may be: small pieces that each leave the
product usable, sized by what a person can review, since reviewing an agent's work is now the
slow step.[^batches]

Like the brief, practices have no status. They are never built; they are corrected in place
whenever the way you work changes, and git keeps the earlier versions.

## Where they live

Practices are kept in two layers, so an agent always has the essentials but reads the detail only
when its task needs it. Coding tools such as Claude Code, Cursor, GitHub Copilot and Kiro split
their instructions the same way.[^tools]

- **The core**: a `## Practices` section in `AGENTS.md`, a format that many coding tools
  read,[^agentsmd] so your practices serve whichever tool your team uses. Claude Code loads its
  project instructions at the start of every session, so every skill and agent sees the core,
  `/plan` and `/build` included. It reads `AGENTS.md` directly only when there is no `CLAUDE.md`,
  only from version 2.1.277 and not in every kind of session, and a personal `CLAUDE.local.md`
  makes it skip `AGENTS.md`. A `CLAUDE.md` holding the line `@AGENTS.md` imports it in every case,
  as Anthropic suggests for sharing one file between tools,[^memory] so `/practices` makes sure that
  line is there. The core is at most 50 lines. That is
  this plugin's own budget: Claude reads the whole file on every task, and Anthropic advises
  keeping it under 200 lines, since a longer file makes Claude follow it less reliably,[^memory] so
  the core leaves most of that room for whatever else the file holds. It has three parts:
  - **Check your work**: the exact commands for setting up, running the product, running every
    test, running one test file, and running the linters and type checker. When a project has
    tests or linters, Anthropic calls the command that runs them "the single most useful line" in
    these instructions.[^check]
  - **Rules**: short lines the agent must follow, such as "write a failing test before the code
    it tests", "open a pull request for every change" or "never edit the files under
    `src/generated/`".
  - **Files to read before a task**: one line for each topic file below, saying which task calls
    for it, such as "before writing or changing tests: `docs/practices/testing.md`". Claude reads
    a file that is only named when it decides it needs it, so each line says when that is.[^memory]
- **Topic files**: `docs/practices/<topic>.md`, one for each topic with more to say than a line or
  two in the core, such as testing, database changes or releasing. Each is at most 200 lines,
  again this plugin's own budget, the same as Anthropic advises for the whole instructions file.
  A topic file names no further files the agent must read, so it reads at most one topic file for
  a task.

The core and the topic files never import other files. An import loads the whole file into every
session, and a file you don't control, such as the README, can grow without limit.

An example of the core, for a recipe-sharing website built in Python. Any other language works the
same way; only the commands change.

```markdown
## Practices

### Check your work
- Set up: `uv sync`
- Run the website: `uv run fastapi dev src/recipes/main.py`
- All tests: `uv run pytest`
- One test file: `uv run pytest tests/test_recipes.py`
- Lint and format: `uv run ruff check --fix . && uv run ruff format .`
- Type check: `uv run mypy src`

### Rules
- Write a failing test before the code it tests.
- Run the tests, linter and type checker before every commit.
- Never commit to the default branch; work on a branch named `<type>/<short-description>`.
- Open a pull request for every change; a person merges it.
- Never edit files under `src/generated/`; run `uv run make-schema` instead.

### Files to read before a task
- before writing or changing tests: `docs/practices/testing.md`
- before releasing or deploying: `docs/practices/releasing.md`
```

## Using `/practices`

You don't set all your practices up front. You add them one topic at a time, whenever you need
them, and improve them as the project grows: how your team works from the start, testing in more
depth once there is more to test, deployment when there is somewhere to deploy to. A practice can
be recorded before the code it describes exists, such as the test command your test framework
will use.

### How a run goes

- **On its own, `/practices` gives an overview and suggests where to start.** It lists the topics,
  each as recorded, not recorded yet, or different from what the repository shows, such as "tests
  exist, but no test command is recorded". When the practices and the repository disagree, it
  says so and asks you which is right. It then suggests the one topic that matters most now,
  judged from the repository and the plans waiting to be built, and offers to start on it. Say
  yes, pick another or stop there. A topic nothing yet needs, such as deployment before there is
  anything to deploy, is not suggested.
- **`/practices <topic>` goes straight to one topic**, such as `/practices testing`. It covers that
  topic alone and stops, so a run is a short conversation. Run it on the same topic later to
  improve it: it starts from what is recorded and proposes changes.
- **Its topics are suggestions, not a complete list.** The plugin offers common topics, such as
  testing, how work is delivered, continuous integration, security and releasing, each with the questions to ask and
  the choices most teams make. Any other topic works the same way: ask for one, such as "I want
  to define how decisions are approved", and `/practices` gives it a topic file and a line in the
  core. It says so as it
  goes: the overview ends by inviting a topic of your own, and within a topic it asks whether
  there is anything else you want recorded.
- **Reads the repository first.** Much of it is already there: build files, test setup,
  continuous integration settings, your README. `/practices` reads them and proposes what it
  finds, so you confirm rather than dictate. Anything it cannot find, or is not sure of, it asks.
- **One question at a time, each with a proposal.** It tells you how many questions it has, then
  asks them one at a time. Each question starts with a short summary of what it is about and what
  the repository shows, so you can answer without knowing the repository, and ends with a
  proposal you can accept, change or reject. Anything you already said, such as answers given
  with the request, is used rather than asked again.
- **Bases its proposals on current advice.** The answers are yours, but when you have no view on a
  question, it asks whether to look up current advice on the web for your language and tools,
  rather than rely on what Claude already knows, which may be out of date. It then proposes a
  default, names the sources it used, and marks the default as one in the practices, by ending
  it with "(default)". If you
  decline, or the session cannot reach the web, it says its proposal comes from Claude's own
  knowledge.

### What it never does

- **Require anything.** Running `/practices` is optional, and so is every topic. A question you
  don't answer is left out, never written as a guess, so it shows as not recorded in the overview.
- **Make a technical choice.** When a question turns out to be a choice between alternatives, it
  says so and leaves it for you to record with `/adr`, as `/plan` does. A command for a tool the
  project does not use yet is marked by ending it with "(not set up yet)".
- **Change anything else.** It writes only the core and the files under `docs/practices/`, and
  leaves the rest of `AGENTS.md` alone, creating the file if the project has none. In `CLAUDE.md`
  it adds only the `@AGENTS.md` line, creating the file if needed, and asks you first when the file
  already exists. It never touches your README, contributing guide or any other file unless you
  explicitly ask it to.
- **Commit.** You look at the change and commit it.

`/build` follows your practices but never changes them. Where a practice is not recorded, it works
it out from the repository and says what it assumed (see [`/build`](build.md)).
[`/plan`](plan.md) keeps each plan to any size or way of splitting work they record.

## Review

Before you see the changes, `/practices` has its reviewer agent check them against a short list of
pass-or-fail checks, such as: each command matches what the repository holds, no secret is
written down, and no choice between alternatives is made there instead of in an ADR. The core and
any topic file a run changed are reviewed together, since they must agree. A hook, a script Claude
Code runs before every edit, refuses an edit that would take a file past the 50-line or 200-line
limit and make it longer, or add an import, so those never reach the review. Beside the reviewer,
the language checker, an agent shared by every skill that writes a document, reads the changes
for words a newcomer could not follow, by the [Plain words](../lifecycle.md#plain-words) rule.
Both are corrected once, as for
every document (see [Review process](../lifecycle.md#review-process)).

[^tools]: [Claude Code](https://code.claude.com/docs/en/memory), [Cursor](https://docs.cursor.com/context/rules),
    [GitHub Copilot](https://docs.github.com/en/copilot/tutorials/customize-code-review) and
    [Kiro](https://kiro.dev/docs/steering/index) each load a short set of instructions always and
    the rest only when a task calls for it.
[^memory]: Claude Code documentation, [How Claude remembers your project](https://code.claude.com/docs/en/memory).
[^agentsmd]: [AGENTS.md](https://agents.md/).
[^check]: Claude Code documentation, [Best practices: give Claude a check to run](https://code.claude.com/docs/en/best-practices#give-claude-a-check-to-run).
[^batches]: DORA's research on [working in small batches](https://dora.dev/capabilities/working-in-small-batches/)
    finds that small batches predict better delivery, and matter more when AI writes the code,
    since "large changes are difficult to review, test, and integrate safely".
