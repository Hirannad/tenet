# tenet

**A rule and a decision are the same object at two altitudes.** Both are things you committed to.
Both have a reason. Both can go stale without anyone noticing. And both should say what catches
them when they break.

`tenet` is the machinery for that. It is one system with two entry points: a journal of decisions
that comes back to you when their assumptions expire, and an audit of the instruction layer that
counts the rules nothing actually enforces.

> **Renaming is a supported operation** — see [Renaming](#renaming). Not a courtesy: a folder
> rename once broke this system for a week without anything noticing, so the path back out is
> built in and checked.

## The problem

Your `CLAUDE.md` has forty rules. Which three are actually enforced by anything? Most instruction
files cannot answer that, so the list grows and compliance quietly falls.

Meanwhile every architecture decision you record is written once and never read again. Tools that
generate decision records are common; tools that *re-read* them are not. A decision without an
expiry condition is a decision you will keep honouring after it stopped being right.

## What it does

**Records commitments with an expiry.** Every decision carries a `revisit` field: the concrete
condition under which a different choice becomes correct. Not "if requirements change" — something
you could recognise on sight.

**Sweeps for expired ones.** A weekly pass judges which reversal conditions may now have fired, and
says so with the original reasoning quoted. This is the part that does not exist elsewhere.

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

## Install

```
/plugin marketplace add Hirannad/tenet
/plugin install tenet@tenet
```

Then create a vault — a directory of markdown files with templates and three worked examples.
Run `/tenet:tenet`: with no vault yet, it prints the exact `bootstrap.sh` command for your
install. The script's path under the plugin cache is version-specific, so the plugin resolves
it — a literal command printed here would break on the first update.

The bootstrap refuses to write over an existing vault. The vault lives at `~/Claude/brain` by
default; pass a path to put it elsewhere and set `BRAIN_VAULT` to match. The tool and its store
carry different names on purpose: `tenet` is the machinery, the vault is the content, and they
are separate directories with separate lifetimes.

## Language

Section headings are prose, so they have a language. English by default; put one word in the
vault's `_meta/locale` to switch (`hu` ships as a worked example, and a locale is six strings —
see `locales/hu.sh`). The locale belongs to the vault rather than the machine, so a vault carries
its language wherever it is cloned. Frontmatter keys and values stay English either way: scripts
read those, you do not.

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

## Picking up where you left off

`_meta/hot.md` is a short cache of working state — at most 500 words, overwritten rather than
appended, rewritten by the weekly sweep. Its last section, **Active threads**, is the one that
earns the file: what is genuinely open, so the next session knows without being told.

It is injected at session start, but only **in the vault itself or in a directory you have bound**
in `_meta/bindings.md`. That gate is deliberate — a growing knowledge base should not follow you
into an unrelated project — but it has a sharp edge worth knowing: if you work on something in a
directory you never bound, the state exists and is not reachable from the place it describes. Bind
the directory:

```
- `~/code/acme-api` → [[Acme]]
```

A binding with no topic notes behind it is still useful; turning `hot.md` on in that directory is
reason enough.

When Active threads is non-empty, the session-start block says so and offers the first one. A hook
injects context — it does not act on it — so without that line the section sits in front of the
model and nothing picks it up.

The block comes back after a compaction too, since that is where the context went. A `/clear` does
not bring it back: there you asked for a clean slate, while compaction took the context without
asking.

## Renaming

Names change, and this one already has: the repository was `canon` for a day before it was
`tenet`. `skills/tenet/scripts/lib.sh` holds both name pairs — `PLUGIN_NAME` for the machinery
and `BRAIN_NAME` for the vault, each with a `_PREVIOUS_NAMES` list. Set the new name, append the
old one to that list, then run:

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

Three injection points and one always-on cost. Measured at 0.6.1:

| What | Size | When |
| :-- | :-- | :-- |
| three skill descriptions | 1.5 KB | every session, unconditionally — the fourth skill is `disable-model-invocation`, so it costs nothing until you call it |
| session start: `promote.sh` then `resolve.sh` | 0.9 KB on a fresh vault, 11.9 KB on one whose universal layer lists thirty-five notes | startup and resume, and `resolve.sh` again after a compaction |
| response end: the capture prompt | 4.2 KB | every response, gated on the vault's `inbox/` existing — no vault, no cost |
| after every edit: the enforcement hook | nothing | it speaks only when the global `CLAUDE.md` just changed and its table no longer matches |

The session-start block is the one that grows: it lists every `universal` note, and its cap
(`MAX_LIST` in `resolve.sh`) counts lines rather than bytes while each line carries a whole
revisit condition. When the cap bites it says how many notes it withheld — a `head` that drops the
tail in silence is the failure this whole system is about. The weekly sweep speaks earlier, past
roughly fifteen notes, but that is advice rather than a brake. The 11.9 KB above is what
thirty-five cost.

The descriptions carry a deliberate cost of their own: the sweep's more than doubled at 0.6.0,
because the short version measurably failed to fire on half the ways a person asks for
maintenance. A description that does not trigger costs the whole skill.

## Requirements

**Bash 3.2 or newer** — the macOS default is enough. This is bash and not `sh`: the scripts use
process substitution, arrays and here-strings, so a POSIX shell will not run them.

**`jq`**, for one script only: `surface-check.sh`, which reads JSON. Without it that one check
reports that it measured nothing rather than reporting zeroes, and nothing else is affected.

`git` is optional and recommended: the notes are the database, git is the backup. Obsidian is
optional too — it renders wikilinks and frontmatter nicely, and it is what reads the seven `.base`
views the vault ships with. Without it they are inert YAML and nothing else changes: every script
here works on plain files.

**What it reads outside its own tree.** None of this ships with the plugin, and no absence is an
error — each one is a first-run state that says which state it is:

| Path | Read by | Absent means |
| :-- | :-- | :-- |
| `~/Claude/brain` | all of it | no vault yet; `/tenet:tenet` prints the bootstrap command for your install |
| `~/.claude/CLAUDE.md` | the audit and its `PostToolUse` hook | nothing to audit |
| `~/.claude/enforcement.md` | `enforcement-check.sh` | no table yet — it reports how many rules are uncovered, and the hook stays quiet rather than alarming |
| `~/.claude/surface-baseline.json` | `surface-check.sh` | no baseline yet — today's counts, plus the command that records them |
| `~/.claude/settings.json` | `surface-check.sh` | the JSON surfaces read as unmeasured, never as zero |
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

## License

MIT.
