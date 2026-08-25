---
type: meta
title: Bindings
---

# Bindings

This file is the gate. It maps a directory on disk to the topics that are relevant there.

**It is empty on purpose.** With no bindings, working in any directory pulls in nothing
topic-specific — only `scope: universal` notes are ever in scope. Add a line here the moment a
project starts accumulating knowledge worth recalling.

## Format

One line per binding. The longest matching path prefix wins, so a binding for a package inside a
repository beats a binding for the repository root.

```
- `/absolute/path` → [[Topic A]], [[Topic B]]
```

`~` is expanded, so `` `~/code/foo` `` also works.

## Active bindings

<!-- Add bindings below this line. Example, remove when adding a real one:
- `~/code/acme-api` → [[Acme]], [[Billing]]
-->

## What is NOT controlled here

Methodology, architecture and structure decisions carry `scope: universal` in their own
frontmatter and are visible everywhere, regardless of what this file says. That is deliberate:
how you work is not the property of one project. See `note-types.md` in the `tenet` skill
references.
