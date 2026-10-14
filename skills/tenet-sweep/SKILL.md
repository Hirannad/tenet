---
name: tenet-sweep
description: Weekly housekeeping for the decision ledger. Sweeps for decisions whose reversal condition may now be met, plus dead links, orphans, stale drafts, and unjustified raw files, then writes a short digest and proposes fixes without applying them. Use when the user asks for the weekly sweep or vault maintenance, wants to look through or tidy up their own decision notes, asks which recorded conditions may have fired since the last pass, or when a session-start notice says maintenance is overdue. It reviews the notes as a set; it does not search them for a fact.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(python3 ${CLAUDE_PLUGIN_ROOT}/tenet/cli.py *)
---

# Ledger maintenance

**The ledger's path is printed by the block below** — use that, never an assumed default.

Nothing in this plugin schedules this run. What ships instead is the nag: `tenet/promote.py`
reports at every session start when the last digest is over a week old. That line is all it does,
and nothing notices when it is ignored; wire the sweep to a real scheduler if it must run. **It proposes;
it does not decide.** The only thing it may write on its own is the digest note. Everything
else is a suggestion for the user.

```!
python3 ${CLAUDE_PLUGIN_ROOT}/tenet/cli.py sweep
```

**Work from that dump, and use `Read` / `Grep` / `Glob` for anything it does not cover — do not
compose shell.** The inventory runs from the block above without prompting; an ad-hoc command is
a fresh permission decision, and in an unattended run there is nobody there to answer it. If the
dump is missing something you need every week, add it to the script rather than working around it.

## The checks

Run all of them, then write the digest. Detail for each is in
[the check list](references/checks.md).

1. **Revisit sweep — the important one.** For each decision with a `revisit` condition, judge
   whether it may now be met. Report the ones that plausibly have, with the original reasoning
   quoted. Do not change any decision.
2. **Stale drafts.** Drafts sitting in `inbox/` for more than 14 days. Either they matter and
   need review, or they should be discarded.
3. **Dead links.** Wikilinks pointing at notes that do not exist.
4. **Orphans.** Notes nothing links to and which link to nothing.
5. **Unjustified raw files.** Files in `raw/` with no companion `source` note explaining why
   they are kept.
6. **Pattern candidates.** Three or more decisions sharing a rationale suggest an undistilled
   principle. **Propose it as a question, never write the pattern.** A pattern must rest on the
   user's own words; drafting one without them breaks the rule the whole vault rests on.
7. **Topic candidates.** Five or more notes sharing a category with no hub note suggest a topic
   worth promoting. Propose the hub note.
8. **Repeated process deviations.** Read the `feedback` entries from Claude Code's auto memory
    (the inventory dumps them) together with `_meta/retro.md`. If two or more name the same
    convention **or the same error class**, it is not working — writing it down was not enough.
    If the dump says it could not read the record, that is the finding; no entries is not no
    deviations.
    Propose one of exactly two outcomes: a mechanism that fails when the rule is broken, or deleting
    the rule. Draft it as a `decision` in `inbox/`, so it reaches the user the same way any other
    decision does. One draft per maintenance run, for the most-repeated rule or class only.

## The digest

Write to `_meta/maintenance-YYYY-MM-DD.md` with `type: meta`. Keep it short — findings and
proposals, no prose padding. Lead with the revisit sweep; that is what the user is here for.

If everything is clean, say so in two lines. A digest that manufactures work to look useful is
worse than a short one.

**Every proposal and question that waits on the user also goes into the frontmatter** as an `open:`
list, so a session-start hook can keep asking until each has a verdict; prose alone is where they
die. One JSON object per line, which is valid YAML:

```yaml
open:
  - {"id": "sweep-hub-invoice-email", "question": "Legyen hub az Invoice Email témának?", "options": ["Igen, a rootban", "Még ne"], "recommended": "Igen, a rootban"}
```

`id` is `sweep-` plus a slug that stays the same across runs; `question` is one line that stands
without the digest, in the digest's language; 2–4 `options`, one of them `recommended`. Inbox
drafts are not items: the inbox already brings them back. Never write `verdict` or `decided`;
those are the user's answer, written back by whatever closes the items.

Before writing, read the previous digest's `open:`. Copy every item without a `verdict` into this
one under the same id, unless this run's evidence settled it; then leave it out and say why in one
line. An item with a `verdict` is decided: if the change it approved is not visible in the ledger
yet, report that as a finding, not as a new item.

There is no index file to maintain; a hand-written one would only go stale.

## What this must never do

- Change a decision's `status`. Reversing a decision is the user's call.
- Write a `pattern`. Propose; never author.
- Delete anything. Propose deletions in the digest.
- Move notes out of `inbox/`. `tenet/promote.py` owns that, off the SessionStart hook.
- Touch anything in `raw/`.
