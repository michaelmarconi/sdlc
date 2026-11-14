---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
type: Spec
status: 📝 Draft
---

# Credit notes

## Story

When the firm refunds a customer, the accounts clerk wants to issue a credit note rather than
a negative invoice, so they can record refunds in a way the accountant understands.

## In scope

- What the requirements below say.

## Out of scope

- Anything else.

## Requirements

### 1. Issue a credit note

When the clerk refunds part of an invoice, the system SHALL issue a credit note for that amount, naming the invoice.

| Example | Partial refund |
|---|---|
| Given | invoice 17 for 1950 cents |
| When | the clerk refunds 500 cents |
| Then | credit note 1 for 500 cents names invoice 17 |

#### How we'll check

Test.

## Constraints

- None.

## Open questions

### 1. Whether a credit note gets its own number sequence

Credit notes could share the invoices' numbers or have their own.

> **Proposed:** Yes, separate from invoices.
>
> **Why:** Accountants expect each kind of document to be numbered on its own.
