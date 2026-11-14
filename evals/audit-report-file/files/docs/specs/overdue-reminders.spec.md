---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
type: Spec
status: 👍 Accepted
---

# Overdue reminders

## Story

When an invoice is still unpaid after it falls due, the accounts clerk wants the customer
reminded, so they can get paid before the firm runs short of cash.

## In scope

- What the requirements below say.

## Out of scope

- Anything else.

## Requirements

### 1. First reminder

When an invoice is still unpaid 30 days or more after its issue date, the system SHALL put it on the reminder list.

| Example | Thirty days |
|---|---|
| Given | invoice 17, issued on 1 October and unpaid |
| When | the list is made on 31 October |
| Then | invoice 17 is on it |

#### How we'll check

Test.

### 2. No reminder once paid

The system SHALL leave paid invoices off the reminder list.

| Example | Paid |
|---|---|
| Given | invoice 18, issued on 1 September and paid |
| When | the list is made on 31 October |
| Then | invoice 18 is not on it |

#### How we'll check

Test.

### 3. Second reminder

When an invoice is still unpaid 60 days or more after its issue date, the system SHALL put it on the second reminder list.

| Example | Sixty days |
|---|---|
| Given | invoice 19, issued on 1 September and unpaid |
| When | the second list is made on 31 October |
| Then | invoice 19 is on it |

#### How we'll check

Test.

## Constraints

- None.

## Open questions

- None.
