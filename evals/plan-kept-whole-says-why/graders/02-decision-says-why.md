---
type: regex
target: trace
pattern: '"name":"(Write|Edit)"[^\n]*docs/plans/[^\n]*## Decisions\\n(?:(?!## Plan)(?:\\.|[^"\\]))*?\\n- (?:(?!\\n- |## Plan)(?:\\.|[^"\\]))*practice(?:(?!\\n- |## Plan)(?:\\.|[^"\\]))*(twice|same)'
weight: 1
---
One line under the plan's Decisions section names the practice the plan goes against and gives the person's reason: both requirements hang off the same release message, so building them apart would change that code twice.
