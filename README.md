# tenet

**A rule and a decision are the same object at two altitudes.** Both are things you committed to.
Both have a reason. Both can go stale without anyone noticing. And both should say what catches
them when they break.

`tenet` is the machinery for that: a journal of decisions that comes back to you when its
assumptions expire, and an audit of the instruction layer that counts the rules nothing actually
enforces.

```
/plugin marketplace add Hirannad/tenet
/plugin install tenet@tenet
```

Four commands, and the first one is the whole tour:

| | |
| :-- | :-- |
| `/tenet:tenet` | what is in scope here, and what you already decided about it |
| `/tenet:tenet-capture` | turn this session's decisions into drafts; review pending ones |
| `/tenet:tenet-sweep` | the weekly pass: which reversal conditions may have fired |
| `/tenet:tenet-audit` | score `CLAUDE.md`, count unenforced rules, diff the tool surface |

`/tenet:tenet` on a fresh install prints the exact command to create the store, then this — real
output, from a vault made by that command thirty seconds earlier:

```
LEDGER: /Users/you/Claude/ledger
BOUND TOPICS: none (this directory is not bound; topic notes are out of scope)

## Always in scope — methodology, architecture, structure
- [[2026-01-12-one-decision-per-note]] (decision, accepted) — revisit when: If a note keeps
  needing a second decision to make sense on its own — then the split is cutting through
  something that is genuinely one choice, and the cap is doing harm
- [[2026-02-20-ship-behind-a-flag]] (decision, accepted) — revisit when: If flags outlive their
  rollouts often enough that reading the code no longer tells you what runs in production —
  then the flag is the new fork, and it costs more than the branch it replaced
```

The second half of each line is the point. Not *what* was decided — the condition that would make
a different choice correct.

This is a personal tool, published as-is. It is what the author runs daily; it is not a product.
There is no support and no stability promise. If it fits how you work, the install is two lines.

