---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
status: 📝 Draft
date: 2026-11-05
---

# Keep each plan within the size the project's practices record

## Context and Problem Statement

This repository is a plugin, an add-on, for Claude Code, Anthropic's AI coding assistant. The
plugin helps a person write a software project's documents, and one of them is a plan: a short
document that says how one piece of work will be built. Claude, or another coding agent, then
builds the plan on a branch of its own, and a person reviews the result before it is merged.

The plugin also records a project's practices: the rules and habits a coding agent follows, kept
in the project's `AGENTS.md` and in topic files under `docs/practices/`. A project can record how
it splits work and how big one piece of work may be, such as "one plan per pull request". Each step of
the plugin is a skill, a set of instructions Claude follows for that step. Today the skill that
builds a plan reads the practices, but the skill that writes the plan does not. So
nothing keeps a plan to the size the project asked for, and an agent can plan, then build, more
than a person can review well.

That matters more when agents write the code. Research by DevOps Research and Assessment (DORA), Google's long-running study
of software delivery, finds that working in small batches[^batch] predicts better delivery, and says of AI
coding assistants: "large changes are difficult to review, test, and integrate safely". It also
says that "any batch of code that takes longer than a week to complete and check is too big"
([DORA: working in small batches](https://dora.dev/capabilities/working-in-small-batches/)).

[^batch]: A batch is the amount of change worked on and delivered together.

## Considered Options

- **Leave planning as it is.** Only the build reads the practices. Rejected: by the time the build
  starts, the person has already signed the plan off, so a plan that is too big is found too late
  or not at all.
- **The planning skill reads the practices and keeps to them, and the person chooses on a
  split.** When the practices say how work is split or how big a plan may be, the skill plans
  within that. When the work asked for is bigger, it proposes splitting it into several plans and
  asks the person. When they record neither, it plans as it does today. A plan the person keeps whole, though it is
  bigger than the practices allow, says why in the part of the plan that records its choices, its
  Decisions section. The plan's reviewer, a separate Claude agent that checks each plan before a
  person sees it, reads the practices too, and fails a plan that is bigger than they allow and does
  not say why.
- **A script or hook that measures a plan's size.** A hook is a script Claude Code runs
  automatically at set moments, such as before each edit. Rejected: practices are written in the
  project's own words, such as "small enough to review in one sitting", so no script can measure
  a plan against them. Judging that takes a model.
- **The build refuses a plan that is too big.** Rejected: the plan has already been signed off,
  and the person would have to plan again from the start.

## Decision Outcome

Chosen option: the planning skill reads the practices and keeps to them, and the person chooses on
a split, because the size is settled while the plan is still being written, and the person, whose
practices they are, can still decide otherwise for a good reason. It is one decision, not two: the reviewer
checks only what the planning skill already does, so neither part would change without the other.

### Consequences

- Good: plans stay as small as the project asked, so each build is one a person can review.
- Good: a plan that breaks the rule says why, so the reviewer, and anyone reading it later, can
  see the choice was made on purpose.
- Bad: the size check is a model's judgement, so a plan just over the limit can pass unnoticed.
- Bad: writing a plan now also reads the practices section of `AGENTS.md`, and any topic file under
  `docs/practices/` that it names for planning work.

### Confirmation

Applies to: how the plugin's planning skill and its reviewer use the project's recorded practices.
Checked by: test. The plugin's tests run the planning skill on a sample project whose practices
limit a plan's size, and check that it proposes a split rather than writing one large plan, that
a plan kept whole because the person chose to says why under Decisions, and that the reviewer
fails a plan bigger than the practices allow that does not say why.

## Open questions

- None.
