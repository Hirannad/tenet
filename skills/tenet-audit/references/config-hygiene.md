---
title: Config hygiene checks (settings.json, hooks, plugins, memory)
type: reference
status: active
updated: 2026-08-21
---

# Config hygiene checks

Companion checks for the auditor that go **beyond** instruction files (`CLAUDE.md` etc.) to
the surrounding Claude config — `settings.json`, hooks, plugins/MCP, and memory files. The
always-loaded global layer is the largest per-session noise source, so keeping it lean is
high-value. Run these on a global/config audit; report findings, fix only on approval.

## Checks

1. **Permission cruft** — in `settings.json` `permissions.allow/deny`, flag one-off,
   file-specific, or stale entries (e.g. a single pandoc/powershell command for a task long
   done). Generic patterns stay; one-shot specifics go. Offer to remove anything not used
   in the recent window.
2. **Nested `.claude/.claude/`** — flag a nested `.claude/.claude/` hierarchy **only after
   ruling out the legitimate case**. If `~/.claude` is ever opened as a working directory —
   check for a project slug for it under `~/.claude/projects/` — then
   `~/.claude/.claude/settings.local.json` is the **normal project-local settings file** for
   that cwd, written and read by Claude Code itself. It is not a migration artifact.
   Before flagging, check: does a session transcript under that project slug carry
   `stop_hook_summary` records or permission grants that trace to that file? If yes, it is live
   config — audit its *contents* (check 1) instead. Only a nested dir that nothing reads is an
   artifact worth cleanup.
   **This wording is a correction.** The check used to call every nested `.claude/.claude/` an
   artifact, and it produced a confident false positive: an audit declared the file misplaced and
   its hooks dead, and a verification pass then found seven `stop_hook_summary` records proving
   the hook had run, 79–239 ms each, zero errors. A check that reads a normal layout as a defect
   costs more than the defect would have.
3. **Broken / dead hooks** — for every hook `command`, verify the target path exists and is
   reachable from where it runs. Flag relative paths that assume a dir which isn't there
   (e.g. `node .claude/hooks/x.mjs` with no global `hooks/` dir), and hooks pointing at
   deleted files.
4. **Plugin / MCP over-load** — count enabled global plugins + MCP servers. Flag domain-heavy
   or unused ones loaded globally (they dominate per-session context). Default: enable
   domain tools at the **project** layer, not global.
