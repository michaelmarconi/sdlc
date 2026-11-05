# ADR rubric

Each check passes or fails. `/adr` reads this while writing; the ADR reviewer reads it while
checking, and quotes the ADR as evidence for every failure.

1. **Shape.** The file is `docs/adrs/NNNN-<subject>.md`, with a four-digit number no other ADR in
   the folder uses. The subject is three to five lowercase words joined by hyphens, naming what
   the decision is about, such as `0004-session-data-storage.md`, not the decision itself. Its
   frontmatter has `status:` set to `📝 Draft`, `👍 Accepted`, `❌ Rejected` or `↪️ Superseded`,
   emoji included, and `date:` as YYYY-MM-DD. The sections are Context and Problem Statement,
   Considered Options, Decision Outcome with Consequences and Confirmation under it, and Open
   questions, in that order.
2. **Title states the decision.** The title names the option chosen, such as "Store sessions in
   Redis", not the topic, such as "Session storage". While no option is chosen yet, a title
   naming the question passes.
3. **One decision.** The ADR makes exactly one choice. If one part of it could be superseded
   while the rest stands, it holds two decisions; that includes a second choice slipped into
   Consequences or Confirmation, such as "we will also use X".
4. **Context states the need.** Context says what forces a decision now, in words a newcomer can
   follow, and does not argue for an option.
5. **Real options.** Considered Options lists at least two options that could each meet the
   need, and each option not chosen says why it was rejected.
6. **Outcome.** Decision Outcome names one of the considered options and gives the reason for
   choosing it. While the person has not chosen, Decision Outcome says so, Open questions asks for
   the choice, and the ADR stays `📝 Draft`.
7. **Consequences.** Consequences names at least one good and one bad result of the choice.
8. **Confirmation.** Confirmation says what the decision applies to, as a concern such as "any
   code that stores or reads session data", never as file paths, and how to check the code
   follows it: by test, demonstration, inspection or analysis. The method can really be carried
   out.
9. **Supersede fields agree.** An ADR that replaces another has `supersedes:` with that ADR's
   four-digit number; a `↪️ Superseded` ADR has `superseded-by:` with the four-digit number of its
   replacement. Each
   number exists in `docs/adrs/`, and an ADR is `↪️ Superseded` only when its replacement is
   `👍 Accepted`, with both ends then naming each other. While the replacement is still
   `📝 Draft`, the ADR it replaces stays `👍 Accepted` with no `superseded-by:`; that passes.
10. **References.** Of the lifecycle's documents, the ADR refers only to other ADRs, and names them
    by number. It does not refer to a spec, the brief, a plan or a spike record in any way: no
    hyperlink, path or title; a spike's measurements are stated in the ADR's own words. Those
    change while an ADR does not, so the reference would go stale. The ADR refers to outside
    material only by a web link. It never refers, by hyperlink, path or title, to material handed
    over in the conversation, to anything outside the repository, or to a file under `docs/` that
    is not a brief, spec, ADR, plan or spike record: such material can change or vanish without the
    ADR being touched, so what matters from it is stated in the ADR's own words. References to code
    are not part of this check.
11. **No overlap.** No other `📝 Draft` or `👍 Accepted` ADR in `docs/adrs/` decides the same thing or
    contradicts this one, unless this one supersedes it.
12. **Accepted means settled.** A `👍 Accepted` or `↪️ Superseded` ADR has no open questions: its
    Open questions section is empty or says only "None." A `📝 Draft` or `❌ Rejected` ADR may
    have some.
