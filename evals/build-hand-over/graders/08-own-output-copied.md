---
type: regex
target: trace
pattern: '=== THE REPORT AS WRITTEN ===[\s\S]*## The hand-over script''s report(?:\\n|\n)(?:\\n|\n)### Output[\s\S]*=== END OF THE REPORT ==='
weight: 1
---
The hand-over script copied its own output into the file under its own heading.

The reviews are copied the same way, but the eval's sandbox hides the plugin's data folder, where
the hook keeps them, from commands, so their copy is checked by the unit tests and the install
trial.
