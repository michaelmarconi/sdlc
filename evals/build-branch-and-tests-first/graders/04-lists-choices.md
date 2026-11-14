---
type: regex
target: trace
pattern: '=== THE REPORT AS WRITTEN ===[\s\S]*## Choices(?:\\n|\n)(?:\\n|\n)- [\s\S]*=== END OF THE REPORT ==='
weight: 1
---
The build's report file lists the choices the build made itself, as a list under Choices.
