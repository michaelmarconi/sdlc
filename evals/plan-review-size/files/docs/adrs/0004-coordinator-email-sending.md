---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
status: 👍 Accepted
date: 2027-01-20
---

# Send emails with Python's standard smtplib

## Context and Problem Statement

The system must email the logistics coordinator about customs holds, and has no email code yet.

## Considered Options

- **A hosted email service's library.** Rejected: it adds an outside account and a library to
  install, for a few emails a day.
- **Python's standard `smtplib`, to the server named by the `SMTP_HOST` setting.**

## Decision Outcome

Chosen option: Python's standard `smtplib`, to the server named by the `SMTP_HOST` setting,
because it needs nothing new installed and the company already runs an email server.

### Consequences

- Good: no new library or account.
- Bad: retries after a failed send are ours to write.

### Confirmation

Applies to: any code that sends email.
Checked by: inspection. Email is sent only through `smtplib`.

## Open questions

- None.
