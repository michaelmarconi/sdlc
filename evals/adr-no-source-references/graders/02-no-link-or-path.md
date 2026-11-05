---
type: regex
target: { source: file, path: docs/adrs/0001-session-data-storage.md }
pattern: 'session-store-notes|Desktop|~/|\]\((?!https?:|mailto:|#)'
flags: i
match: not_contains
weight: 1
---
The ADR has no link to the notes file, nor its path.
