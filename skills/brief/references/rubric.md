# Brief rubric

Each check passes or fails. `/brief` reads this while writing; the brief reviewer reads it while
checking, and quotes the brief as evidence for every failure.

1. **Shape.** The brief has no status, so no `status:` frontmatter. Under a title naming the
   product comes one sentence saying what it is and why it exists, then at least the sections
   Problem, Who it's for, Goals, Out of scope, Constraints and Open questions, in that order
   relative to each other. Further sections, such as "Safety and security" or "Risks", may go
   wherever they fit before Open questions, which comes last, and every other check applies to
   them too. If the person has not named the product, the title describes it and Open questions
   asks for its name.
2. **Whole product.** Every section speaks for the product as a whole. Nothing describes how
   one capability behaves, such as a rule, a limit or what one screen does: that belongs in the
   capability's spec. Nor does the brief list features; specs are the list.
3. **Problem, not solution.** Problem says who has the problem and what they do today, and does
   not mention the solution, not even in passing, such as the app, screen or feature that will
   fix it. While the person has not told you, a Problem that says so, with Open questions asking,
   passes.
4. **People with roles.** Who it's for names each user or other person involved, what their role
   is, and how often they hit the problem. A missing role or frequency passes only while Open
   questions asks for it.
5. **Measurable goals.** Each goal names something that can be observed or counted, and how,
   such as "support emails with attachments fall from 300 a week to under 50, counted in the
   help desk". A vague goal ("make it easier") fails, unless Open questions asks for its measure.
6. **Out of scope is named.** Out of scope lists at least one thing the product will not be or
   do. While the person has not said, a section that says so, with Open questions asking, passes.
7. **What, not how.** Nothing chooses a technology, library, data structure or design: those
   belong in ADRs (architecture decision records). Constraints holds only hard
   limits the person stated for the whole product, such as a law, a deadline or a system it
   must work with.
8. **Nothing guessed.** The brief states only what the person said or showed. It carries no
   guesses, hedges ("probably", "we assume", "likely") or inline markers such as [A] or [?]: an
   assumption is an open question the person can confirm, such as "Is it right that support
   staff are the main users?". Each open question asks one thing. Open questions is empty or
   "None." only when nothing is unknown.
9. **References.** The brief does not refer to a spec, an ADR, a plan or a spike record in any way:
   no hyperlink, path or title. Those can change or be deleted without the brief being touched, so
   the reference would go stale. The brief refers to outside material only by a web link. It never
   refers, by hyperlink, path or title, to material handed over in the conversation, to anything
   outside the repository, or to a file under `docs/` that is not a brief, spec, ADR, plan or spike
   record: such material can change or vanish without the brief being touched, so what matters from
   it is stated in the brief's own words. References to code are not part of this check.
