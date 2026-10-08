---
statuses: proposed unclear accepted rejected superseded reversed resolved
keep_in_inbox: proposed unclear
cap_decision_words: 60
cap_note_words: 400
---

# The note model

The one place the ledger's conventions are stated. The frontmatter above is read by
`tenet/ledger.py` for promote, the sweep and the verdict; change a value there and the check changes with it. A rule marked
*(checked)* has a mechanism; the rest are judgement calls, and are marked as such by being
unmarked.

## Frontmatter

Property names and every value a script compares are English. Free text (`revisit`,
`resolves`) is prose in the ledger's language.

| Property | Values |
|---|---|
| `type` | `decision`, `pattern`, `open`, `source`, `gotcha` |
| `created` | `YYYY-MM-DD` |
| `status` | the list below *(checked)* |
| `categories` | block list of `"[[Plural Noun]]"`, quoted *(checked)*; the link resolves to a hub note of that name |
| `related` | block list of wikilinks; link generously |

Type-specific: `revisit`, `supersedes`, `superseded` on decisions; `derived` on patterns;
`resolves` on open questions; `url`, `accessed`, `influenced`, `kept` on sources; `admission` on
files in `raw/`. A gotcha adds nothing. Frontmatter uses block lists, never inline arrays.

## Status

| Status | Meaning | Where the note lives |
|---|---|---|
| `proposed` | a draft awaiting a verdict | `inbox/` |
| `unclear` | the note failed, not the idea: rewrite or split | `inbox/` |
| `accepted` | the user works by it | root *(moved by promote.py at session start)* |
| `rejected` | weighed and turned down before it took effect; kept for the reasoning | root |
| `superseded` | replaced by a later note, linked in `superseded` | root |
| `reversed` | it took effect, then its `revisit` condition fired | root |
| `resolved` | an open question that got settled | root |

The user never types a status: the review writes it. Off-vocabulary values are reported, never
guessed *(checked)*.

## What earns a note

Any of three gates:

- **A. A real decision.** At least two genuinely viable paths, one chosen for a reason. Could a
  competent person have chosen differently? If not, it was a forced move.
- **B. The user's insight.** A formulation they arrived at and said, in their words.
- **C. A tool that surprised you and will again.** Not specific to one repository, and with no
  second viable path. That is a gotcha; if there was a choice, it is a decision.

Not a note: routine implementation, forced moves, debugging (unless it went through C), session
summaries, findings about one project (evidence for a decision's Why), anything already recorded
(extend or supersede instead), general knowledge.

## Format — the 30-second test

The user must grasp the note in half a minute. Sections in reading order; the headings are the
ones in the ledger's own templates, in its own language. The machinery reads exactly one of
them: the first `##` heading of `templates/Decision Template.md`, which the length cap matches.

- **decision:** Decision (≤ 60 words, *checked*) → When to reconsider (mirrored into `revisit`,
  concrete enough to recognise: "p95 passes 400 ms", not "if requirements change") → Why
  (external evidence with its source named) → Background → Options weighed → The dilemma.
- **gotcha:** What happened → Why (the mechanism) → The workaround → What gave it away.
- **pattern:** The insight → Where it holds → Where it does NOT hold (required) → Where it came
  from (mirrored into `derived`).
- **open:** The tension → Why it is parked → What would close it (mirrored into `resolves`) →
  Interim position. Not a to-do.
- **source:** What I took → What I did NOT take, and why → Why raw material is kept (only when
  it is). Its subject is the source's effect on the user's thinking, never a summary.

The whole note stays under 400 words (decisions and gotchas, *checked*). One decision per note:
two reversal conditions are two notes. One paragraph per line, never hand-wrapped. Write the way
you would say it: second person, everyday words, the concrete case kept. An addendum may add
evidence but never flip the conclusion; rewrite the Decision or supersede the note. Drafts carry
real dates, never a literal `{{date}}` *(checked)*.

## Evidence versus insight

A finding from research, a tool or an assistant is evidence: it goes in a decision's Why with
its source named. A `pattern` records only the user's own insight, in their own formulation.
This boundary is what lets them tell their thinking apart from what they were handed.

## Layout and naming

Knowledge notes live flat in the ledger root; folders are machinery only (`_meta/`, `inbox/`,
`raw/`, `templates/`). Titles are descriptive sentences, not labels. Categories are plural. Link
every note to its topic hub when one exists; name a contradiction instead of smoothing it over.

Raw material enters `raw/` only when it cannot be retrieved again or is an intermediate work
product with no other home, always with a companion `source` note. Email, tasks, calendar entries,
CRM records and chat logs never enter the ledger.
