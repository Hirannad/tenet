---
title: How tenet is built
type: reference
status: active
updated: 2026-08-28
---

# How tenet is built

The README says what this plugin is for. This document says what is in it: every script, when it
runs, what it reads, what it writes, and — for the two cases where the answer is unflattering —
whether shell was the right language for it.

Read this if you are deciding whether to trust the thing, extending it, or looking for the pattern
rather than the product. Nothing here is needed to *use* it.

## The shape

Four skills, one shared library, three hook events, fourteen shell scripts, 2,292 lines of shell
against 3,598 lines of markdown. (The previous figure said 1,849 for thirteen scripts and was ten
lines stale — `rename-check.sh` grew by that much when 2.1.0 added its eighth check, and nothing
recounted. Both numbers here are `grep -c ''` over the tree, and so is the table below.) No `commands/` directory, because custom commands and skills
are the same mechanism on this platform now and `/tenet:tenet` is the modern form. No agents, no
MCP server, no network call anywhere.

```
tenet/
├── .claude-plugin/
│   ├── plugin.json          manifest + userConfig (the store's path, typed `directory`)
│   └── marketplace.json     a one-plugin marketplace, so `/plugin marketplace add` works
├── hooks/
│   ├── hooks.json           3 events, 4 commands. Resolves no path of its own — check 8 enforces
│   ├── on-stop.sh           the capture gate, at the end of a response
│   └── on-claude-md-edit.sh the enforcement check, after an edit to the global CLAUDE.md
├── skills/
│   ├── tenet/               READ. Also the library: scripts/lib.sh
│   ├── tenet-capture/       WRITE drafts. User-invoked only
│   ├── tenet-sweep/         the weekly pass. Writes one digest, proposes everything else
│   └── tenet-audit/         the instruction layer. Also the shared checker directory
├── locales/hu.sh            six section-heading strings — the whole locale interface
└── vault-template/          what bootstrap.sh copies to make a store
```

**Two conventions the directory names do not tell you**, and both matter if you move things:

- **`skills/tenet/scripts/lib.sh` is the library.** `tenet-capture` and `tenet-sweep` source it
  across skill boundaries (`../../tenet/scripts/lib.sh`), so renaming the `skills/tenet/` directory
  breaks them. Both say so when it happens rather than failing quietly.
- **`skills/tenet-audit/scripts/` is the shared checker directory.** `enforcement-check.sh` has
  three callers: the audit skill, the `PostToolUse` hook, and `promote.sh` — which runs it in
  `--empty-only` mode against the *store's* own conventions file. One checker, two targets, which
  is the plugin's thesis applied to itself: a rule and a decision are the same object at two
  altitudes, so the same check scores both. `layer-check.sh` joined the directory in 2.2.0 and has
  one caller, the audit skill's third and fourth steps.

## When each thing runs

| Trigger | What runs | Reaches the model? |
| :-- | :-- | :-- |
| `SessionStart` (`startup`, `resume`) | `promote.sh`, then `resolve.sh` | yes — stdout on these events is added to context |
| `SessionStart` (`compact`) | `resolve.sh` | yes. `clear` is deliberately unmatched: there you asked for a clean slate |
| `PostToolUse` (`Edit`, `Write`) | `on-claude-md-edit.sh` | only on exit 2, via stderr |
| `Stop` (end of every response) | `on-stop.sh` | yes — via `hookSpecificOutput.additionalContext`, which is the **only** channel that works here |
| `/tenet:tenet` | `resolve.sh --interactive` in a `!`-block | injected into the skill body before the model sees it |
| `/tenet:tenet-capture` | `inbox.sh` in a `!`-block | same |
| `/tenet:tenet-sweep` | `inventory.sh` in a `!`-block | same |
| `/tenet:tenet-audit` | `layer-check.sh` at step 3; `surface-check.sh`, `enforcement-check.sh`, `frontmatter-check.sh` at step 4 | as tool output |
| by hand, before a release | `rename-check.sh` | it is for you, not the model |
| by hand, once | `bootstrap.sh` | prints what it created |

**The `Stop` row is the one worth knowing about.** A hook's plain stdout on exit 0 reaches the model
for `SessionStart`, `UserPromptSubmit` and `UserPromptExpansion` — and for no other event. Until
2.1.0 this plugin's capture gate was `cat`-ed to stdout from a `Stop` hook, so it had never once
been delivered. If you are writing a hook, measure the channel before you trust it.

## Every script

