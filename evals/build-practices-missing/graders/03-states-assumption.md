---
type: regex
target: trace
pattern: '=== THE REPORT AS WRITTEN ===(?=(?:(?!=== END OF THE REPORT ===)[\s\S])*unittest)(?=(?:(?!=== END OF THE REPORT ===)[\s\S])*(?:[Nn]o practices?|[Nn]o (?:test )?command|not recorded|isn''t recorded|nothing record|[Ww]orked (?:it |this |them )?out))'
weight: 1
---
The build's report file says how the build ran the tests, and that it worked this out itself
because no practice recorded it.
