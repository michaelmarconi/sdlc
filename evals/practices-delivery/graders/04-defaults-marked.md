---
type: regex
target: trace
pattern: '"name":"(Write|Edit)"[^\n]*"file_path":\s*"[^"]*(AGENTS\.md|docs/practices/[^"]*)"[^\n]*\(default\)'
weight: 1
---
Proposals the person accepted without stating them are marked as defaults.
