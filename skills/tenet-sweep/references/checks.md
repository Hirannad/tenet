# Maintenance checks

Eight checks. Each says what to look for, and what the report line should say.

## 1. Revisit sweep

**The reason this job exists.** For every decision with a non-empty `revisit`, read the
condition and judge whether it may now be met — using what you can actually observe: the state
of the vault, the filesystem, the repositories, elapsed time.

Report only plausible triggers. A false alarm every week trains the user to ignore the digest.

Format:

```
- [[Decision title]] — decided YYYY-MM-DD
  Condition: <the revisit field verbatim>
  Why it may now apply: <what you observed>
  Original reasoning: <one or two sentences quoted from ## Why>
```

**Never change `status`.** Reversing a decision is the user's call; you surface the trigger.

Some conditions are about the vault's own shape, and the inventory dump carries the number they
need — `Gotchas:` is there because the gotcha type reverses itself below three in half a year, and
before that line nothing could observe it. When a condition names a quantity, read it off the
inventory rather than estimating.

## 2. Stale drafts

Files in `inbox/` older than 14 days. List them with age and first heading. Two honest options:
review them, or discard them. A draft that has sat for a month is usually telling you it did not
matter.

## 3. Dead links

Wikilinks whose target does not exist in the vault root. Distinguish two cases:

- **Typo or rename** — propose the correction.
- **Deliberate forward link** — a note referenced before it was written. Legitimate; list
  separately as "not yet written" rather than as breakage.

## 4. Orphans

Notes with no inbound and no outbound links. Usually means the note was written in isolation and
never connected. Propose two or three plausible links rather than just flagging it.

## 5. Unjustified raw files

Every file in `raw/` needs a `source` note whose `kept` property points at it. Files without one
violate the admission rule and should be either justified or removed.

Restate the rule when reporting: raw material is admitted only when it is **not retrievable
elsewhere**, or when it is an **intermediate work product** with no other home.

## 6. Pattern candidates

Three or more decisions sharing a rationale suggest an undistilled principle. The inventory's
`pattern candidates` section lists the groups it found (a `related` link plus text overlap, 3-8
members) with their shared terms; judge each one and word the question. A group is a lead, not a
finding: drop one that is only a shared topic. The observer separately drafts a pattern when the
user's own quote exists; that draft arrives in `inbox/`, so do not write one here.

**Propose it as a question. Never write the pattern.**

```
- These decisions share a rationale: [[A]], [[B]], [[C]]
  The common thread looks like: <one sentence>
  Is there a principle here you would state in your own words?
```

A pattern records the user's own insight. Authoring one for them — however well — replaces their
thinking with yours, which is precisely what this vault exists to prevent.

## 7. Topic candidates

Five or more notes sharing a `categories` value with no hub note. Propose:

- a hub note named **exactly** after the category — `Methods.md` in the vault root, with
  `type: meta`. The name is not cosmetic: the dead-link check resolves `[[Methods]]`
  against `./Methods.md`, `_meta/Methods.md` and `inbox/Methods.md` and nowhere else, so an
  `_index` suffix, a date prefix or a `hubs/` folder all leave the link dead forever. `type: meta`
  keeps it out of the brief, which lists decisions, patterns, gotchas and open questions only.

Hubs carry the category's meaning and its boundary against neighbouring categories. They do **not**
list the notes: a hand-written index goes stale. Being
undated, a hub is invisible to the type/status and word-cap loops in the inventory — deliberate, as
it is bookkeeping rather than knowledge.

Topics are meant to emerge from accumulated material rather than be designed up front. This
check is how that happens. It is a proposal — the user approves the promotion.

## 8. Repeated process deviations

Corrections are no longer collected here. Claude Code's own auto memory records them as `feedback`
notes, and duplicating that was the redundancy 2.0.0 removed. This check reads them and does the
part the platform does not: turns a repeat into a verdict.

The inventory dumps the `feedback` entries it found. It does **not** dump `_meta/retro.md`: read
that yourself with `Read`. It is the log of judgements and the error-class table, and the second
axis of this count.

Count **two ways**: by the rule or convention named, and by error class. Two or more on either
axis means the rule is not working — writing it down was not enough.

**Read the dump's own status line first.** A missing memory directory, a relocated one, or auto
memory switched off all produce *no entries*, and none of them mean *no deviations*. If the dump
says it could not read the record, report that as the finding and stop — do not report a clean
sweep on a record you never opened.

Counting by class matters because the same habit surfaces on different rules. Three entries naming
three different conventions can still be one mistake repeated, and per-rule counting hides it.

Report the repeat, then propose **one of exactly two outcomes**:

- **A mechanism that fails when the rule is broken** — a hook, a script, a permission rule, a schema
  check. Prefer what the harness already ships over anything written from scratch.
- **Deleting the rule.** A rule that keeps being broken and cannot be mechanised is costing context
  and buying nothing.

There is no third option. Restating it more emphatically is what produced the repeat in the first
place — do not propose it.

Draft the change as a `decision` in `inbox/`, so it reaches the user the way any other decision does.
**One draft per maintenance run**, for the most-repeated rule or class only.

## Writing the digest

Order: revisit sweep first, then anything actionable, then everything clean in one line.

Be brief. A clean week should produce a two-line digest, and that is a good outcome — not a
reason to manufacture findings.
