---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
status: 📝 Draft
---

# Customs hold release and email

## Specs

- [Customs hold alerts](../specs/customs-hold-alerts.spec.md)[^hold]
  - Requirement: Release recorded
  - Requirement: Coordinator emailed on release

## ADRs

- [ADR 0003, an architecture decision record: Keep each shipment's status as a history of events](../adrs/0003-shipment-status-history.md)
- [ADR 0004, an architecture decision record: Send emails with Python's standard smtplib](../adrs/0004-coordinator-email-sending.md)

## Decisions

- Show "cleared since <time>" on the container's page in place of "held since": the support team
  asked to see when a hold ended when customers call.

## Plan

A customs hold stops a shipping container from leaving the port, and a release ends it. The customs
broker[^broker] reports each hold and release to the system, but releases are ignored today, so
released containers stay in the list of held containers. A release becomes a "cleared" status
event, "cleared" being the status of a container whose hold has ended, recorded through
`record_status()` in `src/shipments.py`, the way `src/broker/updates.py` already records holds, as
ADR 0003 requires. The list in `src/holds/list.py` already shows only containers whose latest event
is "held", so a cleared container leaves it with no change there. The same handler then emails the logistics coordinator, naming the container and the time of
the release, through a new `send_release_email()` in `src/notify.py`, using `smtplib` as ADR 0004
requires.

1. Write the failing test from the spec's scenario: hold at 2027-02-12 09:12, release at
   2027-02-13 14:30.
2. Turn the broker's "released" message into a "cleared" event in `src/broker/updates.py`.
3. Show "cleared since <time>" in `summary()` in `src/page.py`.
4. Write the failing email test with a stand-in email server, then add `send_release_email()`
   and call it from the release handler.

## Open questions

- None.

[^hold]: An order from the customs authority that a container stay where it is until its goods
    are inspected or its paperwork is approved.
[^broker]: A licensed agent who deals with the customs authority for the company bringing the
    goods into the country.
