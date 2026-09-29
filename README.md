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
- **Decisions come back at session start, per project.** An out-of-band observer reads the last
  30 days of your sessions and works out which notes matter in which project: content match
  between each note and what you asked there, plus a core of the most broadly relevant decisions
  and the notes of the last two weeks. The session-start hook only prints that precomputed brief.
- **Nothing enters without your verdict, and the verdict comes to you.** When drafts wait in
  `inbox/` and a session reaches a resting point (enough work done, nothing running in the
  background, no open task, the last message not a question), one AskUserQuestion asks for one to
  four verdicts, once per session: accept, discard, move to the project's auto memory, or later.
  A script applies the answers; the model never edits a status. `/tenet:tenet-capture` writes
  drafts by hand, and its `review` mode is the manual path.
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
| session start | promote reviewed drafts, print this project's brief | ~30 ms; the brief is capped at 4 KB and says what it withheld |
| session start, when due | a detached background scan (brief older than a week, notes changed, or a new project) | ~2 s, never waited on |
| after compaction | the brief again, no scan | the same |
| after each response | is this a resting point with drafts waiting? If so, one verdict dialog | ~0.1 s with an empty inbox; reads the transcript only when drafts wait; asks at most once per session |
| a slash command | capture, sweep or audit | only when you invoke it |

Nothing runs on a timer. A stale or failing scan prints a
`TENET BRIEF STALE` or `TENET OBSERVER FAILING` line at the top of every session until it is fixed.
Point a scheduler at `/tenet:tenet-sweep` if you want the sweep weekly.

## Configuration

| Setting | What it sets |
| :-- | :-- |
| the ledger option in `/plugin` (`CLAUDE_PLUGIN_OPTION_LEDGER`) | the ledger path |
| `TENET_LEDGER` | an override for one shell or one run |
| `CLAUDE_MD`, `ENFORCEMENT_TABLE` | the instruction file and enforcement table the audit reads |
| `CLAUDE_CONFIG_DIR` | Claude Code's config tree |

## Requirements

macOS or Linux, and Python 3.9 or newer (the macOS system one is enough); nothing else to install.
git is optional and recommended: the notes are the
database, git is the backup. Obsidian is optional; the ledger is plain markdown. Windows is not
supported.

## Privacy

**No script makes a network call.** No telemetry, nothing uploaded. Check it yourself:

```bash
grep -rnE 'curl|wget|https?://|/dev/tcp|urllib|socket|http\.client' tenet/ hooks/
```

**What it writes:** `cli.py bootstrap` creates the ledger; a verdict rewrites the draft's `status`
line, deletes a discarded draft, and appends date, draft name and verdict to
`_meta/observer/verdicts.jsonl`; session start moves approved drafts from
`inbox/` to the ledger root, with `git mv` when the ledger is a repository (which leaves a staged
rename there); the observer appends to `_meta/observer/usage.jsonl` in the ledger (date, note name,
project path, session id: which notes were used where, kept for 180 days) and writes its briefs and
status to the data directory Claude Code assigns the plugin (`~/.claude/plugins/data/tenet-…/`).
Nothing else under `~/.claude` is written.

**What the observer reads:** your session transcripts of the last 30 days
(`~/.claude/projects/*/*.jsonl`). Your prompts, the questions and options of AskUserQuestion calls,
and the file paths tools touched decide which notes matter in which project; the assistant's text
is searched only for ledger note names it cited. None of that text is stored: a brief holds note
names and the first sentence of each note, and the usage log holds what is listed above.

**What it reads from Claude's auto memory** (`~/.claude/projects/*/memory/`): the sweep selects
notes of `type: feedback` and prints each one's project, filename and `description:` line, and
nothing else from them. The audit's `audit layers` check reports only whether a memory line also lives
in an instruction file; `--no-memory` skips it. `CLAUDE_CODE_DISABLE_AUTO_MEMORY` or
`autoMemoryEnabled: false` make both read nothing, and the sweep then says it read nothing rather
than that it found nothing.

**What the audit reads:** the files it scores and diffs: `~/.claude/CLAUDE.md` and `rules/`, the
project's `CLAUDE.md` and `rules/`, `CLAUDE.local.md`, managed policy, the settings files,
`~/.claude.json`, and the skills, agents and plugins directories. It prints to your terminal only.

## Known limits

- Relevance is measured, not perfect: of the notes cited in work sessions over the last 30 days, the
  brief of the project they were cited in shows about two thirds. A citation counts only when the
  note's name appears, so a decision applied without naming it goes unseen.
- A project gets its own brief from its first scanned session; before that the session start
  shows the global brief (core and fresh notes).
- `audit layers` counts directives, not tokens, and undercounts a paragraph holding several rules.
- A contradiction between two rules that share no wording is invisible to the audit.
- With the working directory inside this repository the plugin loads twice.

## License

MIT. Release history: [CHANGELOG.md](CHANGELOG.md).