> **Renaming is a supported operation** — see [Renaming](#renaming). Not a courtesy: a folder
> rename once broke this system for a week without anything noticing, so the path back out is
> built in and checked. The store itself was renamed in 2.1.0, through that same mechanism.

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

**Counts how many instructions are actually competing.** Six layers — managed policy, your
`CLAUDE.md` and `rules/`, the project's `CLAUDE.md` and `rules/`, and `CLAUDE.local.md` — measured
against the ~150–200 instructions frontier models reliably follow, of which Claude Code's own system
prompt already spends about 50. Then the two findings that only show up across layers: a rule
carried by more than one of them, and a pair that differs only by a negation with nothing declaring
which wins. Line count cannot see either, which is why the rubric stopped scoring on `wc -l`. A
layer the check could not open reports as unexamined, never as empty.

**Measures the surface growing behind you.** Permissions, plugins, skills, hooks, MCP servers —
eleven surfaces diffed against a baseline you recorded and accepted, so you see `18 → 25` with the
additions named wherever the baseline recorded the items, rather than a bare `25`. It never
re-records that baseline itself: one that updates itself erases the signal it exists to produce.
It counts what your config *declares*, not what you use — there is no usage data anywhere in this
plugin, so it can say that seven plugins arrived since you accepted a baseline and cannot say which
two you actually invoke. `/skill-doctor` has that number; this has the delta. It runs when you run
the audit, nothing watches the surface in the background, and it never edits your config.

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
- **Not a churn log.** A tool you tried for three days and threw out is a forced move, not a
  decision — no second path was weighed, so the capture gates reject it, and should. This is for
  commitments that outlive the things they were made about: how you work, the shape you gave the
  code, the constraint you accepted. If nothing you decide lasts longer than a fortnight, install
  nothing. That is a real answer, not a failure of the tool.

## Compared to

The popular Obsidian-plus-agent systems solve a different problem well. This table is four
questions, and most of the "no" answers are not shortcomings — they are different jobs. Star counts
read live from the GitHub API on 2026-08-28; every other cell was checked by reading the tool's own
templates and command files, not its marketing.

| | records a decision | carries a reversal condition, named when deciding | something reads it back | audits the instruction layer |
| :-- | :-- | :-- | :-- | :-- |
| **tenet** | yes | **yes** — the `revisit` field | yes — the weekly sweep judges whether each has fired | yes — rubric, enforcement table, surface diff |
| [claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian) · 14.2k★ | no — no decision record of any kind | no | its `wiki-lint` re-reads notes for dead links and stale indexes | no |
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

The two lines are at the top. To update later:

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
3. **Run that command.** It creates the store: templates, seven saved views, and three worked
   example notes. It refuses to write into a directory that already holds markdown, at any depth,
   or that carries an `.obsidian/`. Default location `~/Claude/ledger` — and there is nothing to
   configure if you take the default, because the path is a plugin option the installer already
   asked you for. Pass a different path to `bootstrap.sh` and set the same path in `/plugin`.
4. **Read the three examples, then delete them.** Two are `universal` and one is `domain`. That
   contrast is the whole scoping model, and it is easier to see than to read about.
5. **Decide something, then run `/tenet:tenet-capture`.** It writes a draft to `inbox/` and stops.
   Nothing enters the vault without your verdict.
6. **Start your next session.** The draft is promoted mechanically, and what you decided is in
   scope where you decided it.

The tool and its store carry different names on purpose: `tenet` is the machinery, the `ledger` is
the content, and they are separate directories with separate lifetimes. The store's path is a
typed plugin option (`userConfig`), so Claude Code asks for it at install time and hands it to
every script — no environment variable to remember, and no default written down in two places.

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

**Three first-party things now overlap the audit half**, and naming them is more useful than
waiting to be told. Anthropic ships a `claude-md-management` plugin whose `claude-md-improver` skill
triggers on very nearly this skill's wording — *check, audit, update, improve, or fix* `CLAUDE.md`.
`/doctor` proposes trims for a checked-in `CLAUDE.md`, keeping the pitfalls and the rationale.
`/skill-doctor` reports which loaded skills are unused and what they cost in context, which is
adjacent to the surface-growth check here. If you want your instruction file *improved*, those are
first-party and they will stay current with the platform.

Where this still adds something is what none of them do: a decision, its reasoning, and the
condition that would reverse it, in a store with its own git history rather than a machine-local
cache — plus a score you can compare over time, an enforcement table where every rule names what
catches it when it breaks, and a diff against a baseline you accepted rather than one that updates
itself. The sweep reads the native `feedback` memories as its input for repeated process deviations
and does the part the platform does not: turning a repeat into a verdict, a mechanism that fails
when the rule breaks or deleting the rule.

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
`bootstrap.sh`, which creates your store, and `promote.sh`, which moves an approved draft from
`inbox/` to the store root. Everything else reads. One consequence worth stating: when your store is
a git repository, `promote.sh` uses `git mv`, so an unattended session start can leave a staged
rename in a repository you did not touch.

**All state is local files you can read.** The store is markdown; the baselines and tables are
files in your home directory that you edit by hand. The store's path is the one thing kept in
Claude Code's own settings, under `pluginConfigs`, because it is a plugin option rather than
plugin state.

The one thing to know before running it: `rename-check.sh` greps a wide surface and **prints
matching lines to your terminal**. Read the list in [Renaming](#renaming) first if any of those
paths hold something you would rather not see echoed.

## Known limits

Measured, not estimated. The first four are open questions, and each has an issue rather than a
shrug; the other four live here rather than in the tracker — three are deliberate limits, one is
an unknown stated rather than quietly fixed.

- **The scope gate is unexercised in the author's own vault.** 43 knowledge notes, all
  `scope: universal`, zero `domain` — against a threshold the sweep itself puts at ~15. The
  mechanism works and the evidence for it is thin, which is a different statement.
  [#1](https://github.com/Hirannad/tenet/issues/1)
- **Zero `pattern` notes after a month.** The type exists; the agent is forbidden from writing one,
  and the human path to writing one may be too narrow to walk.
  [#2](https://github.com/Hirannad/tenet/issues/2)
- **`frontmatter-check` scores 2 of 33 files on a fresh clone** (a third, gitignored file joins in
  the author's working copy). Every exemption is justified, and a check that scores two files is
  still close to a check that cannot fail. [#3](https://github.com/Hirannad/tenet/issues/3)
- **A native `DECISIONS.md` was requested and the request expired unanswered.** What that would
  make redundant, and what it would not.
  [#4](https://github.com/Hirannad/tenet/issues/4) — and that issue is written against a condition
  that has not fired, while three first-party things overlapping the audit half already have. See
  [what the platform already does](#what-the-platform-already-does).
- **`layer-check.sh`'s directive count is a proxy, and it undercounts on purpose.** A directive is a
  list item or a line carrying a normative token, so a paragraph holding three rules counts once and
  the token list is English — a Hungarian instruction file undercounts unless its rules are
  bulleted. Both errors point the same way, which is the safe direction for a budget, and the script
  says so in its own header. What it is not is a token count: `/context` has that.
- **A locale is six strings**, covering the decision template's headings only. The other four
  templates have fifteen headings between them and no locale string. Only `SECTION_DECISION` is
  matched mechanically, so the gap costs nothing today — but switching locale is a two-step
  operation, and `locales/hu.sh` says so in its own header.
- **The plugin loads twice if your working directory *is* this repository** — once from the
  marketplace cache and once from the tree in front of you — so hooks fire twice and every measured
  figure doubles. It affects developing the plugin, not installing it.
- **Whether an injected `!`-block aborts on a machine with no matching permission rule is not
  established.** The documented behaviour says it should: an injected command never prompts, and
  anything other than *allow* aborts the invocation. 2.1.0 adds the `allowed-tools` Bash rule that
  removes the question either way, but the abort was never reproduced — this repository's own
  settings hold 43 grants and none of them match the injected form, so the local evidence points
  the other way. Stated rather than quietly fixed.

## Scheduling

The four commands are tabled at the top. Nothing here runs on a timer. The sweep is weekly by convention, and what holds the convention up
is one line at session start once the last digest is over a week old. Point `cron`, `launchd` or
your own scheduler at it if you want more than a nudge.

## Language

Section headings are prose, so they have a language. English by default; put one word in the
vault's `_meta/locale` to switch (`hu` ships as a worked example, and a locale is six strings —
see `locales/hu.sh`). The locale belongs to the vault rather than the machine, so a vault carries
its language wherever it is cloned. Frontmatter keys and values stay English either way: scripts
read those, you do not.

## Renaming

Names change, and this one has twice: the machinery became `tenet` in 0.1.0 and the store became
`ledger` in 2.1.0. `skills/tenet/scripts/lib.sh` holds both name pairs — `PLUGIN_NAME` for the
machinery and `VAULT_NAME` for the store, each with a `_PREVIOUS_NAMES` list. Set the new name,
append the old one to that list, then run:

```bash
bash skills/tenet/scripts/rename-check.sh
```

It greps the whole reference surface for stale names, verifies the vault directory matches in
case (APFS lies about this, and a case mismatch is how a scheduled run once died silently for a
week), checks that every `SKILL.md` still loads — no shell expansion in a `!`-block, which makes the
preprocessor reject the block and truncate the skill's body with no error, and no unquoted
`": "` in the frontmatter, which makes the skill load with no metadata at all — and resolves
every active binding. The script's own header lists all eight checks.

Two of the eight are not about renaming. One compares this repository's two manifests on name,
version, license and keywords. `claude plugin update` gates on one of those copies while the
marketplace advertises the other, and two hand-kept copies of the same facts with nothing
comparing them is the exact failure this tool is about. Run it before a release for that reason
alone.

The other is check 8, and it is the same shape one level down: `hooks/hooks.json` must resolve no
store path of its own. It cannot source `lib.sh`, so anything it names is a second copy of a fact
`lib.sh` owns — which is what it was until 2.1.0. The fix was not to compare the two copies but to
delete one: the guard moved into `hooks/on-stop.sh`, which sources `lib.sh` like everything else,
and check 8 now fails if a path ever reappears in the hook config.

**What it reads.** Run by hand, never from a hook, and it only ever greps — but the surface it
greps is wide by necessity: `~/.claude/CLAUDE.md`, `~/.claude/settings.json`,
`~/.claude/RESTORE.md`, `~/.claude/surface-baseline.json`, `~/.claude/skills`,
`~/.claude/scheduled-tasks`, your Obsidian vault registry, the vault's `_meta/bindings.md`, and
this repository. It prints matching lines. Read the list before running it if any of those hold
something you would rather not see echoed to a terminal.

## Context cost

Three injection points and one always-on cost. Every figure below is either printed by
`claude plugin details tenet` or counted from the shipped files — the previous version of this
section carried one number that was neither, and it was wrong.

| What | Size | When |
| :-- | :-- | :-- |
| four skill descriptions | **~622 tok** total, of which `tenet` ~170, `tenet-sweep` ~200, `tenet-audit` ~140, `tenet-capture` ~110 | every session, unconditionally |
| session start: `promote.sh` then `resolve.sh` | 0.8 KB on a fresh store, 8.5 KB on one whose universal layer lists thirty-seven notes | startup and resume, and `resolve.sh` again after a compaction |
| response end: the capture gate | **0.9 KB** | every response, gated on the store's `inbox/` existing — no store, no cost |
| after every edit: the enforcement hook | nothing | it speaks only when the global `CLAUDE.md` just changed and its table no longer matches |

**What is deliberately not in that table**, because it is not an injection: the audit's four scripts
produce tool output only when you run `/tenet:tenet-audit`. `layer-check.sh`, the one 2.2.0 added, is
**2.2 KB** on a two-layer machine with no findings and grows with the clusters it reports. Nothing
about it loads in a session that never calls the audit — and **no skill description changed in
2.2.0**, so the always-on figure above is the same number it was at 2.1.0.

**Two corrections to what this section used to say.** Both were found by measuring rather than
re-reading, which is the only way this kind of error surfaces.

*The fourth skill is not free.* It carries `disable-model-invocation`, and the old table concluded
from that it "costs nothing until you call it". `claude plugin details` prices it at **~110 tokens
always-on**: the flag stops Claude choosing the skill, it does not remove the description from the
listing. Exactly the class of unverified number this tool exists to catch, in its own README.

*And the total was 18 tokens light, in the section that promises every figure comes from that
command.* 2.1.0 wrote ~604 with `tenet-capture` at ~90; re-running `claude plugin details tenet`
against the same installed 2.1.0 on 2026-08-28 prints **~622** with `tenet-capture` at ~110. The
descriptions did not change, so either the estimator did or the earlier reading was taken before the
last description edit — and which of those it was cannot be recovered, which is the whole argument
for re-running the command every release instead of copying the number forward. 2.2.0 changed no
description, so ~622 is also 2.2.0's figure. The same command prices the on-invoke side, which the
table above deliberately omits because it is not an injection: `tenet` ~1.1k, `tenet-capture` ~1.8k,
`tenet-sweep` ~1.4k, `tenet-audit` ~2.8k, each paid only when that skill fires.

*The response-end cost was 3.2 KB, and nobody was paying it — because nothing was receiving it.*
The `Stop` hook wrote its gate to stdout and exited 0, and a `Stop` hook's exit-0 stdout goes to
the debug log and nowhere else; only `SessionStart`, `UserPromptSubmit` and `UserPromptExpansion`
have their stdout added to the model's context. So the automatic-drafting path had never run once.
2.1.0 moves it to `hookSpecificOutput.additionalContext`, which does reach the model, with a
`stop_hook_active` guard so the injection lands once instead of looping. Measured on 2026-08-27,
four mechanisms, one probe token each: stdout — not delivered; `systemMessage` — not delivered;
`additionalContext` — delivered; `additionalContext` with no guard — delivered, then looped to the
turn limit. The gate itself went 3.2 KB → 0.9 KB in the same change, because the drafting rules it
carried are needed only once the gate fires and now live in a file the model reads then.

The session-start block is the one that grows: it lists every `universal` note, and its cap
(`MAX_LIST` in `resolve.sh`) counts lines rather than bytes while each line carries a whole
revisit condition. When the cap bites it says how many notes it withheld — a `head` that drops the
tail in silence is the failure this whole system is about. The weekly sweep speaks earlier, past
roughly fifteen notes, but that is advice rather than a brake.

The descriptions carry a deliberate cost of their own: the sweep's more than doubled at 0.6.0,
because the short version measurably failed to fire on half the ways a person asks for
maintenance. A description that does not trigger costs the whole skill. The four descriptions total
1,816 bytes at 2.1.0, up 46 from 2.0.0 — `tenet-capture`'s grew because it had been claiming to
promote drafts, which its own body forbids.

**These descriptions changed without a trigger test, and that is a stated gap rather than an
oversight.** 0.6.0 established that a description change gets a blind trigger test; the word
`brain` left all three model-visible descriptions in 2.1.0 and no test was run, exactly as 2.0.0
also confessed. The difference is that the mechanism now has a date: `claude plugin eval` with an
ablation arm is what the next release wires up, which turns that promise into something that can
fail.

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
| `~/Claude/ledger` | all of it | no store yet; `/tenet:tenet` prints the bootstrap command for your install |
| `~/.claude/projects/*/memory/` | the sweep, for `feedback` notes; `layer-check.sh`, for rules duplicated between memory and an instruction file | it says which it was — directory missing, relocated by `autoMemoryDirectory`, or auto memory switched off — because none of those is "no deviations" |
| `~/.claude/CLAUDE.md` | the audit and its `PostToolUse` hook | nothing to audit |
| `~/.claude/rules/`, and the managed policy `CLAUDE.md` | `layer-check.sh` | that layer does not exist on this machine — reported as `absent`, which is not a count of zero |
| `~/.claude/instruction-baseline.json` | `layer-check.sh` | no baseline yet — today's count, plus the command that records one |
| `~/.claude/enforcement.md` | `enforcement-check.sh` | no table yet — it reports how many rules are uncovered, and the hook stays quiet rather than alarming |
| `~/.claude/surface-baseline.json` | `surface-check.sh` | no baseline yet — today's counts, plus the command that records them |
| `~/.claude/settings.json` | `surface-check.sh`, and the sweep for the two auto-memory settings | the JSON surfaces read as unmeasured, never as zero |
| `~/.claude.json` | `surface-check.sh` | no user-scope MCP servers to count |
| `~/.claude/skills/`, `~/.claude/agents/`, `~/.claude/plugins/` | `surface-check.sh` | each says which directory is missing, rather than counting it as zero |

`rename-check.sh` reads a wider surface still, listed under [Renaming](#renaming) — it is the one
script you run by hand, and knowing what it greps before you run it is the point.

**Where the store's path comes from**, in precedence order. The first is the platform's own
mechanism and the reason the other three are rarely needed:

| Source | Notes |
| :-- | :-- |
| `userConfig` → `CLAUDE_PLUGIN_OPTION_LEDGER` | a typed `directory` option in `plugin.json`. Claude Code asks for it when the plugin is enabled and exports it to every hook process. Change it later in `/plugin` |
| `TENET_LEDGER` | environment override, for one shell or one run |
| `BRAIN_VAULT` | the pre-2.1.0 name. **Still works**, so an update cannot silently point you at an empty store; `/tenet:tenet` mentions the new spelling once when it is what resolved the path |
| `~/Claude/ledger` | the default |

**Other environment variables**, all optional:

| Variable | Overrides |
| :-- | :-- |
| `TENET_LOCALE` | the store's `_meta/locale`, for one run |
| `CLAUDE_MD` | the instruction file the audit and its hook read |
| `ENFORCEMENT_TABLE` | where the enforcement table lives |
| `CLAUDE_CONFIG_DIR` | Claude Code's config tree. Honoured by every script that reads it since 2.1.0 — before that, by one of five |

## How it is built

Every script, when it runs, what it reads, what it writes, and the two files where shell was the
wrong choice: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). It names the two directory conventions
the tree does not — `skills/tenet/scripts/lib.sh` is the library, `skills/tenet-audit/scripts/` is
the shared checker directory — and the four house rules the code actually implements, each of which
is there because it was violated first.

## The rubric, on its own

The instruction-layer rubric is the most portable thing here and it needs no install:
[skills/tenet-audit/references/rubric.md](skills/tenet-audit/references/rubric.md). Seven
dimensions, 100 points, synthesised in 2026-08 from 43 `CLAUDE.md` files in public repositories —
size and scope, mandatory content, writing style, compliance technique, anti-patterns, layer
hygiene, freshness. Read it against your own file and you get most of the value of the audit
without running anything.

It is worth knowing what it is *not*. It scores a file; it does not rewrite one. Anthropic's own
`claude-md-management` plugin and `/doctor` both propose improvements, and if that is what you want,
use those — they are first-party and they will stay current with the platform. What this adds
instead is a number you can compare over time, an enforcement table where every rule names what
catches it when it breaks, and a diff of eleven tool surfaces against a baseline you accepted. The
overlap is real and is tracked in [#4](https://github.com/Hirannad/tenet/issues/4).

**Three of the rubric's findings are now counted rather than eyeballed**, and the platform has said
in public which of them it does not do. In
[claude-code#85477](https://github.com/anthropics/claude-code/issues/85477) a Claude Code
collaborator answered a request for instruction-layer diagnostics with *"There is no
instruction-budget warning, duplicate-rule detection, or cross-file conflict detection yet"*.
`layer-check.sh` does the first two and the mechanical subset of the third; the semantic remainder
prints as `none` with the reason, because a contradiction with no shared wording is invisible to a
string comparison and pretending otherwise would make this README the thing it warns about.

## Changelog

Every release and the defect that caused it: [CHANGELOG.md](CHANGELOG.md). The entries are written
as narrative rather than bullet lists, because in almost every case the thing that shipped was a
check that could not fail, and the reason is the useful part.

## License

MIT.
