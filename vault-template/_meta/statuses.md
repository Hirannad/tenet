---
type: meta
title: Statuses
---

# Statuses

Seven values on one axis: **where the note stands in the review loop.** The same list applies to
every type — type-specific meaning is carried by `revisit` and `resolves`, not by `status`.

| Status | What it means | What happens to the note |
|---|---|---|
| `proposed` | A draft. Not part of the vault yet. | Stays in `inbox/` |
| `unclear` | You could not judge it. This is not a rejection — the *note* failed, not the idea. | Stays in `inbox/`; needs a rewrite or a split |
| `accepted` | Approved. This is what you work by. | `promote.sh` moves it to the vault root |
| `rejected` | Weighed and turned down before it ever took effect. **Kept** — the reasoning is still worth having. | Vault root; drops out of the revisit sweep |
| `superseded` | A later note replaced it. Link the replacement in `superseded`. | Vault root; drops out of the revisit sweep |
| `reversed` | It was live, then undone. Its `revisit` condition fired. | Vault root; drops out of the revisit sweep |
| `resolved` | An open question that got settled. | Vault root |

`rejected` and `reversed` are not the same: `rejected` never took effect, `reversed` did and was
then withdrawn. That is exactly why both are worth keeping.

## You do not type this by hand

`/tenet:tenet-capture review` writes the status: you get the draft in short form, you answer,
the agent writes the YAML. If you do type one by hand and it is not on this list, `promote.sh`
says so at the next session start and the note stays in `inbox/`.

Obsidian has no enum property type, so `status` renders as a free-text field with no dropdown. That
is how invented values get in. The check is the guard, not the editor.
