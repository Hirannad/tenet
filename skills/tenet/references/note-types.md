# Note types

Five types. Templates live in `templates/` in the vault.

## decision

The core unit, and the reason the vault exists.

```
## Decision              what was chosen — 60 words maximum
## When to reconsider    the conditions that would make a different choice correct
## Why                   the reasoning; external evidence cited with its source
## Background            what the situation was, what forced a choice
## Options weighed       the genuinely viable paths
## The dilemma           the real tension — what made it hard rather than obvious
```

**Reading order, not narrative order.** The decision and its reversal condition come first because
that is what the user reads first; context and options sit at the bottom for when the decision is
not self-explanatory. The whole note is capped at 400 words — see the format rules in
[conventions](conventions.md).

Frontmatter: `revisit` mirrors `## When to reconsider` into a machine-readable condition. That
field is what the weekly sweep watches, and it is what makes deciding differently later possible.

`supersedes` / `superseded` chain decisions that replaced one another. When a decision is
genuinely reversed, do not delete it — set `status: reversed`, link the replacement, and leave
the reasoning intact. The record of a wrong turn is worth as much as the record of a right one.

**A decision needs at least two viable options.** If there was only one path, it was not a
decision, and it does not get a note.

## pattern

A distilled principle that emerged from one or more decisions.

```
## The insight
## Where it holds
## Where it does NOT hold    required
## Where it came from        mirror into `derived`
```

**Only the user's own insight qualifies.** If it came from research, a tool, or an assistant, it
is evidence for a decision, not a pattern. This is the sharpest rule in the system — getting it
wrong fills the vault with borrowed opinions and destroys its value as a record of their thinking.

Defaults to `scope: universal`: a distilled principle crosses project boundaries by nature.

The "Where it does NOT hold" section is mandatory. A pattern without boundaries becomes dogma.

## open

A genuinely unresolved tension, deliberately parked.

```
## The tension
## Why it is parked
## What would close it       mirror into `resolves`
## Interim position
```

Not a to-do. Tasks go in Todoist. This is for questions whose answer is not yet knowable, or not
yet worth the cost of finding out. Deciding not to decide is itself a decision, and the
provisional position keeps that from turning into paralysis.

## source

A pointer to external material. **Its subject is the source's effect on the user's thinking,
never the source's content.**

```
## What I took
## What I did NOT take, and why
## Why raw material is kept (only when it is)
```

If the note reads like a summary of the article, it is redundant with the article — delete it and
keep the link. The second section is often the more valuable one.

Required for every file in `raw/`. Raw material is admitted only when it is not retrievable
elsewhere, or when it is an intermediate work product with no other home. Email, tasks, calendar
and CRM records are never admitted. The admitted file itself carries `type: raw` and an `admission`
property naming which of the two criteria let it in — the rule is enforced by a human reading
`raw/`, and `admission` is what makes each file's justification checkable where it sits.

## gotcha

A tool behaved in a way that surprised you, and will surprise you again.

```
## What happened          the surprise, concretely
## Why                    the mechanism behind it
## The workaround         what to do instead
## What gave it away      the symptom that will recur
```

**A gotcha has no second viable path.** That is what separates it from a decision: nothing was
chosen, a tool simply behaves the way it behaves. If it turns out there *were* two ways, it was a
decision in the wrong carrier — change `type` to `decision` and write the six sections in the same
file. No promotion chain, no extra property.

**Not bound to a repository**, which is the reason this type exists at all. Obsidian having no enum
property type is true in every vault; a hyphen parsing as subtraction is true in every `.base`
file. That knowledge used to live in script comments, where only someone who already knew it could
find it. So `gotcha` defaults to `scope: universal` — the only type that does.

**It carries no `revisit`.** There is nothing to reconsider about a fact.

**It stays out of the session-start list.** `resolve.sh` prints what has already been *decided*, so
a growing reference layer would spend context in every session for something you only need on the
way into the surprise. Where a gotcha actually matters, a decision cites it in `## Why` and brings
the link along — that is the same evidence rule the vault already runs on, with a wikilink instead
of a script comment as the source. In Obsidian it is a normal note: the views and search see it.
