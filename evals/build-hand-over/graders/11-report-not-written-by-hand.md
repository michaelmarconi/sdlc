---
type: regex
target: trace
pattern: '\"name\":\"(?:Write|Edit|MultiEdit)\",\"input\":\{\"file_path\":\"[^\"]*(?:/reports/|agentic-reports-)'
match: not_contains
weight: 1
---
Claude neither wrote nor edited the report file itself.
