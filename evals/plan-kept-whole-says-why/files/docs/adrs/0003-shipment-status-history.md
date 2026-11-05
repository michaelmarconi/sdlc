---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
status: 👍 Accepted
date: 2027-01-20
---

# Keep each shipment's status as a history of events

## Context and Problem Statement

Support staff need to see what happened to a shipment and when, not only where it is now.

## Considered Options

- Overwrite a single status field: rejected, because it loses what happened before.
- Record every status change as an event: chosen.

## Decision Outcome

Chosen option: record every status change as an event, because the history answers customers'
questions.

### Consequences

- Good: the full history of every shipment is kept.
- Bad: reading the current status means finding the latest event.

### Confirmation

Applies to: any code that changes a shipment's status.
Checked by: inspection that status changes go through the one function that records events.
