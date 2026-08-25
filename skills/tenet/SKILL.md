---
name: tenet
description: Consult the decision brain — a personal journal of architectural, structural and methodological decisions, the reasoning behind them, and the conditions that would reverse them. Use before making or revisiting a design, architecture, tooling or process decision; when the user asks what was decided before, why something is the way it is, or whether a similar problem has already been reasoned through; and when a past decision may need reconsidering. Only surfaces what is in scope for the current directory.
allowed-tools: Read, Grep, Glob
---

# The decision brain

A vault at `~/Claude/brain` (override with `BRAIN_VAULT`) that records **how decisions were
made**: the situation, the viable options, the dilemma, the choice, the reasoning, and what
would reverse it. It is not a source archive and not a task list.

## What is in scope right now

The block below was resolved before you saw this message. It already accounts for scoping —
do not try to widen it by searching the vault for unrelated notes.

```!
"${CLAUDE_PLUGIN_ROOT}/skills/tenet/scripts/resolve.sh" --interactive
```

**If that block is empty, the brain has nothing in scope for this directory.** Say so plainly
and answer from your own knowledge. Do not go hunting through the vault, and do not invent
notes that were not listed.

**If the block says there is no vault yet, relay its bootstrap command verbatim** — that is
the user's install path, resolved for this machine and plugin version.

## How scope works

Two levels, set per note in the `scope` property:

- **`universal`** — methodology, architecture and structure decisions. In scope in *every*
  directory, because how the user works is not the property of one project.
- **`domain`** — in scope only when the working directory is bound to a matching topic in
  `_meta/bindings.md`.

Bindings gate what *you* load. They hide nothing from the user inside Obsidian.

## Answering

1. **Start from the list above.** It gives titles, types and revisit conditions — enough to
   choose what is worth opening.
2. **Read only the notes you actually need**, by path in the vault root.
3. **Always cite.** Reference notes as `[[Note title]]`. If the brain contains the answer,
   answer from the brain, not from general knowledge — and make clear which you are doing.
4. **Surface stale decisions.** If a note's `revisit` condition looks like it may now be met,
   say so. That is the single most valuable thing this system does.
5. **Never edit the vault from this skill.** Writing is `/tenet:tenet-capture`, and it needs the
   user's approval. This skill is read-only.

## When the user is about to decide something

Check whether they have decided it before. If they have and are now leaning the other way,
that is worth naming explicitly: quote the earlier reasoning and ask whether the reversal
condition has actually been met, or whether the earlier reasoning still holds.

## References

- [Conventions](references/conventions.md) — frontmatter, naming, dates, categories.
- [Note types](references/note-types.md) — the five types and when each applies.
- [Hot cache rules](references/hot-cache.md) — the hard limits on `_meta/hot.md`.

## Related skills

- `/tenet:tenet-capture` — turn a session's decisions into notes, and review pending drafts.
- `/tenet:tenet-sweep` — the weekly housekeeping and revisit sweep.
- `obsidian-markdown`, `obsidian-bases` — file format reference for the vault.
