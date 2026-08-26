---
name: tenet-sweep
description: Weekly housekeeping for the decision brain. Sweeps for decisions whose reversal condition may now be met, plus dead links, orphans, stale drafts, unjustified raw files and an over-grown universal layer, then writes a short digest and proposes fixes without applying them. Use when the user asks for the weekly sweep or vault maintenance, wants to look through or tidy up their own decision notes, asks which recorded conditions may have fired since the last pass, or when a session-start notice says maintenance is overdue. It reviews the notes as a set; it does not search them for a fact.
allowed-tools: Read, Write, Edit, Grep, Glob
---

# Brain maintenance

Vault: `~/Claude/brain` (override with `BRAIN_VAULT`).

Nothing in this plugin schedules this run. What ships instead is the nag: `promote.sh` reports
at every session start when the last digest is over a week old, so a forgotten sweep says so
rather than going quiet. Wire it to a real scheduler yourself if you want one. **It proposes;
it does not decide.** The only thing it may write on its own is the digest note. Everything
else is a suggestion for the user.

```!
"${CLAUDE_PLUGIN_ROOT}/skills/tenet-sweep/scripts/inventory.sh"
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
6. **Universal layer growth.** If there are more than ~15 `universal` notes, say so. An
   unchecked universal layer recreates the leakage that scoping exists to prevent.
7. **Pattern candidates.** Three or more decisions sharing a rationale suggest an undistilled
   principle. **Propose it as a question, never write the pattern.** A pattern must be the
   user's own insight; drafting one on their behalf breaks the rule the whole vault rests on.
8. **Topic candidates.** Five or more notes sharing a category with no hub note suggest a topic
   worth promoting. Propose the hub and the binding line.
9. **Repeated process deviations.** Read the `feedback` entries from Claude Code's auto memory
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

There is no index file to maintain: the `bases/` views are the catalogue, and a hand-written one
would only go stale.

## What this must never do

- Change a decision's `status`. Reversing a decision is the user's call.
- Write a `pattern`. Propose; never author.
- Delete anything. Propose deletions in the digest.
- Move notes out of `inbox/`. The `tenet` skill's `scripts/promote.sh` owns that, off the
  SessionStart hook — a reviewed note reaches the vault root without anyone remembering to run it.
- Touch anything in `raw/`.