`lib.sh` is sourced, never executed. Everything else exits 0 except `rename-check.sh`, which is
the only script that gates, and the three that are allowed to fail an invocation
(`bootstrap.sh`, `inbox.sh`, `inventory.sh`, `frontmatter-check.sh`).

| Script | Lines | When | Reads | Writes | Exit |
| :-- | --: | :-- | :-- | :-- | :-- |
| `skills/tenet/scripts/lib.sh` | 224 | sourced by all | the four path sources, `_meta/locale`, `locales/*.sh` | — | n/a |
| `skills/tenet/scripts/resolve.sh` | 181 | SessionStart ×2, `/tenet:tenet` | the store root, `_meta/bindings.md` | — | always 0 |
| `skills/tenet/scripts/promote.sh` | 182 | SessionStart | `inbox/`, `_meta/maintenance-*`, `conventions.md` | **`git mv` inside the store**, `inbox/` → root | always 0 |
| `skills/tenet/scripts/bootstrap.sh` | 77 | by hand, once | `vault-template/` | **creates the store** | 1 on refusal |
| `skills/tenet/scripts/rename-check.sh` | 291 | by hand, pre-release | a wide surface incl. `~/.claude` and the Obsidian registry | — | **1 on any finding** |
| `skills/tenet-capture/scripts/inbox.sh` | 37 | `/tenet:tenet-capture` | `inbox/`, the store root | — | 1 if the store is unusable |
| `skills/tenet-sweep/scripts/inventory.sh` | 194 | `/tenet:tenet-sweep` | the whole store, `settings.json`, the auto-memory tree | — | 1 if the store is unusable |
| `skills/tenet-audit/scripts/enforcement-check.sh` | 129 | audit step 4, PostToolUse hook, `promote.sh` | an instruction file + its enforcement table | — | always 0 |
| `skills/tenet-audit/scripts/frontmatter-check.sh` | 68 | audit step 4 | every `.md` in a repo, `.claude/frontmatter-exempt` | — | 1 on an undeclared violation |
| `skills/tenet-audit/scripts/layer-check.sh` | 433 | audit steps 3 and 4 | six instruction layers, `claudeMdExcludes`, the auto-memory tree, a baseline | **never** — `--record` prints to stdout | always 0 |
| `skills/tenet-audit/scripts/surface-check.sh` | 296 | audit steps 4 and 5 | eleven config surfaces + a baseline | **never** — `--record` prints to stdout | always 0 |
| `hooks/on-stop.sh` | 82 | Stop | the payload on stdin, `stop-prompt.md` | — | always 0 |
| `hooks/on-claude-md-edit.sh` | 68 | PostToolUse | the payload on stdin, `enforcement-check.sh` | — | 2 on a mismatch |
| `locales/hu.sh` | 30 | sourced by `lib.sh` | — | — | n/a |

**Three of the fourteen write anything at all.** `bootstrap.sh` creates the store. `promote.sh`
moves an approved draft out of `inbox/`, with `git mv` when the store is a repo — worth knowing,
because an unattended `SessionStart` therefore leaves a staged rename in a repository you did not
touch. The sweep skill may write one digest note. Nothing else writes, and nothing writes under
`~/.claude` — the two scripts that produce a baseline both print it to stdout and leave the redirect
to the user, because a baseline that updates itself erases the signal it exists to produce.

## Why shell, and where it is the wrong answer

Shell is a defensible default here and an indefensible one for two of these files, and the way to
tell them apart is to ask what the script is actually manipulating.

**Measured rather than asserted:** across the 39 plugins in the official Anthropic directory there
are 43 `.py` files and 19 `.sh`. The pattern is consistent — shell for installers, environment
checks and thin hook wrappers; Python, with a `scripts/lib/` module directory, wherever a plugin
does real data work (`claude-security` ships a `sarif.py` and a `strictjson.py`; `hookify` writes
its hook handlers in Python). By that yardstick this repository is shell-heavy but not an outlier:
the official `plugin-dev` plugin ships 1,142 lines of it.

**Where shell is right, and stays:** `bootstrap.sh` is `mkdir`, `cp -R`, `rm`, `find | wc -l` —
its whole job is moving files. `frontmatter-check.sh` matches shell globs read from a file against
paths, with `case "$rel" in $pat)`, which no other language does more naturally. `resolve.sh` and
`promote.sh` are globbing, `grep` and `git mv`. `rename-check.sh` really does only `grep`.
`on-stop.sh` and `on-claude-md-edit.sh` are hook handlers reading a payload and dispatching.

