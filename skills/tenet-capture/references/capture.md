# The capture procedure

## The three gates

Something earns a note if **any** is true.

**Gate A — a real decision.** At least two genuinely viable paths existed, and one was chosen
for a reason. Test it: could a competent person reasonably have chosen differently? If not, it
was a forced move, not a decision.

**Gate B — the user's insight.** They arrived at a formulation worth keeping and said it. Their
words, their realisation.

**Gate C — a tool surprised you, and will again.** A platform or tool behaves in a way nobody
would predict, the behaviour is not specific to this repository, and the next encounter with it
is a matter of when. That is a `gotcha`. Test it against Gate A first: if there were two viable
ways and one was picked, it is a decision, not a gotcha.

## What does NOT deserve a note

This list is the difference between a brain and a pile.

- **Routine implementation.** Writing the code that a decision already implied.
- **Forced moves.** "We used the only library that does this." No alternative, no decision.
- **Debugging.** Unless the root cause revealed a structural problem worth deciding about, or the
  root cause was a tool behaving unpredictably — that one goes through Gate C.
- **Session summaries.** "We built X, then Y, then Z." That is what `_meta/log.md` is for, in
  one paragraph.
- **Your own findings about this project.** Research results, benchmarks, things you discovered in
  a repository. These are *evidence*. They belong in a decision's `## Why` with the source named.
  A finding is never a `pattern`. A finding about a **tool** rather than about this project is the
  one exception, and it has its own carrier — see Gate C.
- **Anything already recorded.** Search the vault root first. If a note covers it, extend that
  note or supersede it — do not create a near-duplicate.
- **Restatements of general knowledge.** If it would be true for anyone, it is not this user's
  thinking.

## Writing a good decision note

Sections in this order — reading order, not narrative order. The user reads the decision first.

**`## Decision`** — what was chosen, at most 60 words, in the indicative. This is the section that has
to work on its own.

**`## When to reconsider`** — the conditions under which a different choice becomes correct.
Mirror it into the `revisit` property, concretely enough to recognise later:

- Weak: `"if requirements change"`
- Good: `"if the vault passes 500 notes, or if a work domain with sensitive data is added"`

**`## Why`** — the reasoning. External evidence cited with its source, so that later the user can
separate their own thinking from what was handed to them. This separation is a stated requirement,
not a stylistic preference.

**`## Background`** — enough that it makes sense in two years without this conversation. Name the
constraint that made the choice necessary.

**`## Options weighed`** — the real ones, each with a sentence on why it was plausible. An option
list where every rejected item is obviously bad is a sign the real alternatives were not captured.

**`## The dilemma`** — what made this hard. If nothing was hard, revisit whether Gate A actually
passed.

### The 30-second test

The whole note stays under 400 words, and covers **one** decision. Two choices with two separate
reversal conditions are two notes. A note carrying two cannot be given a verdict: accepting it
accepts both, rejecting it loses the good half, and the two expire on different triggers.

Write one paragraph per line and let the editor wrap it. Frontmatter as block lists, not inline
arrays, because Obsidian rewrites inline arrays the moment the user touches a property.

**An addendum may add evidence; it may never flip the conclusion.** If a later finding changes the
decision, rewrite `## Decision` and move the old text into `## Why` as history — or supersede the
note.

## Writing a gotcha

Four sections, and the last one is the one that earns the note.

**`## What happened`** — the surprise, concretely. The exact command, the exact silence, the exact
wrong output.

**`## Why`** — the mechanism. Not "it is buggy": what the tool is actually doing that makes this
the expected behaviour once you know it.

**`## The workaround`** — what to do instead. If there is nothing to do, say that; a gotcha whose
only advice is "expect it" is still worth having.

**`## What gave it away`** — the symptom, written so that you recognise it next time before you
have diagnosed it. This is the section that turns the note from a diary entry into something that
saves an hour.

### The boundary, which is three-way and easy to blur

- **`pattern`** — the user's own insight. Unchanged, and the gotcha type does not soften it.
  Nothing an assistant or a tool produced becomes a pattern.
- **`gotcha`** — a fact about a tool. True for anyone using it, in any repository.
- **evidence** — a fact about *this* project. Goes in a decision's `## Why` with the source named,
  and gets no note of its own.

"The `.base` filter parses a hyphen as subtraction" is a gotcha. "Our `raw/` frontmatter used
`kept-under`, so two views were silently wrong for weeks" is evidence for the decision that
renamed them. The first is why the second happened; they are not the same note.

## Choosing scope

`domain` is the default.

Propose `universal` when the decision is about **how the user works** — methodology,
architecture, structure — rather than what was built in one project. These stay visible in every
directory, because that layer is exactly what they want available everywhere.

Say which you chose and why. The user approves it; do not decide silently.

**Watch the absolute count, not the ratio.** The first batch was 100% universal and legitimately so
— it was all methodology. The risk is the size of the layer loaded into every session, so the
maintenance run warns above ~15. When in doubt, `domain` — promoting later is cheap.

**A `gotcha` is `universal` and needs no approval for it.** A tool's behaviour is not the property
of one project, and the type is skipped by `resolve.sh`, so it costs nothing in the layer the
warning above is about.

## Titles

Descriptive sentences, not labels.

- Good: `Isolation by binding rather than splitting the vault`
- Good: `Drafting is automatic, canonising is not`
- Bad: `Scoping`, `Vault decision`, `Notes on structure`

## Linking

Every approved note gets:

- links to the decisions or patterns it builds on or contradicts,
- a link to its topic hub, if one exists,
- `related` frontmatter mirroring the important ones.

Contradictions are valuable. If a new note conflicts with an existing one, do not quietly
smooth it over — link them and name the conflict. Either the old decision needs
`status: superseded`, or the tension is real and deserves an `open` note.

## After approval

1. `status: accepted`. **Do not move the file** — `scripts/promote.sh` does that off the SessionStart
   hook, so promotion cannot be forgotten the way it was between 2026-07-26 and 07-28.
2. One paragraph appended to `_meta/log.md`, newest on top.
3. `_meta/hot.md` rewritten: overwrite, 500 words max, verified with `wc -w`. Never append.

There is no index file. The `bases/` views are the catalogue; a hand-written one only goes stale.
