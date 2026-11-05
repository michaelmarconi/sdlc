---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
status: 👍 Accepted
---

# Customs hold alerts

## Problem

When customs holds a container at the port, the logistics coordinator at a furniture importer
finds out only when the customer calls to ask where their sofa is, often two days later.

## Goal

The coordinator sees every held container as soon as the customs broker reports the hold, and
sees it leave the list once the broker reports its release.

## Scope

In:
- Holds and releases reported by the customs broker.
- Emailing the coordinator when a container is released.

Out:
- Telling customers about holds.

## Requirements

### Requirement: Hold recorded

When the customs broker reports a hold on a container, the system SHALL add the container to the
list of held containers, showing the time of the hold.

#### Scenario: Hold reported
- GIVEN container MSCU1234567 is not held
- WHEN the broker reports a hold at 2027-02-12 09:12
- THEN the list of held containers shows MSCU1234567, held since 2027-02-12 09:12

Verified by: test, feeding a recorded broker hold message to the update handler.

### Requirement: Release recorded

When the customs broker reports the release of a held container, the system SHALL remove the
container from the list of held containers and show the time of the release on its page.

#### Scenario: Release reported
- GIVEN container MSCU1234567 is held since 2027-02-12 09:12
- WHEN the broker reports its release at 2027-02-13 14:30
- THEN the list of held containers no longer shows MSCU1234567
- AND its page shows cleared since 2027-02-13 14:30

Verified by: test, feeding a recorded broker release message to the update handler.

### Requirement: Coordinator emailed on release

When the customs broker reports the release of a held container, the system SHALL email the
logistics coordinator within 5 minutes, naming the container and the time of the release.

#### Scenario: Release emailed
- GIVEN container MSCU1234567 is held since 2027-02-12 09:12
- WHEN the broker reports its release at 2027-02-13 14:30
- THEN by 2027-02-13 14:35 the coordinator has an email saying MSCU1234567 was released at
  2027-02-13 14:30

Verified by: test, with a stand-in email server that records the messages it receives.

## Constraints

- None.

## Open questions

- None.
