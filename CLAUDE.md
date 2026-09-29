---
title: tenet repo instructions
type: guide
status: active
updated: 2026-09-27
---

# tenet — repo instructions

The plugin is the machinery; the ledger (`~/Claude/ledger` by default, its own repository) is the
content. `tenet/paths.py` is the only place that resolves the ledger path. `hooks/hooks.json`
calls `tenet/cli.py` and names no path of its own, and CI fails if it ever does.

## Layout

- `tenet/`: Python 3.9, stdlib only (macOS ships 3.9). `tenet/cli.py` is the single entry point for
  hooks and skills; a new capability is a subcommand, not a new script. `tenet/observer/` reads
  transcripts out of band; the session-start hook only reads what it wrote, and must stay fast.
- `tenet/audit/`: the instruction-layer checks behind `cli.py audit`.
- `vault-template/`: what `cli.py bootstrap` copies into a new ledger.
- `tests/`: `python3 -m unittest discover -s tests -t .`

## Working agreements

- **The version bump is the release.** `claude plugin update` compares `plugin.json`'s version,
  the only copy of it (the marketplace entry carries none). Bump it in the commit it describes, with
  the version in the subject, and add one line to the CHANGELOG.
- **Release steps:** tests green; `claude plugin validate .claude-plugin/plugin.json` (the plugin
  manifest: given the repo root it validates only the marketplace; the plugin-root CLAUDE.md warning
  is expected); `claude plugin tag --push`; then `git push origin main`, because the tag command
  pushes the tag and not the branch. Done when `git status -sb` shows no `ahead`.
- **Test against a sandbox ledger, never the live one:** `python3 tenet/cli.py bootstrap
  <scratch>/ledger`, then run commands with `TENET_LEDGER` pointing there.
- **No silent zero.** A check that found nothing must print differently from one that looked at
  nothing. Test every check in the failing direction too.
- Comments say why, in a line or two. History belongs in git and the CHANGELOG, not in the code.
- Every new `.md` carries `title/type/status/updated` frontmatter unless `.claude/frontmatter-exempt`
  covers it (`python3 tenet/cli.py audit frontmatter .`).
- With the working directory inside this repo the plugin loads twice (cache and tree), so hooks
  fire twice and every measured figure doubles.
- Everything in this repository is English. The ledger carries its own language in its templates.
