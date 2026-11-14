---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
type: ADR
status: 👍 Accepted
date: 2026-09-01
supersedes: 0001
---

# Keep amounts as whole numbers of cents

## Question

In what form does the code keep amounts of money?

## Decision

Chosen: whole numbers of cents, because integer sums are exact.

## Background

Floating-point numbers can't hold most amounts of pounds exactly, so totals drift by a cent.

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

Applies to: any code that stores or works out amounts of money.

1. Inspection: every amount is an int of cents; no amount is ever a float, and no code multiplies or divides an amount by a float.

## Open questions

- None.

## Technical detail

None.
