---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
type: ADR
status: 👍 Accepted
date: 2026-09-01
---

# Export with Python's csv module

## Question

How does the accountant's export write its file, quickly enough for a year of invoices?

## Decision

Chosen: Python's csv module, because it quotes fields correctly and is fast enough for a year of invoices.

## Background

The accountant exports a year of invoices at once, about 10,000 of them, and it must be quick.

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

Applies to: the export code.

1. Test: exporting 10,000 invoices takes under 1.0 seconds.

## Open questions

- None.

## Technical detail

The check in full: running `python3 tests/bench_export.py` prints the time taken to export 10,000 invoices, which must be under 1.0 seconds.
