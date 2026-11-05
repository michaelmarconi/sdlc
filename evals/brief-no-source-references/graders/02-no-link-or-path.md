---
type: regex
target: { source: file, path: docs/brief.md }
pattern: 'courtside-prd|\]\((?!https?:|mailto:|#)'
flags: i
match: not_contains
weight: 1
---
The brief has no link to the requirements document, nor its path.
