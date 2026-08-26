---
name: tenet-capture
description: Capture this session's decisions into the decision brain, and review drafts waiting in the inbox. Distils what was decided, which options were weighed, what the dilemma was, and what would reverse the choice — then promotes approved drafts into the vault.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Grep, Glob
---

# Capture into the decision brain

Vault: `~/Claude/brain` (override with `BRAIN_VAULT`). Argument: `$ARGUMENTS`

Two modes. Pick based on the argument, or on what is actually pending.

- **`review`**, or anything in `inbox/` — go through pending drafts with the user.
- **anything else / no argument** — distil the current conversation into new drafts.

```!
"${CLAUDE_PLUGIN_ROOT}/skills/tenet-capture/scripts/inbox.sh"
```

## Mode 1 — distil this session

Apply **all three gates**. Something qualifies if any is true:

- **A real decision.** At least two genuinely viable paths existed and one was chosen for a
  reason. One path is not a decision.
- **An insight the user reached.** Their own formulation, stated by them.
- **A tool that surprised you and will again.** Not specific to this repository, and with no
  second viable path — that is a `gotcha`. If there was a choice, it is a decision instead.

Then:

1. **Draft, do not publish.** Write to `inbox/YYYY-MM-DD-short-slug.md` with `status: proposed`,
   using the matching template from `templates/`. Write today's real date into every
   `{{date:…}}` placeholder it carries — Obsidian expands those for a human, nothing expands
   them for you, and `bases/Inbox.base` sorts by `created`.
2. **Show the user what you wrote** and ask for approval. Never move a draft into the vault root
   in the same breath as writing it.
3. Fill `revisit` (decisions) or `resolves` (open questions). A decision with no reversal
   condition is half-recorded — that field is the entire point of the system.
4. Propose `scope`. Default `domain`; propose `universal` only when the decision is about *how
   to work* rather than *what was built*. Say which you chose and why, so the user can correct it.
   A `gotcha` is always `universal` and needs no proposal — `resolve.sh` skips the type, so it
   never reaches the session-start list.

See [the capture procedure](references/capture.md) for the detailed rules, including what does
**not** deserve a note.

## Mode 2 — review pending drafts

**This mode owns the `status` field.** The user must not have to type into the YAML: Obsidian has
no enum property type, so `status` is a free text box with no dropdown and no tooltip — which is how
invented values get into a vault. You show the note, they answer in whatever words they like, you
write a valid one.

For each draft in `inbox/`:

1. **Show the decision, not the file.** `## Decision` and `## When to reconsider` verbatim, plus
   one line each for scope and what it links to. Nothing else unless they ask. If those two sections
   do not make the choice clear on their own, the note has failed the 30-second test — say so, and
   offer to rewrite it rather than asking for a verdict on something unreadable.
2. **Ask for one of:** accept, reject, unclear, discard, or edit.
3. **Write the status** — `accepted`, `rejected` or `unclear`. See the status table in the `tenet`
   skill's [conventions](../tenet/references/conventions.md). `rejected` keeps the note: a
   weighed-and-turned-down choice is still worth having in writing. `unclear` means the *note*
   failed, not the idea — leave it in `inbox/` and rewrite or split it.
4. **Do not move the file.** `scripts/promote.sh` moves reviewed notes to the vault root off the
   SessionStart hook. Nothing here has to remember it.
5. On `accepted`: rename to a descriptive title if the slug is terse, add wikilinks to related notes
   and to the topic hub if one exists, then append **one paragraph** to `_meta/log.md`, newest on
   top.
6. **On `unclear` or `rejected`-for-form, append a retro entry** to `_meta/retro.md` — what deviated,
   which convention it touched, which error class it falls into, and what would have caught it. That
   file is the process's own record, and the maintenance run reads it for repeats. A note rejected on
   its *merits* is normal operation and gets no entry. The full intake rule — which also covers any
   rule the user had to enforce by hand, not just the Brain's own — lives in that file's header.

**On discard:** delete the draft. Say what was discarded so it is not silently lost.

## Hard rules

- **Never write outside `inbox/` without explicit approval in this conversation.** Approval for
  one draft is not approval for the next.
- **Your findings are evidence, not insight.** Anything you discovered through research or
  tooling goes in a decision's `## Why` section with its source named. It never becomes a
  `pattern`. Patterns record what the *user* worked out.
- **Prose and headings in the vault's language**, matching the existing notes; property names and
  values in English.
- **The 30-second test is a hard gate**, not advice: `## Decision` under 60 words, note under 400,
  one decision per note, one paragraph per line, no hand-wrapped prose.
- **Never put email, tasks, calendar entries, CRM records or chat logs into the vault.** They
  live in their own systems; link out instead.
- Raw material enters `raw/` only under the admission rule, and always with a companion `source`
  note explaining why it is kept.
