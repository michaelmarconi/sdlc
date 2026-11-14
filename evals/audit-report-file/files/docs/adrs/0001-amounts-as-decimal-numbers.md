---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
type: ADR
status: ↪️ Superseded
date: 2026-09-01
superseded-by: 0002
---

# Keep amounts as decimal numbers of pounds

## Question

In what form does the code keep amounts of money?

## Decision

Chosen: decimal numbers of pounds, because the clerk thinks in pounds.

## Background

Amounts need one form throughout the code.

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

1. Inspection: amounts are floats of pounds.

## Open questions

- None.

## Technical detail

None.
