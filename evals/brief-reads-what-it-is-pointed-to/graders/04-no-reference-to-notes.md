---
type: regex
target: { source: file, path: docs/brief.md }
pattern: 'kickoff-notes|\]\((?!https?:|mailto:|#)'
flags: i
match: not_contains
weight: 1
---
The brief does not link to the notes it was drawn from, nor give their path: they are not a
lifecycle document, so the brief states their facts in its own words.
