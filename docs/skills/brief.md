# `/brief`

`/brief` is the skill for writing and changing the product brief. It is one step of
[the SDLC](../../README.md); read that page first for the documents, skills and agents it
mentions.

## What a brief is

The brief says what the product is, who it is for, why it exists and how we will know it works.
A product has one brief, at `docs/brief.md`. It is edited in place, and git is its history.

The brief holds only what is true of the whole product. How one capability behaves, such as a
rule or a limit, belongs in that capability's [spec](spec.md), and a technical choice belongs in
an [ADR](adr.md). Keeping each thing in one place means the documents cannot
disagree. Specs read the brief to see whether they fit the product.

Unlike the other documents, the brief has no status. A spec moves from `📝 Draft` to
`👍 Accepted` once you accept its text, but the brief is never signed off as finished: it is only
kept true.

## Anatomy

| Section | Holds |
|---|---|
| Title and summary | The product's name, then one sentence on what it is and why it exists |
| Problem | Who has the problem, and what they do about it today[^shapeup] |
| Who it's for | Each user or other person involved, their role, and how often they hit the problem |
| Goals | What changes for the product as a whole, by how much, and how we will see it |
| Out of scope | What the product will not be or do[^shapeup] |
| Constraints | Hard limits on the whole product, such as a law, a deadline or a system it must work with |
| Open questions | What is not known yet |

These sections are the minimum. A brief for a larger or riskier product can have more, such as
"Safety and security" or "Risks", when you ask `/brief` for them; they go before Open questions,
and are held to the same checks as the rest.

The brief says only what you told `/brief` or showed it. Anything it does not know, or would
otherwise have to assume, goes in Open questions, worded so you can answer or confirm it, such as
"Is it right that support staff are the main users?". Where a fact comes from a document you
handed over, such as a requirements document or notes, the brief states it in its own words and
does not refer to that document: it can change or vanish without the brief being touched. Only a
web page may be linked.

## Using `/brief`

Run `/brief` and say what you want: a new brief, or a change to the one you have.

- **Drafts from the conversation.** If you have already talked the product through, `/brief`
  drafts from that, and where you changed your mind, the latest word wins. Only with nothing to go
  on does it ask what you are building first.
- **Reads only what you point to.** The brief records what you intend, which only you know, so
  `/brief` reads the documents and links you give it, the existing brief and the web pages that
  brief links to, and nothing else. It does not search the
  repository, its README or a connected service on its own, because what a repository holds today
  can quietly pass for what the product is meant to be. If it thinks something would help, it asks
  before reading it.
- **Keeps later stages out.** When you mention how one capability behaves or how to build
  something, `/brief` leaves it out of the brief and tells you where it goes: how a capability
  behaves goes in its spec, a technical choice you have made goes in an ADR, and one you have not
  made yet becomes an open question. A hard limit on the whole product, such as a law or a
  deadline, stays in the brief as a constraint.
- **One question at a time.** When the brief has open questions, `/brief` tells you how many
  there are and asks them one at a time, playing back what it has understood.[^superpowers] The
  rest wait in Open questions. If you would rather not answer now, it leaves them there.

## Review

Before you see the brief, `/brief` has its reviewer agent check it against a short list of
pass-or-fail checks: the sections are all there, it speaks for the whole product, the goals can
be measured, nothing is guessed or chooses how to build it. It also checks that the brief refers to no spec,
ADR or plan, nor to any material outside the lifecycle's documents except a web page, by
hyperlink, path or title, since those can change without the brief being touched and the
reference would go stale. A plugin hook also refuses any such hyperlink or path. The reviewer
sees only the brief, not your conversation, so it judges the page as a newcomer would. At
the same time, a language checker reads it for words a newcomer could not follow, by the
[Plain words](../lifecycle.md#plain-words) rule: a term from your field gets a footnote, and
team shorthand is rewritten. `/brief` corrects what both find, once, and has the corrections checked (see
[Review process](../lifecycle.md#review-process)); then you get the brief with the reports.

The reviewer cannot tell whether the brief matches what you said or showed it, so read the draft
before you rely on it.

[^shapeup]: Ryan Singer, [Shape Up, chapter 6: Write the Pitch](https://basecamp.com/shapeup/1.5-chapter-06),
    Basecamp, 2019. We take its problem told before any solution, and its no-gos, things
    explicitly excluded, which become our Out of scope.
[^superpowers]: Jesse Vincent, [obra/superpowers: brainstorming skill](https://github.com/obra/superpowers),
    MIT licence. We take asking one question at a time and playing back what has been understood
    before moving on.
