---
name: tenet-capture
description: Capture this session's decisions into the decision ledger, and review drafts waiting in the inbox. Distils what was decided, which options were weighed, and what would reverse the choice. Writes drafts only; a mechanical step promotes them once you have given a verdict.
disable-model-invocation: true
argument-hint: "[review]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(python3 ${CLAUDE_PLUGIN_ROOT}/tenet/cli.py *)
---

# Capture into the decision ledger

Argument: `$ARGUMENTS`. **The ledger's path is printed below** — use it, never an assumed default.
With no ledger yet, the block prints the bootstrap command instead; offer to run it.

```!
python3 ${CLAUDE_PLUGIN_ROOT}/tenet/cli.py inbox
```

The note model — frontmatter, statuses, what earns a note, the section order per type — is in
[conventions](references/conventions.md). Read it before writing or judging a draft.

## Mode 1 — distil this session (no argument)

1. Apply the three gates from the conventions. Most sessions pass none; say so and stop.
2. Write each qualifying note to `inbox/YYYY-MM-DD-short-slug.md` from the matching template in the
   ledger's `templates/`, with `status: proposed` and today's real date in every `{{date}}` slot.
3. Fill `revisit` (decisions) or `resolves` (open questions). Propose `scope` and say why.
4. Show the user what you wrote. Never promote in the same breath as writing.

## Mode 2 — review (`review`, or drafts are pending)

The manual path: drafts are also put to the user automatically, at a session's resting point.
This mode owns `status`; the user answers in their own words and you write a valid value.

1. For each draft show the first two sections verbatim, plus one line on scope and links. If those
   two sections do not make the choice clear, the note failed the 30-second test: offer a rewrite
   instead of asking for a verdict.
2. Ask for accept, reject, unclear, discard or edit. Write `accepted`, `rejected` or `unclear`.
3. Do not move files: `tenet/promote.py` moves reviewed notes at the next session start.
4. On `unclear`, or a rejection on form rather than merit, append an entry to `_meta/retro.md`
   (what deviated, which rule, which error class, what would have caught it).
5. On discard, remove the draft (`git rm` when the ledger tracks it, so git keeps it) and say which one.

## Hard rules

- Write nothing outside `inbox/` (and `_meta/retro.md` in review) without explicit approval here.
- Your findings are evidence for a decision's Why, never a `pattern`.
- Prose and headings in the ledger's language; property names and values in English.