**Where it is not, stated plainly:**

- **`surface-check.sh` (296 lines) is a `jq` program wrapped in glue.** It reads JSON with `jq` and
  writes JSON with `printf`; it emulates out-parameters with four global variables; it classifies
  into six states with integer arithmetic; and its membership test is a space-padded string
  (`SURFACE_SET=" $(echo $SURFACES) "`) that relies on unquoted word splitting — a construction
  whose own comment records that it once reported four measured surfaces as never-measured. In
  Python this is a dict and a `json.load`, and the `jq` dependency — the plugin's only external
  requirement — disappears with it.
- **`inventory.sh` (194 lines)** does a frontmatter-scoped tally with `awk` fence tracking, a
  multi-file join for the dead-wikilink check, JSON settings parsing with `sed`, and a
  four-by-three state machine. Same class.

- **`layer-check.sh` (433 lines) is the largest script in the tree, and it is two things at once.**
  Its counting and normalization is `awk` — per-line frontmatter, fence and comment tracking, then a
  string normalizer — and that is shell being used for what shell is good at. Its two *JSON* reads
  are not: `claudeMdExcludes` and the baseline's `total_directives` both come out of `sed` captures,
  which is `surface-check.sh`'s defect at one tenth the size. Those two functions belong in the same
  Python rewrite, and they are the reason the rewrite moved up the list rather than down when this
  script shipped.

All three are scheduled for rewriting, and `surface-check.sh` first — 2.2.0 identified a check it
should grow (a permission grant naming an MCP server that no longer exists: the eleven surfaces are
counted independently and never cross-referenced, so that grant passes today) and adding it in shell
would mean growing the wrong language. They are named here rather than left for a reader to notice,
because a repository whose subject is unenforced claims should not have an unstated one.

## The house rules the code actually implements

Four, and each one is in the tree because it was violated first.

**No silent zero.** A check that found nothing must be distinguishable from a check that looked at
nothing. `surface-check.sh` has seven states of which only one means calm; `inventory.sh` prints a
status line naming which of four reasons produced an empty memory read; `frontmatter-check.sh`
prints `checked` and `exempted` side by side so coverage is visible instead of inferred;
`enforcement-check.sh` distinguishes a missing table from an unreadable one.

**Two states, not one.** "Missing" is almost always two different things. A configured store path
that is not there is broken configuration and shouts. The default path not existing yet is a first
run and stays quiet, because shouting a repair procedure at someone with nothing to repair is noise
in every session forever.

**A rule that breaks twice gets a mechanism, or gets deleted.** Writing it down again is neither.
`rename-check.sh` exists because care failed twice at the same task.

**Errors go to stdout, on purpose.** The hooks pipe stderr to `/dev/null` (`2>/dev/null || true`),
so stderr is exactly where a message goes to disappear. The one exception is `on-stop.sh`, whose
stdout is a JSON channel — and there `lib.sh` hands its warnings back through
`TENET_LIB_NOTICE` so they travel with the payload instead of being dropped by the caller that
needed a clean pipe.

## Verification

What runs before a release, and what each one covers:

```bash
bash skills/tenet/scripts/rename-check.sh          # 8 checks; exits 1 on any finding
claude plugin validate .claude-plugin/plugin.json  # pass the PLUGIN manifest, not the repo root
bash skills/tenet-audit/scripts/frontmatter-check.sh .
bash skills/tenet-audit/scripts/layer-check.sh .   # 6 layers, budget, duplication, override candidates
claude plugin details tenet                        # component inventory + projected token cost
```

Pass `validate` the plugin manifest explicitly. Given the repository root it finds
`marketplace.json` first, validates only that, and passes — having walked no skill and no hook.
That difference hid a defect for a few minutes during 0.6.0: one unquoted `": "` in a description
made the whole frontmatter unparseable, and the skill would have shipped loading with no metadata
at all.

One warning is expected and will not clear: `CLAUDE.md at the plugin root is not loaded as project
context`. It is this repository's own instructions, correctly loaded when you work *in* the repo and
inert in an installed copy. That is why CI does not use `--strict`.

Test scripts against a throwaway store, never a real one:

```bash
bash skills/tenet/scripts/bootstrap.sh /tmp/scratch/ledger
TENET_LEDGER=/tmp/scratch/ledger bash skills/tenet/scripts/resolve.sh --interactive
```
