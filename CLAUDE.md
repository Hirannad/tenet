---
title: tenet repo instructions
type: guide
status: active
updated: 2026-08-24
---

# tenet — repo instructions

The plugin is the machinery; the store (`~/Claude/ledger` by default, a separate repository
with its own lifetime) is the content. `skills/tenet/scripts/lib.sh` is the single source for
both names and the store path — never hardcode either elsewhere, and `rename-check.sh` check 8
now enforces that for `hooks/hooks.json` specifically, which cannot source shell and therefore
had carried an unchecked second copy until 2.1.0.

## Onboarding

- What the tool is, what it reads outside its own tree, and what it costs to run:
  [README.md](README.md).
- What changed in each release and why: [CHANGELOG.md](CHANGELOG.md), and then the commit body
  behind the version you care about. Those bodies are written as narrative decision records —
  read the one that decided a thing before re-deciding it.
- Live working state is deliberately **not** here. It arrives from Claude Code's own auto memory
  (`~/.claude/projects/<project>/memory/`), which this plugin stopped duplicating in 2.0.0. This
  file carries only stable facts, by design.

## Working agreements

- **The version bump is the release.** `claude plugin update` compares `plugin.json`'s version
  field, not commits — a fix that ships without a bump sits in the remote indefinitely while
  the installed copy keeps running the code it fixed. Bump both manifests in the same commit as
  the content they describe; the commit subject carries the version. From 1.0.0 a release also
  carries an annotated tag and a GitHub Release: the manifests are still the ledger the plugin
  manager reads, but a published repository needs a revision a person can check out by name.
  Nothing before 1.0.0 is tagged, and the CHANGELOG is keyed by version rather than by commit
  for the same reason — a version survives a repository move, a hash does not.
- **Create the tag with `claude plugin tag --push`**, from 2.0.0 on. It refuses on a dirty tree,
  writes the annotation, and pushes. The naming convention changed with it: `v1.0.0` was made by
  hand, everything from `tenet--v2.0.0` is the harness's format, so the tag list is mixed by
  design and the CHANGELOG says where the seam is.
  **It does not replace `rename-check.sh` check 7**, and this was measured rather than assumed
  (2026-08-26, sandbox clone, one field broken at a time): the native command validates the
  **version** field only. A `name`, `license` or `keywords` mismatch between the two manifests
  passes it clean and would have been tagged. Check 7 covers all four, so it is a superset on
  three of them — run both, and do not delete the check on the assumption that the platform now
  owns it.
- **Before any release or rename**, run `bash skills/tenet/scripts/rename-check.sh`. Eight
  checks, and the last two are not about renaming at all. The seventh compares `plugin.json`
  against `marketplace.json` on name, version, license and keywords, and the eighth fails if
  `hooks/hooks.json` resolves a store path of its own — both because two hand-kept copies of
  the same facts with nothing comparing them is the drift class this repo's whole thesis is
  about. (This paragraph said *seven* from 1.0.0 until 2026-08-28, while the eighth check
  shipped in 2.1.0 and both the script header and the README counted it. An off-by-one in the
  release-gate instructions, which is the worst place for one.) The three *descriptions* are
  deliberately different — different lengths for different surfaces — so no check compares them;
  read them against each other yourself before a release.
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
  `bash skills/tenet/scripts/bootstrap.sh <scratch>/Claude/ledger`, then run the other scripts
  with `TENET_LEDGER` pointing there.
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