5. **Memory-file staleness** — auto memory lives at `~/.claude/projects/<project>/memory/`,
   where `<project>` is derived from the git repository; `autoMemoryDirectory` (readable from any
   settings scope) relocates it, so resolve the path rather than assuming it. For each `MEMORY.md`
   entry, check it still matches reality (e.g. a note claiming "global settings.json only has the
   model" when it now has permissions/hooks). Flag contradictions; memory files are living docs,
   not snapshots. Three specifics worth checking: only the first **200 lines or 25 KB** of
   `MEMORY.md` load, so anything past that is dead weight that reads as present; a file written by
   Claude carries a `modified` timestamp in its frontmatter, which dates the claim for you; and if
   auto memory is off (`autoMemoryEnabled: false`, or `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`) the
   absence of memories is a **setting, not a clean bill** — say which it was.
6. **Surface growth** — run `scripts/surface-check.sh` and report the **delta** it prints, not
   today's absolute numbers. See below.

## Check 6 — surface growth

Checks 1 and 4 count the surface at a point in time. That is not enough to catch the failure
mode they exist for: the surface grows *quietly*, one justified addition at a time. A single
audit says "25 plugins"; only a baseline says "18 → 25, +39% since the last reset".

`scripts/surface-check.sh` is that comparison. It reads eleven surfaces out of the declarative
config, diffs each against `~/.claude/surface-baseline.json`, and names the added and removed
items where the surface is a list — `+12` tells you to look, the twelve names tell you whether to
keep them. `--baseline FILE` points it elsewhere.

**Why the declarative config rather than what is loaded.** There is no non-interactive way to ask
what is actually active — no file, no CLI command, only an interactive panel. So the measurable
proxy is the config, which is diffable.

`measure()` in the script is one readable case per surface, and that is the list that matters — do
not keep a second copy of it here. Three rows do carry reasoning a reader needs, because all three
were once measured in the wrong place:

| surface | what it reads, and why that and not the obvious thing |
| :-- | :-- |
| `enabled_plugin_skills` | every `SKILL.md` under the `installPath` that `plugins/installed_plugins.json` records for each **enabled** plugin. Not the cache tree: `cache/<marketplace>/<plugin>/` keeps every version ever installed, some named by commit SHA rather than semver, so counting it counted history — 111 files on a machine where 15 descriptions load, rising with every plugin update |
| `user_scope_mcp` | `~/.claude.json` → `mcpServers`, which is where `claude mcp add -s user` writes. Not `~/.claude/.mcp.json`, a path Claude Code never creates, which made this surface a zero that could never become anything else |
| `global_hook_entries` | the leaf commands under `.hooks`, not its keys. There are only about nine hook events, so counting event names saturates at once and five hooks added under an existing event registered as no growth |

Project-scope MCP servers are deliberately not diffed: domain tools belong at the project layer,
so a `<repo>/.mcp.json` appearing there is the intended behaviour rather than growth.

All three were the same mistake, caught by an adversarial pass and not by the state-by-state
testing that preceded it: **measuring a place rather than the thing.** Every input state can be
covered and every branch exercised while the number still answers a different question than the one
asked. When a surface here reads suspiciously flat, suspect the reading before the reality.

**Reporting rule.** Any net growth gets a line with the added items named, wherever the baseline
recorded the items to name. A grant, plugin, skill or server nobody can justify out loud is a
removal candidate. Zero growth is also worth one line: it means the constraint is holding. And
`grown`, `shrunk`, `unchanged`, `unread` (nothing readable), `unbaselined` (counted, never
accepted), `unusable` (the baseline holds something that is not a count) and `untracked` (the
baseline tracks a surface this no longer measures) are seven different states — **only `unchanged`
means nothing grew**, so never report the others as calm.

**Re-baselining is the user's, never the script's.** `--record` prints a fresh baseline to stdout
and leaves the redirect to them; nothing writes that file on its own. Offer it only once they have
accepted the current state as intentional — a baseline that updates itself erases the signal it
exists to produce. Recorded counts carry no notes: those are written by hand, because why an
addition was accepted is the part a diff cannot reconstruct.

**If the user has a recorded decision to keep their tool surface small, this check is its
enforcement cell.** Such a decision reverses on something like "if the surface starts growing
unnoticed again" — and something has to be the thing that notices.

The script needs `jq`, for the JSON surfaces and for the baseline itself. Without it, it reports
that it measured nothing rather than reporting zeroes.

## What happened to this check's own replacement trigger

It used to carry one: *when plugins arrive, or skills come from more than two sources, adopt a
real lockfile-based tool — APM (`github.com/microsoft/apm`) declares agent primitives in
`apm.yml`, and `apm audit` rebuilds the agent context and diffs it — and delete this check plus
the baseline.*

That condition fired: plugins arrived, and this system became one. The verdict taken on
2026-08-21 was to build the diff rather than adopt the dependency — the surface being watched is
one machine's `~/.claude`, the mechanism is a single script whose only state is a JSON file the
user owns, and a package manager for agent primitives is a larger commitment than the problem.
Until that day the check was prose asking the model to compare by hand, which is why the promise
outran the code for as long as it did.

**The trigger now**, and this time countable off what the script itself prints: when more than two
surfaces sit at `unusable` or `untracked` across consecutive audits — the baseline has drifted out
of shape faster than it is being re-accepted — or when a lockfile tool reads Claude Code's own
config format directly. Either replacement is a tool, not more prose. The trigger it replaced
("hand-edited more often than read") was not observable by anything, which is the standard this
system applies to every `revisit` field it ships.

**Why measure at all.** One recorded case: an inventory three months after a full config reset
found 25 enabled plugins where an earlier count had 18 — and 15 of the 25 had never fired once. A
one-off cleanup does not keep anything clean; only a repeated measurement with a recorded baseline
does, because each individual addition looks justified at the moment it is made.

## Output

Fold into the auditor's Report step as a "Config hygiene" section: a bulleted findings list
with the exact file/line and a one-line remediation each. Surface growth (check 6) leads that
section when there is any delta, because it is the only check that measures a trend rather
than a state. Apply only after approval, one issue at a time (never bulk-rewrite
settings.json silently).

## Where these checks came from

Each one is a defect that actually happened, not a category invented for completeness: permission
cruft, plugin and MCP over-load, stale memory files, a global hook pointing at a path that had
moved, a nested `.claude` misread as an artifact. Nothing here is derived from published guidance —
config hygiene is not a well-covered topic, and these are local findings.

That matters when you use this file: a check earns its place by having caught something. If one of
them has never fired on your setup after a few audits, it is measuring someone else's problem, and
deleting it beats running it.
