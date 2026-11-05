---
tags: [spec]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Agent]
---

Write a spec, saved as docs/specs/account-lockout.spec.md, from this support ticket. Put "Source: ticket SUP-412" at the top so readers know where it came from. Just draft it, no questions.

SUP-412: Customers say attackers keep guessing passwords. Agreed fix: after 5 failed sign-ins in a row, lock the account for 15 minutes and email the owner that it happened.
