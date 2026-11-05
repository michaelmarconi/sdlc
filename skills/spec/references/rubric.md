# Spec rubric

Each check passes or fails. `/spec` reads this while writing; the spec reviewer reads it while
checking, and quotes the spec as evidence for every failure.

1. **Shape.** The spec has `status:` frontmatter set to `📝 Draft` or `👍 Accepted`,
   emoji included, and at least the sections Problem, Goal, Scope, Requirements, Constraints and
   Open questions, in that order relative to each other. Further sections, such as "Security" or
   "Privacy", may go wherever they fit before Open questions, which comes last, and every other
   check applies to them too. A further section holds no `### Requirement:` heading; those
   belong under Requirements.
2. **One specific story.** Problem names who is stuck and what happens to them today, as one
   concrete situation rather than a general complaint, and does not mention the solution, not
   even in passing, such as the file format, screen or button it will use. While the person has
   not given the story, a Problem that says so, with Open questions asking for it, passes.
3. **Out of scope is named.** Scope names at least one thing that is out, not only what is in.
   While the person has not said what is out, an Out list that says so, with Open questions
   asking what is out, passes; "anything not stated is undecided" alone does not.
4. **What, not how.** Nothing in the spec chooses a technology, library, data structure or
   design. Such a choice belongs in an ADR, and a choice still to make is an open question.
5. **One rule per requirement.** Each requirement has a `### Requirement:` heading with a name
   unique in the spec, and exactly one rule sentence in an EARS pattern, using SHALL once.
6. **Scenarios add cases.** Each requirement has at least one `#### Scenario:` in
   Given/When/Then, and each scenario pins down a concrete case, such as a boundary or an
   example with real values. Where a rule has a limit, such as a time or a count, scenarios sit
   just on each side of it, and the spec's rules state the outcome on both sides (one rule may
   cover both, as in "SHALL accept the link if it is at most 24 hours old, and reject it
   otherwise"). Example values name no person except people the person named: otherwise use
   generic ones such as `user@example.com`. A scenario that only restates the rule fails. So
   does one whose outcome no rule in the spec states, such as what happens on an error or when a
   rule's condition does not hold: until the person decides that case, it is an open question,
   or a rule is widened to state it.
7. **Verified by.** Each requirement ends with a `Verified by:` line naming a method (test,
   demonstration, inspection or analysis) and what it checks, and the method can really be
   carried out: a test that depends on an outside system names the stand-in it uses, and
   something only a person can check is a demonstration or inspection, not a test.
8. **Testable words.** No rule, scenario or constraint relies on words that cannot be checked,
   such as "fast", "user-friendly" or "as appropriate", without a measure.
9. **Accepted means settled.** A spec with status `👍 Accepted` has no open questions: its
   Open questions section is empty or says only "None."
10. **No overlap.** No other spec under `docs/specs/` covers the same capability or contradicts a
    requirement here.
11. **References.** The spec does not refer to the brief, another spec, an ADR, a plan or a spike
    record in any way: no hyperlink, path or title. Those can change or be deleted without this
    spec being touched, so the reference would go stale. A spike's answer is stated in the spec's
    own words, with its evidence. The spec refers to outside material only by a web link. It never
    refers, by hyperlink, path or title, to material handed over in the conversation, to anything
    outside the repository, or to a file under `docs/` that is not a brief, spec, ADR, plan or
    spike record: such material can change or vanish without the spec being touched, so what
    matters from it is stated in the spec's own words. References to code are not part of this
    check.
