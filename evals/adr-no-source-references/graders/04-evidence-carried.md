---
type: regex
target: { source: file, path: docs/adrs/0001-session-data-storage.md }
pattern: '2\s?ms[\s\S]*9\s?ms|9\s?ms[\s\S]*2\s?ms'
weight: 1
---
The ADR states the measurements itself: 2 ms from Redis and 9 ms from Postgres.
