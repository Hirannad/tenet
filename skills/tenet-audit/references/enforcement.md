# Enforcement table — the format

Every rule in the instruction file gets a row saying what catches it when it is broken, or `none`
and the reason. A rule with no row is itself the defect, and `cli.py audit enforcement` counts them.

Your table lives beside the file it describes, not here: `~/.claude/CLAUDE.md` holds the rules,
`~/.claude/enforcement.md` holds the table (`CLAUDE_MD` and `ENFORCEMENT_TABLE` point elsewhere).
Start one by copying the header below; the check says which rules are still missing.

## Matching

Rows are keyed by the first 40 normalised characters of the rule's line in `CLAUDE.md`:

- **unmarked rule**: a `- ` bullet with no row. The defect.
- **orphan row**: a row whose rule no longer exists. The table went stale.
- **empty cell**: a row with no answer.

Rows prefixed `¶` are prescriptions that are not bullets; they are kept by hand and excluded from
the orphan check.

## The table

| Rule | What catches it |
|---|---|
| Never commit, log, or echo secrets / API keys / tokens | none — no secret scanner runs on `Write`/`Edit` or before a commit. Fully mechanisable, so this is backlog, not a judgement call |

## Three kinds of answer

- **A mechanism**: something fails when the rule breaks. A `permissions.ask`/`deny` pattern, a
  `PreToolUse` hook (blocks regardless of the model), or a check that prints a number.
- **`none`, judgement call**: cannot be mechanised; most rows.
- **`none`, mechanisable, not built**: the backlog. Say so, so it does not read like the row above.

A cell reading `none` alone is worth almost nothing: name what exists, what it does not reach, and
whether the rest is closable. A reasoning habit (stating an unchecked inference as fact) is not a
rule and belongs in the ledger's `_meta/retro.md`, not here.
