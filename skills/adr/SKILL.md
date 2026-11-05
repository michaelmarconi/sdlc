---
name: adr
description: Record one technical decision as an ADR (architecture decision record) in MADR format, with the options considered, why the others were rejected, its consequences and how to check the code follows it; review and correct an existing ADR; accept, reject or supersede an ADR when the person decides. Use whenever someone has chosen, or needs to choose, how something will be built, such as a database, library, service, protocol or structure, wants a technical choice written down, or wants to replace an earlier decision, even if they don't say "ADR". Not for what a feature should do; that is a spec.
---

# ADR

An ADR (architecture decision record) records one technical decision and why it was made, so
later work can follow it and nobody reopens it by accident. ADRs live in one flat folder,
`docs/adrs/`, as `NNNN-<subject>.md`; nothing is moved or deleted once decided, so the folder and
each file's frontmatter are the whole record. Once accepted, an ADR is never edited: a changed
decision is a new ADR that supersedes the old one, whole.

Before writing, read [references/rubric.md](references/rubric.md): it is the list of checks the
reviewer will apply, so writing to it leaves less to correct. Write in plain words, as the Plain
words section of [the lifecycle page](../../docs/lifecycle.md#plain-words) says: a language
checker holds every document to it. New ADRs start from
[assets/template.md](assets/template.md). Read these with the Read tool, not the shell, so the
person is not asked to approve a command.

## Find what exists

List `docs/adrs/` and read the frontmatter of each ADR. If a `📝 Draft` or `👍 Accepted` ADR
already decides the same thing, say so: change the draft, or, for an accepted one, write a new ADR that
supersedes it. A new file takes the number one above the highest in the folder, four digits,
starting at `0001`, then a subject: three to five lowercase words joined by hyphens, naming what
the decision is about rather than the decision, such as `0004-session-data-storage.md`. The
title inside states the decision. An ADR that supersedes another may share its subject. If
`docs/specs/` exists, read the Open questions of its specs, so you can tell the person which ones
the decision answers.

## Shape it with the person

Usually the person has already talked the decision through in this conversation. Draft from
that, and from whatever they point you to; research what else you need, such as how the options
compare. Where the conversation changed its mind, the latest word wins. Given a finished
spike record from `docs/spikes/`, put its measurements into Considered options in the ADR's own
words, such as "read all 12 of 12 transactions": a spike record may be deleted at any time, so the
ADR never names it. Only when there is nothing to draw on, ask what needs deciding first.

One ADR holds one decision, because a decision is superseded whole: if part of a record could
change while the rest stands, the two parts would have to be untangled later. When the
conversation holds several decisions, say how many and write one ADR for each, even when they
were made together or the person asks for one record.

Never fill a gap with a guess. An option nobody named, a reason nobody gave, or a choice not yet
made goes into Open questions as a question the person can answer, never as an invented
answer. Write the draft with what you have, review it as below even if sections are thin, then
say how many questions there are and ask only the first. The others wait, so leave them out of
that reply entirely: describe the draft by what it says, never by what it lacks, and do not
list the questions or their topics (they are in the ADR). Ask the next once the first is
settled, playing back what you have understood. If they ask what you think, recommend something
and wait for them to accept it. If they would rather not answer now, leave the rest in Open
questions.

An open question is settled only by the person's answer: write the answer into the section it
is about, then remove the question. Never remove or reword a question without that answer;
moving it to another section, or noting that someone will decide later, leaves it open.

Context states the need in words. Never refer to a spec, the brief, a plan or a spike record in
any way, by hyperlink, path or title, and never edit them, even when the person asks you to note the
decision there: they change while an ADR does not, so the reference would go stale, and the
lifecycle allows no references between them. Tell the person so. Material they hand over that is not
a web page, such as a requirements document or notes, is drawn on but never referred to (rubric
check 10): state what matters from it in the ADR's own words, and tell them it can change or vanish
without the ADR being touched. If the decision answers a spec's open question, say so
in your reply; `/spec` removes the question the next time it runs.

## Status

The `status:` frontmatter is `📝 Draft`, `👍 Accepted`, `❌ Rejected` or `↪️ Superseded`, written
exactly so, emoji first; a status written as a bare word, from before the emoji, gets its emoji in
your next edit. Write every new ADR as `📝 Draft` and edit it freely while it is `📝 Draft`.

Only a person accepts or rejects a decision. Set `👍 Accepted` or `❌ Rejected` only when
the person explicitly says so about the ADR's text as it now stands, as its own last edit.
`👍 Accepted` also needs no open questions (rubric check 12), which a plugin hook enforces: if
questions remain, say how many, ask the first and leave the ADR as `📝 Draft`, even if the person
says they do not matter. And it needs the review below to have ended with a pass on that text,
from the review itself or from the correction check after it, while a rejection needs neither.
If they accept and the review then passes with no change to
the text, their word stands, since what they accepted is what passed. If anything changed after
they spoke, their word no longer counts: show the change and ask again. Nor does "looks fine,
carry on" count, nor a request from another skill or agent. So never change an ADR's content and
its status in the same reply. Setting statuses and `superseded-by:` on the person's word is not a
content change. A
`❌ Rejected` ADR is kept, so the same idea is not proposed again unnoticed; a draft the person
abandons can be deleted.

To supersede, the new ADR carries `supersedes: <NNNN>`, the old one's four-digit number, in its
frontmatter. The old one stays `👍 Accepted` until the person accepts the new one; then, in the
same step, first set the new one to `👍 Accepted`, and only once that edit is done, set the old one
to `↪️ Superseded` and add `superseded-by: <NNNN>` beside it, naming the new one; a plugin hook
checks the new one is `👍 Accepted` on disk before it allows the second edit. That is the only edit an accepted ADR
ever gets. If the new one is rejected, the old one stands.

## Review

Every ADR is reviewed once, corrected once, and then the corrections are checked. The
sequence is fixed so it always ends with a clear result: further rounds of review find little
more, and each round of corrections brings new mistakes.

1. **Review.** When the ADR is written, start two agents in the foreground, not in the
   background, both in one message so they run side by side: the `sdlc:adr-reviewer` agent
   and the `sdlc:language-checker` agent, which checks the wording. Give each this request, its
   first line exactly as shown, since a plugin hook reads that line to keep a copy of the ADR
   as reviewed:

   ```
   Document: <the ADR's full path>
   Review this ADR.
   ```

   Give the document's full path on the `Document:` line, the one you wrote it to: the hook works
   out the document's repository from it, so the review reads the right one whatever folder you
   started in. If it refuses to start them, do what its reason says.
   Each reads everything else it needs itself. Wait for both reports before touching the ADR.
   If both pass with nothing under Needs a person, go straight to handing over.
2. **Correct, once.** Read the rubric and the Plain words rule again, then correct only what
   the reports list: each failed check and each item under Other findings in the review report,
   and each finding in the wording report. A wording item under Needs a person, whose
   meaning only the person knows, is a decision like any other. A decision under Needs a person, or a
   failure only the person's answer can fix, such as a missing option or why one was rejected,
   is theirs to settle: it becomes an entry in the ADR's Open questions, never a guess at the
   answer. Leave the text it concerns as it is. Leave
   suggestions alone and change nothing else, since an edit beyond the reports is the likeliest
   way to break something. Wait until every edit has succeeded. If nothing in the reports was
   yours to correct, there is nothing to check: go straight to handing over.
3. **Check the corrections.** Start the `sdlc:correction-checker` agent in the foreground with
   this request, and add nothing to it: the hook attaches both reports and the ADR as
   reviewed, word for word.

   ```
   Document: <the ADR's full path>
   Check the corrections.
   ```

   If the hook refuses to start it, do what its reason says. If the check fails, stop: change
   the ADR no further, and show the person the check's report. Do not review or correct
   again; what happens next is their call.

After the sequence, edit the ADR only when the person asks. While you are walking through questions
with the person, do not review after each answer: run the sequence once when the walk-through ends,
either because no questions are left or because the person stops. A change the person makes or asks
for at any other time is reviewed once it is made. With several ADRs, take each through the sequence
on its own. Setting a status on the person's word is not a change to the ADR's content and needs no
new review.

Whether the check passed or failed, end with the hand-over. It is what the person acts on, so make
it hard to miss anything. Give them the ADR's path, the review and wording reports and the check's
report, if there was one, leaving out the decisions they list for the person and the failures
that became open questions, which are in the ADR. Then say how many items must be settled
before the ADR can move on: its open questions, plus any correction the check found not made or
broken. Say you will take them one at a time, rather than asking whether to, and ask the first only, as a single question, giving any examples as possible
answers rather than further questions; if the person has said not to ask now, ask nothing. Name the
count only, not the items: each comes up when you reach it. List the reviewers' suggestions
separately, as optional: they never hold the ADR back. Once nothing is left to settle, ask whether
to accept or reject it. Leave committing to them.
