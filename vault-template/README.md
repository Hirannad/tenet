---
type: meta
title: The vault
---

# The vault

A directory of markdown files. That is the whole storage format — there is no database, no index
file, and nothing that breaks if you edit a note in any other editor.

`tenet` reads this directory; the two are separate on purpose, with separate lifetimes. Point the
plugin somewhere else with `BRAIN_VAULT`.

## Layout

| Where | What |
|---|---|
| root | Knowledge notes, flat. `YYYY-MM-DD-short-slug.md` |
| `inbox/` | Drafts awaiting your review. **Empty is the healthy state** — `promote.sh` empties it as soon as a draft gets a status |
| `_meta/` | The vault's own bookkeeping: bindings, statuses, the hot cache, the log, the retro |
| `templates/` | One per note type |
| `bases/` | Saved views over the notes — the catalogue. There is no index file, because a hand-written one goes stale. Obsidian reads these; without it they are inert YAML and nothing else changes |
| `raw/` | Source material that could not be linked instead of copied. Every file here needs a `source` note saying why |

No folders for organising knowledge. Categories are frontmatter, and nothing queries a directory
name.

Two dotfiles ship with the vault and matter the first time you run anything over it: `.gitignore`
keeps Obsidian's churn out of the history, and `.claude/frontmatter-exempt` tells the instruction
auditor that this repository runs the vault schema on purpose — without it, an audit reports every
note here as a defect.

## Note types

Five, and the boundary between them is what keeps a brain from becoming a pile.

- **decision** — the core unit. Context, options, dilemma, choice, why, and what would reverse it.
- **pattern** — a distilled principle. **Only your own insight qualifies.** Findings handed to you
  by research or an assistant are evidence inside a decision, never patterns.
- **open** — a parked dilemma, with what would settle it. Not a to-do.
- **source** — a pointer. Its subject is the source's *effect* on your thinking, never its content.
- **gotcha** — a tool behaved in a way nobody would predict, and will again. No second viable path;
  if there was a choice, it is a decision instead.

`meta` and `raw` also appear as `type` values, but they mark machinery rather than knowledge: the
files in `_meta/`, and material kept in `raw/`.

## Admission rule for raw material

Something may be copied into `raw/` only if **at least one** is true:

1. it is **not retrievable elsewhere** (non-public, offline, may disappear), or
2. it is an **intermediate work product** supporting a decision, with no other home.

Every file in `raw/` needs a companion `source` note explaining why it is kept, and an `admission`
property recording which of the two criteria admitted it. Files without a companion note get
flagged by the weekly sweep.

**Never admitted:** email, tasks, calendar entries, CRM records, chat logs. Those live in their own
systems — this vault belongs to thinking. Link out, do not mirror.

## The three notes already here

They are examples, and they are not yours. Read them once to see the shape — a decision, its
reversal condition, the options that were real — then delete them. Two are `scope: universal` and
show up everywhere; the third is `scope: domain` and stays invisible until a directory is bound to
it in `_meta/bindings.md`. That contrast is the thing worth seeing before you delete them.

## Language

Notes are prose, and prose has a language. Section headings come from the plugin's locale: English
by default, and `_meta/locale` holding one word switches it (`hu` ships as a worked example). The
60-word cap matches on the heading, so changing the headings without changing the locale means the
check silently stops finding them.

**Switching the locale is two steps, not one.** The locale tells the *checks* which heading to look
for; it does not rewrite `templates/`, which arrive in English and get copied verbatim. So after
setting `_meta/locale`, translate the headings inside your `templates/` files once — leaving the
filenames as `* Template.md`, because every saved view excludes templates by filename. Skip that
step and notes written from the templates carry headings the checks are no longer looking for.

Frontmatter keys stay English, and so does every value a script compares against — `type`,
`status`, `scope`. Free-text properties like `revisit` follow the vault's language: nothing matches
on their contents.

## Where the rules live

Conventions, note types and the hot-cache limits are documented in the `tenet` skill's
`references/`, not here — that way they travel with the machinery that enforces them rather than
with the content.
