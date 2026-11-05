---
type: regex
target: trace
pattern: 'subagent_type[^,]{0,8}sdlc:adr-reviewer[\s\S]*"name":"(Edit|Write|MultiEdit)"[^\n]*docs/adrs/[^\n]*\.md(?![\s\S]*subagent_type[^,]{0,8}sdlc:correction-checker)'
match: not_contains
weight: 1
---
Every correction made after the review was followed by a correction check, so the person never gets an unchecked correction.
