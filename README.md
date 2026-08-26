# tenet

**A rule and a decision are the same object at two altitudes.** Both are things you committed to.
Both have a reason. Both can go stale without anyone noticing. And both should say what catches
them when they break.

`tenet` is the machinery for that. It is one system with two entry points: a journal of decisions
that comes back to you when their assumptions expire, and an audit of the instruction layer that
counts the rules nothing actually enforces.

This is a personal tool, published as-is. It is what the author runs daily; it is not a product.
There is no support, no roadmap and no stability promise. If it fits how you work, the install is
two lines.

> **Renaming is a supported operation** — see [Renaming](#renaming). Not a courtesy: a folder
> rename once broke this system for a week without anything noticing, so the path back out is
> built in and checked.

## The problem

Your `CLAUDE.md` has forty rules. Which three are actually enforced by anything? Most instruction
files cannot answer that, so the list grows and compliance quietly falls.

Meanwhile the decision records you do write are written once. Plenty of tools record a decision,
and several now re-read them — searching for past reversals, dating facts, linting for staleness.
What none of them ask for is the thing that makes re-reading useful: **the condition, named when
you decide, under which a different choice becomes correct.** A decision without one is a decision
you will keep honouring after it stopped being right, and no amount of searching afterwards
recovers a threshold you never wrote down.

## What it does

**Records commitments with an expiry.** Every decision carries a `revisit` field: the concrete
condition under which a different choice becomes correct. Not "if requirements change" — something
you could recognise on sight, like `p95 search latency passes 400 ms`.

**Sweeps for expired ones.** A weekly pass judges which reversal conditions may now have fired, and
says so with the original reasoning quoted. Pre-committed condition plus a pass that reads it back
is the pairing; either half alone is something other tools already do.

**Counts what nothing enforces.** Every rule appears in an enforcement table next to what catches
it when broken — or `none` and the reason. A rule with no answer is itself the defect, and the
count is a number rather than an assumption. The same check runs against two targets: the vault's
own conventions and your global `CLAUDE.md`.

**Measures the surface growing behind you.** Permissions, plugins, skills, hooks, MCP servers —
eleven surfaces diffed against a baseline you recorded and accepted, so you see `18 → 25` with the
additions named wherever the baseline recorded the items, rather than a bare `25`. It never
re-records that baseline itself: one that updates itself erases the signal it exists to produce.

**Stays out of the way.** Notes are scoped per directory. Methodology is visible everywhere;
project knowledge only where you bind it. A growing knowledge base never floods an unrelated
session.

**Never canonises on its own.** The agent may only write drafts. A human verdict is what promotes
one, and a separate mechanical step does the promoting so it cannot be forgotten.

## What this is not

- **Not a second brain.** It does not ingest sources, summarise articles, or file your reading. A
  `source` note here records what a source *changed*, never what it said.
- **Not a note-taking system.** Three admission gates and an explicit not-list mean most of what
  happens in a session earns no note at all. That is the design, not a gap.
- **Not your agent's memory.** Claude Code already does that — see
  [what the platform already does](#what-the-platform-already-does).
- **Not a task list.** Open questions are parked tensions with a closing condition, not to-dos.
- **Claude Code only.** Skills, hooks and the plugin manifest are Claude Code mechanisms. It is not
  editor-agnostic and does not target other agents.

## Compared to

The popular Obsidian-plus-agent systems solve a different problem well. This table is four
questions, and most of the "no" answers are not shortcomings — they are different jobs. Star counts
read live from the GitHub API on 2026-08-26; every other cell was checked by reading the tool's own
templates and command files, not its marketing.

| | records a decision | carries a reversal condition, named when deciding | something reads it back | audits the instruction layer |
| :-- | :-- | :-- | :-- | :-- |
| **tenet** | yes | **yes** — the `revisit` field | yes — the weekly sweep judges whether each has fired | yes — rubric, enforcement table, surface diff |
| [claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian) · 13.2k★ | no — no decision record of any kind | no | its `wiki-lint` re-reads notes for dead links and stale indexes | no |
| [obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain) · 4.2k★ | yes — `/obsidian-decide --formal` writes a Nygard-shaped ADR | no | yes, and well: `/obsidian-challenge` surfaces your own past reversals, and a linter enforces that every fact is timeless, dated, or a pointer | no — it generates a vault `CLAUDE.md`, it does not score one |
| [obsidian-mind](https://github.com/breferrari/obsidian-mind) · 4.6k★ | yes — a `Decision Record` template with context, options, consequences | no | yes — weekly synthesis and a vault audit | no — its audit covers the vault, not your instruction files |
| [claude-code#15222](https://github.com/anthropics/claude-code/issues/15222) — a native `DECISIONS.md`, requested | proposed | not in the proposal | proposed | no |

Two honest notes on that table. `obsidian-second-brain`'s freshness linter is real machinery
against rot, and for *facts* it goes further than anything here; the target differs — facts there,
decisions and rules here. And the non-AI classics are still the reference for the record format
itself ([adr-tools](https://github.com/npryce/adr-tools) 5.6k★,
[log4brains](https://github.com/thomvaill/log4brains) 1.6k★) — worth reading, though neither has
been pushed to since 2024, so neither has met an agent.

## Install

```
/plugin marketplace add Hirannad/tenet
/plugin install tenet@tenet
```

To update later:

```bash
claude plugin update tenet@tenet
```

It compares the version field in the plugin manifest, so a release here is a version bump, and it
needs a restart to take effect. To remove it, `claude plugin uninstall tenet@tenet` (`/plugin` opens
the manager if you would rather click). Your vault is a directory of markdown files the plugin never
owned, so it stays exactly where it is.

## Getting started

The first ten minutes, in order:

1. **Install** with the two lines above.
2. **Run `/tenet:tenet`.** With no vault yet it prints the exact `bootstrap.sh` command for your
   install. The script's path under the plugin cache carries a version number, so the plugin
   resolves it — a literal command printed here would break on your first update.
3. **Run that command.** It creates the vault: templates, seven saved views, and three worked
   example notes. It refuses to write over an existing vault. Default location `~/Claude/brain`;
   pass a path to put it elsewhere and set `BRAIN_VAULT` to match.
4. **Read the three examples, then delete them.** Two are `universal` and one is `domain`. That
   contrast is the whole scoping model, and it is easier to see than to read about.
5. **Decide something, then run `/tenet:tenet-capture`.** It writes a draft to `inbox/` and stops.
   Nothing enters the vault without your verdict.
6. **Start your next session.** The draft is promoted mechanically, and what you decided is in
   scope where you decided it.

The tool and its store carry different names on purpose: `tenet` is the machinery, the vault is the
content, and they are separate directories with separate lifetimes.

## With and without Obsidian

Obsidian is optional, and it is worth being exact about what it changes.

**Without it, everything mechanical works.** Capturing decisions, the review loop, promotion, the
weekly sweep, every check, the whole audit half. The vault is a directory of markdown files; every
script here reads plain text.

**With it, you get the seven `.base` views** — saved queries over the frontmatter, which is the
human-facing half of the method. The one that earns the install is `Revisit.base`: every live
decision that carries a reversal condition, oldest first. The sweep tells the agent; that view
tells you. Without Obsidian the seven files are inert YAML and nothing else changes.

## What the platform already does

Claude Code has its own memory, and this plugin deliberately does not duplicate it.

**Auto memory** — Claude's own notes about your preferences, corrections and project context —
lives in `~/.claude/projects/<project>/memory/` with a `MEMORY.md` index loaded into every session.
That is where working state belongs, and 2.0.0 of this plugin removed its own version of it. Two
things worth knowing about the native one: it is machine-local and not synced anywhere, and it is
scoped per repository.

**`CLAUDE.md` and `.claude/rules/`** are the instruction layers, with path-scoped rules for
instructions that should only load for matching files. This plugin does not replace them — it
audits them.

Where it still adds something is the third thing neither covers: a decision, its reasoning, and the
condition that would reverse it, in a store with its own git history rather than a machine-local
cache. The sweep now reads the native `feedback` memories as its input for repeated process
deviations, and does the part the platform does not — turning a repeat into a verdict: a mechanism
that fails when the rule breaks, or deleting the rule.

## Privacy

**No script here makes a network call.** No telemetry, no analytics, no phoning home, and nothing
is uploaded. Check it yourself, over everything executable in the tree:

```bash
grep -rE 'curl|wget|https?://|/dev/tcp' --include='*.sh' --include='*.json' skills/ hooks/ locales/
```

That returns nothing. (Run without `--include` and you get one hit: a reference document discussing
a `curl`-pipe-`bash` deny rule in prose. Prose, not a call — which is why the filter is there and
not hiding anything.) The only `git` calls are local reads — `remote get-url`, `rev-parse`,
`status` — plus one local `git mv` when an approved draft is promoted.

**No script writes anywhere under `~/.claude`.** The two things that write at all are
`bootstrap.sh`, which creates your vault, and `promote.sh`, which moves an approved draft from
`inbox/` to the vault root. Everything else reads.

**All state is local files you can read.** The vault is markdown; the baselines and tables are
files in your home directory that you edit by hand.

The one thing to know before running it: `rename-check.sh` greps a wide surface and **prints
matching lines to your terminal**. Read the list in [Renaming](#renaming) first if any of those
paths hold something you would rather not see echoed.

## Known limits

Measured, not estimated, and each one has an issue open rather than a shrug.

- **The scope gate is unexercised in the author's own vault.** 43 knowledge notes, all
  `scope: universal`, zero `domain` — against a threshold the sweep itself puts at ~15. The
  mechanism works and the evidence for it is thin, which is a different statement.
  [#1](https://github.com/Hirannad/tenet/issues/1)
- **Zero `pattern` notes after a month.** The type exists; the agent is forbidden from writing one,
  and the human path to writing one may be too narrow to walk.
  [#2](https://github.com/Hirannad/tenet/issues/2)
- **`frontmatter-check` scores 2 of 33 files in this repository** (one on a fresh clone). Every
  exemption is justified, and a check that scores one file is still close to a check that cannot
  fail. [#3](https://github.com/Hirannad/tenet/issues/3)
- **A native `DECISIONS.md` was requested and the request expired unanswered.** What that would
  make redundant, and what it would not.
  [#4](https://github.com/Hirannad/tenet/issues/4)
- **A locale is six strings**, covering the decision template's headings only. The other four
  templates have fifteen headings between them and no locale string. Only `SECTION_DECISION` is
  matched mechanically, so the gap costs nothing today — but switching locale is a two-step
  operation, and `locales/hu.sh` says so in its own header.
- **The plugin loads twice if your working directory *is* this repository** — once from the
  marketplace cache and once from the tree in front of you — so hooks fire twice and every figure
  below doubles. It affects developing the plugin, not installing it.

## Commands

| Skill | What it does |
| :-- | :-- |
| `/tenet:tenet` | What is in scope here, and what you already decided about it |
| `/tenet:tenet-capture` | Turn a session's decisions into drafts; review pending ones |
| `/tenet:tenet-sweep` | The weekly pass: fired reversal conditions, dead links, orphans, an over-grown universal layer |
| `/tenet:tenet-audit` | Score the instruction layer, find cross-layer duplication, count unenforced rules, diff the tool surface |

Nothing here runs on a timer. The sweep is weekly by convention, and what holds the convention up
is one line at session start once the last digest is over a week old. Point `cron`, `launchd` or
your own scheduler at it if you want more than a nudge.

## Language

Section headings are prose, so they have a language. English by default; put one word in the
vault's `_meta/locale` to switch (`hu` ships as a worked example, and a locale is six strings —
see `locales/hu.sh`). The locale belongs to the vault rather than the machine, so a vault carries
its language wherever it is cloned. Frontmatter keys and values stay English either way: scripts
read those, you do not.

## Renaming

Names change, and this one already has. `skills/tenet/scripts/lib.sh` holds both name pairs —
`PLUGIN_NAME` for the machinery and `BRAIN_NAME` for the vault, each with a `_PREVIOUS_NAMES` list.
Set the new name, append the old one to that list, then run:

```bash
bash skills/tenet/scripts/rename-check.sh
```

It greps the whole reference surface for stale names, verifies the vault directory matches in
case (APFS lies about this, and a case mismatch is how a scheduled run once died silently for a
week), checks that every `SKILL.md` still loads — no shell expansion in a `!`-block, which makes the
preprocessor reject the block and truncate the skill's body with no error, and no unquoted
`": "` in the frontmatter, which makes the skill load with no metadata at all — and resolves
every active binding. The script's own header lists all seven checks.

One of the seven is not about renaming: it compares this repository's two manifests on name,
version, license and keywords. `claude plugin update` gates on one of those copies while the
marketplace advertises the other, and two hand-kept copies of the same facts with nothing
comparing them is the exact failure this tool is about. Run it before a release for that reason
alone.

**What it reads.** Run by hand, never from a hook, and it only ever greps — but the surface it
greps is wide by necessity: `~/.claude/CLAUDE.md`, `~/.claude/settings.json`,
`~/.claude/RESTORE.md`, `~/.claude/surface-baseline.json`, `~/.claude/skills`,
`~/.claude/scheduled-tasks`, your Obsidian vault registry, the vault's `_meta/bindings.md`, and
this repository. It prints matching lines. Read the list before running it if any of those hold
something you would rather not see echoed to a terminal.

## Context cost

Three injection points and one always-on cost. Measured at 2.0.0 on 2026-08-26:

| What | Size | When |
| :-- | :-- | :-- |
| three skill descriptions | 1.5 KB | every session, unconditionally — the fourth skill is `disable-model-invocation`, so it costs nothing until you call it |
| session start: `promote.sh` then `resolve.sh` | 0.8 KB on a fresh vault, 8.5 KB on one whose universal layer lists thirty-seven notes | startup and resume, and `resolve.sh` again after a compaction |
| response end: the capture prompt | 3.2 KB | every response, gated on the vault's `inbox/` existing — no vault, no cost |
| after every edit: the enforcement hook | nothing | it speaks only when the global `CLAUDE.md` just changed and its table no longer matches |

Both injection points got cheaper in 2.0.0, and the session-start figure did so while the note
count went *up*: 11.9 KB at thirty-five notes before, 8.5 KB at thirty-seven now. Removing the
working-state cache is where the difference came from, and the response-end prompt dropped 1.0 KB
by handing corrections back to the platform's own record.

The session-start block is the one that grows: it lists every `universal` note, and its cap
(`MAX_LIST` in `resolve.sh`) counts lines rather than bytes while each line carries a whole
revisit condition. When the cap bites it says how many notes it withheld — a `head` that drops the
tail in silence is the failure this whole system is about. The weekly sweep speaks earlier, past
roughly fifteen notes, but that is advice rather than a brake.

The descriptions carry a deliberate cost of their own: the sweep's more than doubled at 0.6.0,
because the short version measurably failed to fire on half the ways a person asks for
maintenance. A description that does not trigger costs the whole skill.

## Requirements

**Bash 3.2 or newer** — the macOS default is enough. This is bash and not `sh`: the scripts use
process substitution, arrays and here-strings, so a POSIX shell will not run them.

**`jq`**, for one script only: `surface-check.sh`, which reads JSON. Without it that one check
reports that it measured nothing rather than reporting zeroes, and nothing else is affected.

`git` is optional and recommended: the notes are the database, git is the backup. Obsidian is
optional too — see [with and without Obsidian](#with-and-without-obsidian).

**What it reads outside its own tree.** None of this ships with the plugin, and no absence is an
error — each one is a first-run state that says which state it is:

| Path | Read by | Absent means |
| :-- | :-- | :-- |
| `~/Claude/brain` | all of it | no vault yet; `/tenet:tenet` prints the bootstrap command for your install |
| `~/.claude/projects/*/memory/` | the sweep, for `feedback` notes | it says which it was — directory missing, relocated by `autoMemoryDirectory`, or auto memory switched off — because none of those is "no deviations" |
| `~/.claude/CLAUDE.md` | the audit and its `PostToolUse` hook | nothing to audit |
| `~/.claude/enforcement.md` | `enforcement-check.sh` | no table yet — it reports how many rules are uncovered, and the hook stays quiet rather than alarming |
| `~/.claude/surface-baseline.json` | `surface-check.sh` | no baseline yet — today's counts, plus the command that records them |
| `~/.claude/settings.json` | `surface-check.sh`, and the sweep for the two auto-memory settings | the JSON surfaces read as unmeasured, never as zero |
| `~/.claude.json` | `surface-check.sh` | no user-scope MCP servers to count |
| `~/.claude/skills/`, `~/.claude/agents/`, `~/.claude/plugins/` | `surface-check.sh` | each says which directory is missing, rather than counting it as zero |

`rename-check.sh` reads a wider surface still, listed under [Renaming](#renaming) — it is the one
script you run by hand, and knowing what it greps before you run it is the point.

**Environment variables**, all optional:

| Variable | Overrides |
| :-- | :-- |
| `BRAIN_VAULT` | the vault path (`~/Claude/brain`) |
| `TENET_LOCALE` | the vault's `_meta/locale`, for one run |
| `CLAUDE_MD` | the instruction file the audit and its hook read |
| `ENFORCEMENT_TABLE` | where the enforcement table lives |

## Changelog

Every release and the defect that caused it: [CHANGELOG.md](CHANGELOG.md). The entries are written
as narrative rather than bullet lists, because in almost every case the thing that shipped was a
check that could not fail, and the reason is the useful part.

## License

MIT.
