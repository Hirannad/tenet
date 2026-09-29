# Layer map

## Load order

Root-most first. Every file is concatenated into context, none replaces another: a "project
override" works only because the later text is read later and says so.

```
1. Managed policy CLAUDE.md      macOS: /Library/Application Support/ClaudeCode/CLAUDE.md
                                 Linux: /etc/claude-code/CLAUDE.md
                                 or the `claudeMd` key in managed-settings.json; cannot be excluded
2. ~/.claude/CLAUDE.md           user, personal; every project inherits it
   ~/.claude/rules/*.md          user rules; load before project rules
3. <repo>/CLAUDE.md              project, team; committed
   or <repo>/.claude/CLAUDE.md   the same layer
   <repo>/.claude/rules/**.md    project rules; without `paths:` they load at launch
4. <repo>/CLAUDE.local.md        machine-local, gitignored; appended after CLAUDE.md
```

On demand rather than at launch: `CLAUDE.md` files in subdirectories below the working directory,
and rules with `paths:` frontmatter. Both arrive when Claude reads a matching file. `AGENTS.md` is
not a layer: Claude Code reads it only through an `@AGENTS.md` import (or a symlink).

`/context` lists what actually loaded; `claudeMdExcludes` (any settings layer, arrays merge) is why
a present file can still never load.

## What belongs where

| Layer | Belongs | Does not belong |
| :-- | :-- | :-- |
| managed policy | org-wide standards IT must guarantee | anything a team should be able to turn off |
| `~/.claude/CLAUDE.md` | personal preferences, autonomy, style | project commands, repo structure |
| `~/.claude/rules/` | personal rules split by topic or path | anything a teammate needs |
| `<repo>/CLAUDE.md` | stack, commands, structure, conventions, guardrails | personal preferences, secrets, machine paths |
| `<repo>/.claude/rules/` | topic- and path-scoped project rules | rules for every file (keep those in CLAUDE.md) |
| `CLAUDE.local.md` | local ports, machine env, personal scratch | anything the team needs |

## Imports versus path-scoped rules

An `@`-import expands at launch (up to four hops) and costs the same context inline: it is the
answer to duplication, never to length. A `paths:` rule is what defers the cost. In a project file,
an import that resolves outside the working directory asks the user for approval once; declining
disables it silently.

## Cross-layer findings

1. **Duplication**: the same rule in two layers. Keep it in the most general correct layer.
   `cli.py audit layers` clusters exact matches after normalisation; a paraphrase escapes it.
2. **Undeclared override**: a contradiction with no flag leaves two live rules. The script lists
   pairs that differ only by a negation as candidates; a contradiction with no shared wording is
   invisible to it, and its output says so.
3. **Misplaced content**: personal preference in a team file, a team rule in `CLAUDE.local.md`, a
   secret or machine path committed (also a leak).
4. **Situational content** that should be a `paths:` rule.
5. **An unexamined layer**: rules directories and managed policy are the most often missed; report
   them as unexamined, never as clean.
6. **Instructions duplicating auto memory**: the script includes the memory tree in the
   duplication scan (not in the budget, which the harness meters separately); `--no-memory` skips it.
