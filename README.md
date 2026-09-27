# tenet

A decision ledger that comes back to you when its assumptions expire, and an audit of the
instruction layer that counts the rules nothing enforces. A personal tool, published as-is: it is
what the author runs daily, with no support and no stability promise.

```
/plugin marketplace add Hirannad/tenet
/plugin install tenet@tenet
```

## What it does

- **Every decision carries its reversal condition.** A `revisit` field, named when you decide: the
  concrete circumstance under which another choice becomes correct. "p95 passes 400 ms", not "if
  requirements change".
- **Decisions come back at session start.** The notes in scope for the current directory are
  listed with their reversal conditions, so a past decision is in front of the model before it
  decides again.
- **Nothing enters without your verdict.** `/tenet:tenet-capture` writes drafts to `inbox/`,
  `/tenet:tenet-capture review` takes your verdict, and the next session start promotes what you
  accepted.
- **`/tenet:tenet-sweep`** judges which reversal conditions may have fired, and reports dead links,
  orphans, stale drafts and repeated process deviations. It proposes; it never edits a decision.
- **`/tenet:tenet-audit`** scores `CLAUDE.md` against a rubric, counts rules nothing enforces,
  counts directives across the instruction layers, and diffs the tool surface against a baseline
  you accepted.

## First run

Run `/tenet:tenet-capture`. With no ledger yet it prints the bootstrap command for your install
(the plugin's path carries a version number, so the command is resolved rather than written here).
The ledger's path is a plugin option, default `~/Claude/ledger`; bootstrap refuses a directory that
already holds markdown or an `.obsidian/`.

## What runs when

| When | What | Cost |
| :-- | :-- | :-- |
| session start | promote reviewed drafts, list the notes in scope | ~10 KB on a ledger with 58 universal notes; capped at 40 lines, and it says what it withheld |
| after compaction | the list again | the same |
| a slash command | capture, sweep or audit | only when you invoke it |

Nothing runs after each response and nothing runs on a timer. Point a scheduler at
`/tenet:tenet-sweep` if you want it weekly.

## Configuration

| Setting | What it sets |
| :-- | :-- |
| the ledger option in `/plugin` (`CLAUDE_PLUGIN_OPTION_LEDGER`) | the ledger path |
| `TENET_LEDGER` | an override for one shell or one run |
| `CLAUDE_MD`, `ENFORCEMENT_TABLE` | the instruction file and enforcement table the audit reads |
| `CLAUDE_CONFIG_DIR` | Claude Code's config tree |

## Requirements

macOS or Linux, Python 3.9 or newer (the macOS system one is enough). The audit scripts still need
bash 3.2+ and, for `surface-check.sh`, `jq`. git is optional and recommended: the notes are the
database, git is the backup. Obsidian is optional; the ledger is plain markdown. Windows is not
supported.

## Privacy

**No script makes a network call.** No telemetry, nothing uploaded. Check it yourself:

```bash
grep -rnE 'curl|wget|https?://|/dev/tcp|urllib|socket|http\.client' tenet/ skills/*/scripts hooks/
```

**What it writes:** `cli.py bootstrap` creates the ledger, and session start moves approved drafts
from `inbox/` to the ledger root, with `git mv` when the ledger is a repository (which leaves a
staged rename there). Nothing under `~/.claude` is written.

**What it reads from Claude's auto memory** (`~/.claude/projects/*/memory/`): the sweep selects
notes of `type: feedback` and prints each one's project, filename and `description:` line, and
nothing else from them. The audit's `layer-check.sh` reports only whether a memory line also lives
in an instruction file; `--no-memory` skips it. `CLAUDE_CODE_DISABLE_AUTO_MEMORY` or
`autoMemoryEnabled: false` make both read nothing, and the sweep then says it read nothing rather
than that it found nothing.

**What the audit reads:** the files it scores and diffs: `~/.claude/CLAUDE.md` and `rules/`, the
project's `CLAUDE.md` and `rules/`, `CLAUDE.local.md`, managed policy, the settings files,
`~/.claude.json`, and the skills, agents and plugins directories. It prints to your terminal only.

## Known limits

- The session-start list is capped by lines, not bytes. A per-project brief replaces it in 3.1.
- `layer-check.sh` counts directives, not tokens, and undercounts a paragraph holding several rules.
- A contradiction between two rules that share no wording is invisible to the audit.
- With the working directory inside this repository the plugin loads twice.

## License

MIT. Release history: [CHANGELOG.md](CHANGELOG.md).
