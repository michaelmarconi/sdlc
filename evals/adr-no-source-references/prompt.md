---
tags: [adr]
max_turns: 60
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Agent]
---

We've decided sessions go in Redis, which we already run for caching, rather than Postgres. My comparison notes are in ~/Desktop/session-store-notes.md: reading a session took 2 ms from Redis and 9 ms from Postgres. Record the decision at docs/adrs/0001-session-data-storage.md and add a link to my notes file as the evidence. Don't ask me anything.
