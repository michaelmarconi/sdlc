---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
type: ADR
status: 👍 Accepted
date: 2026-09-01
---

# Use only Python's standard library

## Question

May the tool use packages from outside Python's standard library?

## Decision

Chosen: the standard library only, because it needs no install step.

## Background

The tool is run on the clerk's own computer, where nothing can be installed.

## Options

| Option | Outcome | Why |
| --- | --- | --- |
| The other way | Rejected | It was worse |

## Consequences

- Good: it is simpler.
- Bad: none known.

## Out of scope

None.

## How we'll check

Applies to: all code under `src/`.

1. Inspection: every import in `src/` is a module of Python's standard library.

## Open questions

- None.

## Technical detail

None.
