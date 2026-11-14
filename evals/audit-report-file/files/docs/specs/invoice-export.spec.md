---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
type: Spec
status: 👍 Accepted
---

# Invoice export

## Story

When the accountant needs the firm's invoices, the accounts clerk wants to export them, so
they can hand them over without the accountant retyping each one into their own software.

## In scope

- What the requirements below say.

## Out of scope

- Anything else.

## Requirements

### 1. Export as CSV

When the clerk exports invoices, the system SHALL write one CSV row per invoice, after a header row, with the columns number, date and total, in that order, the total in cents.

| Example | One invoice |
|---|---|
| Given | invoice 17, dated 2026-10-01, totalling 1950 cents |
| When | the clerk exports |
| Then | the file is `number,date,total` then `17,2026-10-01,1950` |

#### How we'll check

Test.

## Constraints

- None.

## Open questions

- None.
