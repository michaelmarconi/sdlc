---
type: regex
target: trace
pattern: '## Left for you to check(?:\\n|\n)(?:(?!(?:\\n|\n)## )[\s\S])*?(?:/verify|[Vv]erify)[\s\S]*=== END OF THE REPORT ==='
weight: 1
---
The build's report file reminds the person to check the work, for example with /verify, before merging.
