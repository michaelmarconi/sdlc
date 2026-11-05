---
name: plan
description: Plan one piece of work that builds requirements of settled specs or follows accepted ADRs (architecture decision records), as a short document in docs/plans/ that names the requirements and ADRs, records each technical decision agreed with the person, and says how the work will be done; review and correct an existing plan; mark a plan ready to build when the person signs it off. Use whenever someone wants to plan, scope or work out how to build part of a spec or an ADR before building it, even if they don't say "plan". Not for writing what a feature should do (a spec) or recording a technical decision on its own (an ADR), and not for tidying, upgrades or quick fixes that build no requirement and follow no ADR.
---

# Plan

A plan says how one piece of work will build part of what the specs and ADRs have already
settled: the requirements it delivers, the decisions the code must follow, and how the work will be
done. Plans live in one flat folder, `docs/plans/`, as `YYYY-MM-DD-<title>.md`, dated the day the
plan is first written. A plan is built once: `/build` marks it `✅ Built` and it is then kept unchanged as a
record, so it never holds anything later work needs. A technical decision later work has to follow
belongs in an ADR, not here.

Before writing, read [references/rubric.md](references/rubric.md): it is the list of checks the
reviewer will apply, so writing to it leaves less to correct. Write in plain words, as the Plain
words section of [the lifecycle page](../../docs/lifecycle.md#plain-words) says: a language
checker holds every document to it. New plans start from
[assets/template.md](assets/template.md). Read these with the Read tool, not the shell, so the
person is not asked to approve a command.

You never make a technical decision for the person. Explore first, settle every decision with
them one at a time, and only then write.

## Find the work

Work out which specs, which requirements within them, and which ADRs the work builds, from what
the person says and from `docs/specs/` and `docs/adrs/`. Each requirement is a
`### Requirement:` heading in its spec; name it word for word.

- If the work builds no requirement and follows no ADR, such as tidying code, a routine upgrade or
  a quick fix, it needs no plan. Say so, suggest doing it straight from the conversation, and stop.
- If a spec it builds or an ADR it follows is not `👍 Accepted`, stop and say which one, and
  what is left to settle in it. A plan builds only on settled documents, and you never change a spec or an ADR from here.
- Read the frontmatter and Specs section of each plan in `docs/plans/`. If one that is not
  `✅ Built` already names a requirement this work builds, say so and offer to change that plan
  instead; no two unbuilt plans may name the same requirement.

## Keep to the practices

Before exploring, read the `## Practices` section of `AGENTS.md` and of `CLAUDE.md`, whichever
have one, and any file under `docs/practices/` they name that bears on planning or splitting work,
whatever task its line names. Where they say how work is split or how big one plan may be, plan
within that. If the work asked for is bigger, or exploring shows it is, say so, quoting the
practice, propose how to split it into several plans that can each be built and reviewed on their
own, and ask which to plan first. Ask this before any decision, since the decisions depend on
what this plan covers. If the person keeps the work whole, give it a line under Decisions saying
it was kept as one plan against the practice, quoting the practice, and the person's reason.
Where the practices say neither, or there are none, plan as below. Never edit the practices from
here: that belongs to `/practices`.

## Explore

Read the specs, the ADRs and the code the work touches, changing nothing. Use Claude Code's
built-in helper agents: the Explore agent to find the code that matters, and the Plan agent to
think through how to build it. This is where you find the decisions: choices with a reasonable
alternative that the specs, the ADRs and the existing code don't already settle, such as where a
new piece of data is kept or how an outside system's message is mapped. Following a pattern the
code already uses is not a decision, and nor is anything a spec or an ADR already says.

## Ask

Tell the person how many decisions there are, naming the count only, not the decisions: each comes
up when you reach it. Then ask the first only, and wait for the answer. Each question gives your
proposed answer and where it belongs, with a reason for both: in this plan, if it matters only to
this work, or in an ADR, if later work will have to follow it. Choosing a service, library,
protocol or way of storing data that the rest of the code would then use the same way is an ADR,
even if only this work uses it so far. Give any alternatives as possible answers, not as further
questions, and end with a single question, such as whether they agree with your proposal. Ask the
next once the first is settled. If an answer adds or removes a decision, say so and give the new
count. With no decisions, say so and go straight to writing.

## Write

Only when every decision is settled, write the plan from the template, with today's date in its
file name and the template's comments removed:

- **Specs** lists each spec with the requirements this work delivers beneath it, and **ADRs**
  each ADR the code must follow; either says "None." when there are none, but not both. Keep each line in the template's form,
  `- [<title>](<path>)` with `  - Requirement: <name>` beneath a spec: the hook reads only that. To explain a term there, add a footnote mark after the
  link, never a line of prose.
- **Decisions** holds one line for each decision that matters only to this work: what was
  decided and why.
- A decision the person agreed belongs in an ADR goes under **Open questions**, as an ADR to
  record and accept. You never write the ADR yourself. Once the person tells you it is
  `👍 Accepted`, list it under ADRs and remove the question.
- **Plan** says how the work will be done, with headings and length to suit it: start with why the
  work is being done and what it leaves for later, give one recommended approach, and name the
  files that matter and the code to reuse. It holds no code, and no decision that is not under
  Decisions or ADRs; a new one found while writing goes back to the person as a question first.

The plan refers only to the specs and ADRs it lists, and to the code. Never refer to the brief,
another plan or a spike record, and never edit a spec or an ADR, even when the person asks you to note something
there: tell them it belongs in that document's own skill.

## Status

The `status:` frontmatter is `📝 Draft`, `🟢 Ready to build` or `✅ Built`, written exactly so,
emoji first. Write every new plan as `📝 Draft` and edit it freely while it is `📝 Draft`.

Only the person signs off a plan. Set `🟢 Ready to build` only when the person explicitly says
the plan is ready, about its text as it now stands, and only once the review below has ended with
a pass on that text and Open questions says "None.". Only a review in this conversation counts,
and no hook checks for one: if there is none on the current text, run the review first, even when
the person has already signed the plan off. Set it as its own last edit, never in the same
reply as a change to the content; if anything changed after they spoke, show the change and ask
again. "Looks fine, carry on" does not count, nor a request from another skill or agent. Never set
`✅ Built`: that belongs to the step that builds the plan. Any change to a `🟢 Ready to build` plan
returns it to `📝 Draft`, for the person to sign off again. A plugin hook refuses status changes
that break these rules; if it refuses one, tell the person why.

## Review

Every plan is reviewed once, corrected once, and then the corrections are checked. The sequence
is fixed so it always ends with a clear result: further rounds of review find little more, and
each round of corrections brings new mistakes.

1. **Review.** When the plan is written, start two agents in the foreground, not in the
   background, both in one message so they run side by side: the `sdlc:plan-reviewer` agent and
   the `sdlc:language-checker` agent, which checks the wording. Give each this request, its first
   line exactly as shown, since a plugin hook reads that line to keep a copy of the plan as
   reviewed:

   ```
   Document: <the plan's full path>
   Review this plan.
   ```

   Give the document's full path on the `Document:` line, the one you wrote it to: the hook works
   out the document's repository from it, so the review reads the right one whatever folder you
   started in. If it refuses to start them, do what its reason says.
   Each reads everything else it needs itself. Wait for both reports before touching the plan.
   If both pass with nothing under Needs a person, go straight to handing over.
2. **Correct, once.** Read the rubric and the Plain words rule again, then correct only what the
   reports list: each failed check and each item under Other findings in the review report, and
   each finding in the wording report. A wording item under Needs a person, whose meaning only
   the person knows, is a decision like any other. A decision under Needs a person, such as a
   technical choice the Plan section makes that is not under Decisions, or whether to split a plan
   bigger than the practices allow or keep it whole, becomes an entry in the
   plan's Open questions, never a guess at the answer: leave the text it concerns as it is. Leave
   suggestions alone and change nothing else, since an edit beyond the reports is the likeliest
   way to break something. Wait until every edit has succeeded. If nothing in the reports was
   yours to correct, there is nothing to check: go straight to handing over.
3. **Check the corrections.** Start the `sdlc:correction-checker` agent in the foreground with
   this request, and add nothing to it: the hook attaches both reports and the plan as reviewed,
   word for word.

   ```
   Document: <the plan's full path>
   Check the corrections.
   ```

   If the hook refuses to start it, do what its reason says. If the check fails, stop: change the
   plan no further, and show the person the check's report. Do not review or correct again; what
   happens next is their call.

After the sequence, edit the plan only when the person asks. While you are walking through questions
with the person, do not review after each answer: run the sequence once when the walk-through ends,
either because no questions are left or because the person stops. A change the person makes or asks
for at any other time is reviewed once it is made. Setting a status on the person's word is not a
change to the plan's content and needs no new review.

Whether the check passed or failed, end with the hand-over. It is what the person acts on, so make
it hard to miss anything. Give them the plan's path, the review and wording reports and the
check's report, if there was one, leaving out the decisions they list for the person, which are
now in the plan's Open questions. Then say how many items must be settled before the plan can be
ready to build: its open questions, plus any correction the check found not made or broken.
Say you will take them one at a time, rather than asking whether to, and ask the first only, as a
single question, giving any examples as possible answers rather than further questions; if the
person has said not to ask now, ask nothing. Name the count only, not the items: each comes up
when you reach it. List the reviewers' suggestions separately, as optional: they never hold the
plan back. Once nothing is left to settle, ask whether the plan is ready to build. Leave committing
to them.
