---
name: brief
description: Write or change the product brief, the one short document at docs/brief.md that says what the product is, who it is for, why it exists and how we will know it works. Use whenever someone wants to start a new product, write or update a brief, a product vision or a one-pager, or capture what the product is and for whom before any specs are written, even if they don't say "brief". Not for one feature or capability; that is a spec.
---

# Brief

The brief says what the product is, who it is for, why it exists and how we will know it works.
A product has one, at `docs/brief.md`, edited in place; git is its history. Specs are written
against it, one per capability, so the brief holds only what is true of the whole product.

Before writing, read [references/rubric.md](references/rubric.md): it is the list of checks the
reviewer will apply, so writing to it leaves less to correct. Write in plain words, as the Plain
words section of [the lifecycle page](../../docs/lifecycle.md#plain-words) says: a language
checker holds every document to it. A new brief starts from
[assets/template.md](assets/template.md). Read these with the Read tool, not the shell, so the
person is not asked to approve a command.

## What to read

The brief records what the person intends, which only they know. So draft from what they said in
this conversation and from what they point you to, such as a document, a link or notes. If
`docs/brief.md` exists, read it and change it rather than starting again; the documents it
already links to on the web count as pointed to. Don't read anything else on your own, not the README, the
code or a connected service: what a repository holds today can quietly pass for what the product
is meant to be. If something would help, ask first ("There's a README here; shall I read it?")
and read it only if they say yes.

## Shape it with the person

Usually the person has already talked the product through. Draft from that, carrying over every
fact they gave that the brief's sections hold, such as who does what; where the
conversation changed its mind, the latest word wins. Only when there is nothing to draw on, ask
what they are building and for whom first.

Write only what they said or showed you, as rubric check 8 describes. What they haven't said becomes an open question, each asking one
thing: "What do they do today, and how long does it take?" is two questions. When they want the
brief to refer to a spec, an ADR (architecture decision record), a plan or a spike record, by
hyperlink, path or title, leave it out (check 9) and tell them why: that document can change or be deleted without the
brief being touched, so the reference would go stale. Material they hand over that is not a web
page, such as a requirements document or notes, is drawn on but never referred to (check 9): state
what matters from it in the brief's own words, and tell them it can change or vanish without the
brief being touched. When they mention something that belongs to a
later stage (rubric checks 2 and 7), leave it out and tell them where it goes: how one capability
behaves goes in its spec, so suggest `/spec`; a technology or design they have decided goes in an
ADR, and one they have not becomes an open question.

Add a section beyond the template's, such as "Safety and security", only when the person asks
for one, and place it as rubric check 1 says.

Then ask about what the draft or the review leaves open: say how many questions there are and ask
only the first, as one question rather than two joined together, with any examples given as possible
answers rather than further questions. The others wait in the brief, so leave them out of that reply
entirely: describe the draft by what it says, never by what it lacks ("nothing yet on who else is
involved" names a question), and report what you or the review changed without naming the gaps that
remain. Ask the next once the first is settled, playing back what you have understood. Settle each
answer before moving on: take the part they answered and ask again about the rest, because silence
is not agreement. If the person has said not to ask now, or would rather not answer, give only the
count: no question and no list of what the questions cover. An open question goes only when their
answer is written into the brief.

## Review

Every brief is reviewed once, corrected once, and then the corrections are checked. The
sequence is fixed so it always ends with a clear result: further rounds of review find little
more, and each round of corrections brings new mistakes.

1. **Review.** When the brief is written, start two agents in the foreground, not in the
   background, both in one message so they run side by side: the `sdlc:brief-reviewer` agent
   and the `sdlc:language-checker` agent, which checks the wording. Give each this request, its
   first line exactly as shown, since a plugin hook reads that line to keep a copy of the brief
   as reviewed:

   ```
   Document: <the brief's full path>
   Review this brief.
   ```

   Give the document's full path on the `Document:` line, the one you wrote it to: the hook works
   out the document's repository from it, so the review reads the right one whatever folder you
   started in. If it refuses to start them, do what its reason says.
   Each reads everything else it needs itself. Wait for both reports before touching the brief.
   If both pass with nothing under Needs a person, go straight to handing over.
2. **Correct, once.** Read the rubric and the Plain words rule again, then correct only what
   the reports list: each failed check and each item under Other findings in the review report,
   and each finding in the wording report. A wording item under Needs a person, whose
   meaning only the person knows, is a decision like any other. Correct by making the brief
   accurate, never by dropping or hedging what the person said. A decision under Needs a person
   becomes an entry in the brief's Open questions, never a guess at the answer. Leave
   suggestions alone and change nothing else, since an edit beyond the reports is the likeliest
   way to break something. Wait until every edit has succeeded. If nothing in the reports was
   yours to correct, there is nothing to check: go straight to handing over.
3. **Check the corrections.** Start the `sdlc:correction-checker` agent in the foreground with
   this request, and add nothing to it: the hook attaches both reports and the brief as
   reviewed, word for word.

   ```
   Document: <the brief's full path>
   Check the corrections.
   ```

   If the hook refuses to start it, do what its reason says. If the check fails, stop: change
   the brief no further, and show the person the check's report. Do not review or correct
   again; what happens next is their call.

After the sequence, edit the brief only when the person asks. While you are walking through
questions with the person, do not review after each answer: run the sequence once when the
walk-through ends, either because no questions are left or because the person stops. A change the
person makes or asks for at any other time is reviewed once it is made.

Whether the check passed or failed, end with the hand-over. It is what the person acts on, so make
it hard to miss anything. Give them the brief's path, the review and wording reports and the check's
report, if there was one, leaving out the decisions they list for the person. Then say how many items must be
settled before the brief can move on: its open questions, plus any correction the check found not
made or broken. Say you will take them one at a time, rather than asking whether to, and ask the
first only, as a single question, giving any examples as possible answers rather than further
questions; if the person has said not to ask now, ask nothing. Name the count only, not the items:
each comes up when you reach it. List the reviewers' suggestions separately, as optional: they never
hold the brief back. Leave committing to them.
