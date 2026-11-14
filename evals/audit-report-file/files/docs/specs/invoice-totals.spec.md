---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
type: Spec
status: 👍 Accepted
---

# Invoice totals

## Story

When the accounts clerk writes an invoice, the clerk wants its lines added up for them, so they can
send invoices whose totals are right without adding them up by hand.

## In scope

- What the requirements below say.

## Out of scope

- Anything else.

## Requirements

### 1. Line amount

The system SHALL work out each line's amount as its quantity times its unit price.

| Example | Three at a price |
|---|---|
| Given | a line of 3 hinges at 250 cents each |
| When | the line's amount is worked out |
| Then | it is 750 cents |

#### How we'll check

Test.

### 2. Invoice total

The system SHALL work out an invoice's total as the sum of its lines' amounts.

| Example | Two lines |
|---|---|
| Given | lines of 750 and 1200 cents |
| When | the total is worked out |
| Then | it is 1950 cents |

#### How we'll check

Test.

## Constraints

- None.

## Open questions

- None.
