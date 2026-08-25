---
title: tenet repo instructions
type: guide
status: active
updated: 2026-08-24
---

# tenet — repo instructions

The plugin is the machinery; the vault (`~/Claude/brain` by default, a separate repository
with its own lifetime) is the content. `skills/tenet/scripts/lib.sh` is the single source for
both names and the vault path — never hardcode either elsewhere.

## Onboarding

- What the tool is, what it reads outside its own tree, and what it costs to run:
  [README.md](README.md).
- What changed in each release and why: [CHANGELOG.md](CHANGELOG.md), and then the commit body
  behind the version you care about. Those bodies are written as narrative decision records —
  read the one that decided a thing before re-deciding it.
- Live working state (open threads) arrives via the plugin's own SessionStart hook from the
  vault's `hot.md`. This file carries only stable facts, by design.

## Working agreements

- **The version bump is the release.** `claude plugin update` compares `plugin.json`'s version
  field, not commits — a fix that ships without a bump sits in the remote indefinitely while
  the installed copy keeps running the code it fixed. Bump both manifests in the same commit as
  the content they describe; the commit subject carries the version. From 1.0.0 a release also
  carries an annotated tag and a GitHub Release: the manifests are still the ledger the plugin
  manager reads, but a published repository needs a revision a person can check out by name.
  Nothing before 1.0.0 is tagged, and the CHANGELOG is keyed by version rather than by commit
  for the same reason — a version survives a repository move, a hash does not.
- **Before any release or rename**, run `bash skills/tenet/scripts/rename-check.sh`. Seven
  checks, and the seventh is not about renaming at all: it compares `plugin.json` against
  `marketplace.json` on name, version, license and keywords, because two hand-kept copies of
  the same facts with nothing comparing them is the drift class this repo's whole thesis is
  about. The three *descriptions* are deliberately different — different lengths for different
  surfaces — so no check compares them; read them against each other yourself before a release.
  The script only ever greps, but it greps files outside this repository and prints matching
  lines, so don't paste its output anywhere public. And describe a previous name, never spell
  one: the check greps for them, so quoting one in a tracked file would make that file a
  finding of its own.
- **A release that changes `vault-template/bases/` or `vault-template/templates/` needs human
  validation** (owner decision 2026-08-18, narrowed 2026-08-21): bootstrap a throwaway vault,
  open it in Obsidian, and confirm the seven `.base` views show what they claim — before the
  version-bump commit. The 0.4.0 release went through exactly this gate. Prose elsewhere under
  `vault-template/` — `_meta/`, the README, the worked examples — cannot change what a view
  renders, and a gate that fires where it cannot catch anything is a gate people learn to wave
  through. Opening `vault-template/` directly still leaves an `.obsidian/` behind: gitignored,
  and `bootstrap.sh` has stripped it from fresh vaults since 0.4.1, so it is residue rather
  than a hazard.
- **Run the official validator before a release too**, and pass it the *plugin* manifest:
  `claude plugin validate .claude-plugin/plugin.json`. Given the repo root it finds
  `marketplace.json` first, validates only that, and passes — having walked no skill and no
  hook. That difference hid a defect during 0.6.0 for a few minutes: one `": "` in a
  description made the whole frontmatter unparseable, and the skill would have shipped loading
  with no metadata at all. `rename-check.sh` now catches that one cause; the validator catches
  what it does not. The `CLAUDE.md at the plugin root` warning is expected — this file is the
  repo's own instructions, not shipped context.
- **Test scripts against a sandbox, never the live vault.** Pattern:
  `bash skills/tenet/scripts/bootstrap.sh <scratch>/Claude/brain`, then run the other scripts
  with `BRAIN_VAULT` pointing there.
- **No silent zero.** A check that found nothing must be distinguishable from a check that
  looked at nothing (house rule, see the comment at `promote.sh:63`). Apply it to any check you
  add, and to hook wiring too: 0.4.1 closed two violations of exactly this kind — a glob pinned
  to one year, and a hook named after an event that does not exist.
- **Every new `.md` needs `title/type/status/updated` frontmatter** unless a glob in
  `.claude/frontmatter-exempt` covers it. Verify with
  `bash skills/tenet-audit/scripts/frontmatter-check.sh .`

## Language

Everything in this repository is English, commit messages included. The language that varies
belongs to the vault, not here: a vault carries it in `_meta/locale`, and the machinery reads
section headings from there rather than hardcoding any.
