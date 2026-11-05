---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
status: 👍 Accepted
date: 2026-11-05
---

# Refuse references to outside material with a hook that checks every edit to a brief, spec or ADR

## Context and Problem Statement

This repository is a plugin, an add-on, for Claude Code, Anthropic's AI coding assistant. Its
skills, sets of instructions Claude follows for one kind of task, write a project's lifecycle
documents under `docs/`: the brief, which says what the product is and for whom; specs, which
say what one capability should do; architecture decision records (ADRs), which each record one
technical decision; plans, which each set out one piece of work that builds part of a spec or an
ADR; and spike records, which hold one throwaway experiment.

People often hand a skill material to draw on, such as a product requirements document, notes or
a ticket, by dropping a file into the conversation or naming one on their computer. A brief
written from such a file referred to it by a link. That file can change or vanish without the
brief being touched, and it may never be in the repository at all. The brief, specs and ADRs
should therefore be understandable without any such file: they state what matters from such
material in their own words, and refer to outside material only by a web link, which is likely
to stay where it is.
They never refer to a file handed over in a conversation, to a path outside the repository, or
to a file under `docs/` that is not one of the lifecycle's documents, since `docs/` should hold
only those. The lifecycle's documents are the five kinds above: the brief, specs, ADRs, plans
and spike records. References to code are not part of this rule. The rule itself is one of the
lifecycle's principles, which hold how its documents are written; this ADR records only how the
plugin enforces it.

Until now references between documents were checked only by the reviewer agents, separate
instances of Claude that check each document a skill writes against a list of checks. The rule
above has an exact shape, so the question is how to enforce it.

## Considered Options

- **Leave it to the reviewer agents.** Rejected: a model reading a long document can miss a
  link, and the rule's shape is exact enough for a script to apply without mistakes.
- **A script the skill runs after writing.** Rejected: it holds only when Claude remembers to run
  it, and, as ADR 0019 found, the skills' tests in Claude Code's cloud sessions cannot run
  commands, so they could never exercise it.
- **A hook that checks every edit Claude is about to make to a brief, spec or ADR.** A hook is a
  script Claude Code runs automatically at set moments, here just before each edit. It is started
  by the same script as the hook of ADR 0005, which checks that a document's status changes only
  in allowed ways, and runs after that check. It reads every link and every reference definition
  outside code in the document as the edit would leave it, and refuses the edit if it adds a
  target that names an address of a kind other than a web or email address (`http`, `https` or
  `mailto`), such as `file:`; is a path starting at the root of the computer or at a home folder (`~`);
  leads outside the repository; or points to a file under `docs/` that is not a lifecycle
  document. Email addresses are allowed because they point to no file. Any other target passes:
  a heading in the same document, a path to code, or a path to another lifecycle document, whose
  references the reviewer agents check against the lifecycle's own rules. A target the document
  already held before the edit is not refused again, as ADR 0019's hook refuses only an edit that
  makes a file worse: an ADR that has been accepted or rejected can't be edited, so it could not
  have the reference removed, and refusing the edit would leave it stuck, though such an ADR is
  only ever replaced by a new ADR, with one edit marking it as replaced. It tells Claude which references to remove and why.

## Decision Outcome

Chosen option: a hook that checks every edit, because it applies the rule exactly, before the
file changes, whichever skill is running, and the skills' tests exercise it without running any
command.

### Consequences

- Good: Claude cannot add a link to material outside the lifecycle to a brief, spec or ADR,
  whether or not a skill is running.
- Good: the refusal names each reference and says why, so Claude can state the material in the
  document's own words in the same session.
- Bad: a reference by title, such as "as the kick-off notes say", or a path written as plain text
  is not a link, so the reviewer agents still have to catch it.
- Bad: a link a document held before this check, or one added by hand, stays until someone
  removes it; only the reviewer agents point it out.
- Bad: the hook sees only edits made with Claude's file-editing tools, not a person's own edits
  or a shell command.

### Confirmation

Applies to: any edit Claude makes to a brief, spec or ADR.
Checked by: test. Unit tests give the hook examples of edits and check that it allows web links,
references to code and references between lifecycle documents, and refuses each kind of
reference above. For each of the brief, spec and ADR skills, a test on a sample conversation has
the person hand over material that is not a lifecycle document, such as a requirements document,
notes or a ticket, and checks that the document written refers to it in no way.

## Open questions

- None.
