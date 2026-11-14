---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
type: Plan
status: ✅ Built
---

# Work out invoice totals

## Specs

- [Invoice totals](../specs/invoice-totals.spec.md)
  - [Line amount](../specs/invoice-totals.spec.md#1-line-amount)
  - [Invoice total](../specs/invoice-totals.spec.md#2-invoice-total)

## ADRs

| ADR | Decision |
| --- | --- |
| [0002](../adrs/0002-amounts-in-whole-cents.md) | Keep amounts as whole numbers of cents |

## Decisions

- None.

## Plan

Add `line_amount` and `total` to `src/invoices.py`, with tests.

## Open questions

- None.
