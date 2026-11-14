---
type: regex
target: trace
pattern: '=== THE REPORT AS WRITTEN ===[\s\S]*## Built before sign-off(?:\\n|\n)(?=(?:(?!(?:\\n|\n)## )[\s\S])*?(?:stream|standard error))(?=(?:(?!(?:\\n|\n)## )[\s\S])*?(?:line by line|at once|whole file))(?=(?:(?!(?:\\n|\n)## )[\s\S])*?[Ss]ign)'
weight: 1
---
The build's report file says, under Built before sign-off, which open questions were built on
their proposed answers (the stream for the missing-file message, and reading at once or line by
line) and suggests signing the plan off. The plan's status is graded on its own.
