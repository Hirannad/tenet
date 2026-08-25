# Enforcement — the format

Every rule in your instruction file gets a row saying **what catches it when it is broken** — or
`none` and the reason. **A rule missing its row is itself the defect**, and
`scripts/enforcement-check.sh` counts those, so the silence is a number rather than an assumption.

This is the vault's own convention table applied one layer up. Vault conventions have carried an
enforcement column for a while; the instruction layer never got one, and the instruction layer is
where the recurring session-level mistakes come from.

`none` is a legitimate answer, and in practice most rows say it. Judgement calls cannot be
mechanised, and a rule does not become invalid by resisting automation. What the table removes is
the third state — a rule nobody ever asked the enforcement question about.

## Where your table lives

Not here. This file is the format; your rules are data, and data belongs beside the file it
describes:

```
~/.claude/CLAUDE.md        the rules
~/.claude/enforcement.md   what catches each one
```

`enforcement-check.sh` reads that pair by default. Point it elsewhere with `CLAUDE_MD` and
`ENFORCEMENT_TABLE` if your instruction file lives somewhere else. Create `~/.claude/enforcement.md`
by copying the two headings below and adding one row per rule; the check tells you which rules are
still missing, so you can grow it a few rows at a time rather than in one sitting.

## How the rows are matched

Rows are keyed by the first 40 normalised characters of the rule's own line in `CLAUDE.md`, so the
check is a set comparison, not a hand-maintained list:

- **unmarked rule** — a `- ` bullet in `CLAUDE.md` with no row here. This is the defect.
- **orphan row** — a row here whose rule no longer exists in `CLAUDE.md`. The table went stale.
- **empty cell** — a row with no answer in the second column.

Rows prefixed `¶` are prescriptions that are not bullets (prose instructions, a frontmatter block,
the layer order). They are maintained by hand and excluded from the orphan check.

## The table

| Rule | What catches it |
|---|---|
| Never commit, log, or echo secrets / API keys / tokens | none — the deny list covers `sudo` and curl-pipe-bash only. No secret scanner runs on `Write`/`Edit` or before a commit. **The highest-severity gap in this table**, because unlike the judgement calls it is fully mechanisable |

One row, kept as the worked example, because it shows what a good cell does: it names the mechanism
that exists, names what that mechanism does *not* reach, and says whether the gap is closable. A
cell reading `none` alone is worth almost nothing; `none` plus the reason is the whole point.

Three shapes of answer are worth distinguishing, and the example is the third:

- **A real mechanism** — `settings.json` → `permissions.ask` on `Edit(**/package.json)`. Something
  fails when the rule is broken.
- **`none` — judgement call.** Cannot be mechanised and does not need to be. Most rows.
- **`none` — mechanisable, not yet built.** The interesting ones. These are the backlog, and
  writing the reason down is what keeps them from reading like the row above.

## What a table like this does not cover

Not every recurring mistake is a rule violation. A reasoning habit — stating an unchecked inference
as fact — has no rule to mark, and adding one would make the file longer without making it more
enforceable, which is the failure mode the table exists to prevent.

Keep those in a separate record of process deviations (the vault's `_meta/retro.md`), classified,
so that a repeat becomes visible as a count. A rule and a habit both need catching; only one of
them belongs in this table.
