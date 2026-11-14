---
type: regex
target: trace
pattern: 'Report written: \S*(?:/reports/|agentic-reports-)\S*build-\S*\.md'
weight: 1
---
The script wrote the build's report file outside the repository.
