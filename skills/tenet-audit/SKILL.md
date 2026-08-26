---
name: tenet-audit
description: Use when auditing, reviewing, iterating on, or improving CLAUDE.md and related instruction files (CLAUDE.local.md, .claude/rules/, AGENTS.md, managed policy) across global and project layers. Use when the user mentions CLAUDE.md audit, instruction-layer review, memory-file cleanup, checking Claude config against best practices, or whether the tool surface (permissions, plugins, skills, MCP servers) has grown.
---

# CLAUDE.md Auditor

Audits and improves the user's Claude instruction files across **every layer** — the managed policy file, global `~/.claude/CLAUDE.md` and `~/.claude/rules/`, project `CLAUDE.md` and `.claude/rules/`, and `CLAUDE.local.md` — against a rubric synthesized from 43 CLAUDE.md files in public repositories. It scores each file, flags cross-layer duplication and undeclared overrides, then proposes surgical fixes you approve before any edit.

It also measures **tool-surface growth** over time (permissions, plugins, skills, agents, hooks, MCP servers) by diffing eleven surfaces against a baseline you accepted, because that surface grows one justified addition at a time and only a comparison catches it.

## When to use

- "Audit / review / improve my CLAUDE.md"
- "Check my Claude config against best practices"
- "Is my CLAUDE.md too long / ignored / messy?"
- "Has my setup grown? What did I add since last time?"
- After a session where instructions drifted, or before sharing a repo.

## Workflow

Work through these five steps in order. Create a TodoWrite item per step for multi-file audits.

### 1. Discover
Find every instruction file in scope. Use Glob/Read — do not assume paths.
- Managed policy: macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`, Linux/WSL `/etc/claude-code/CLAUDE.md`, Windows `C:\Program Files\ClaudeCode\CLAUDE.md`; also the `claudeMd` key in `managed-settings.json`
- Global: `~/.claude/CLAUDE.md` (on Windows: `C:\Users\<user>\.claude\CLAUDE.md`)
- Global rules: `~/.claude/rules/**/*.md`
- Project: `<repo>/CLAUDE.md` **or** `<repo>/.claude/CLAUDE.md`, plus nested/monorepo `**/CLAUDE.md`
- Project rules: `<repo>/.claude/rules/**/*.md` — note which carry `paths:` frontmatter, since those load only when a matching file is read
- Local: `<repo>/CLAUDE.local.md`
- Portable: `<repo>/AGENTS.md` — **not a layer** (Claude Code does not read it); in scope only as the target of an `@AGENTS.md` import

List what exists. Note line counts (the size dimension needs them).

A layer you did not open is **unexamined, not clean** — say which of the above you could not read
and why. The rules directories and the managed policy file are the two most often missed, and an
audit that silently skips them reports a passing grade on a stack it never saw. Run `/context` in
the session under audit to see which files actually loaded, and check `claudeMdExcludes` across
settings layers before concluding a present file is in play.

### 2. Score
Apply `references/rubric.md` to each file: 7 dimensions, a point score each, a letter grade per file. Read the rubric file before scoring — do not score from memory.

### 3. Cross-layer check
Apply `references/layer-map.md`. Look for:
- Same rule duplicated across layers (e.g. a global default repeated in a project file).
- A project layer that contradicts the global default **without declaring it as an override**.
- Content sitting in the wrong layer (personal prefs in a repo file; team rules in a personal file).
- Situational content that should be a `paths:`-scoped rule in `.claude/rules/`. Do **not** recommend
  an `@`-import to shrink a file — imports expand at launch and do not reduce context.
- A layer that went unexamined (see step 1) — reported as such, never folded into a pass.

### 4. Report
Output a compact report:
- A table: files (rows) × 7 dimensions (cols) with scores, plus a per-file grade.
- Cross-layer findings as a bulleted list.
- A **prioritized** fix list — highest-impact first (e.g. "global file 480 lines → split" beats "rephrase one sentence").
- For a **global/config audit**, also run `references/config-hygiene.md` (settings.json permission cruft, broken hooks, nested `.claude/`, plugin/MCP over-load, memory-file staleness, and **surface growth vs the recorded baseline**) and add a "Config hygiene" section to the report. Check 6 there is a script, not a procedure: run `scripts/surface-check.sh` from this skill's base directory — same rule as below, never from a remembered absolute path. Lead the section with its delta whenever there is one, and report `unread` / `unbaselined` / `untracked` / `unusable` surfaces as gaps rather than folding them into "unchanged" — only `unchanged` means nothing grew.
- For a **global audit**, also run `scripts/enforcement-check.sh`, resolved from this skill's base directory (the harness prints it when the skill loads). Never from a remembered absolute path — the plugin cache path carries a version number. It reads the user's own table at `~/.claude/enforcement.md`; `references/enforcement.md` here is the format and one worked example, not anybody's data. If the user has no table yet, say so and offer to start one — that is a missing mechanism, not a passing check. It reports three numbers: unmarked rules, orphan rows, empty cells. **An unmarked rule is itself the defect** — every rule in the global CLAUDE.md carries a row saying what catches it, or `none` and the reason. Put the three numbers next to the surface-growth delta at the top, and propose an enforcement cell for anything unmarked. A `PostToolUse` hook runs the same script on every CLAUDE.md edit, so a non-zero count here means an edit slipped through outside a session.
- For **every audited repo**, run `scripts/frontmatter-check.sh <repo>...` from the same base directory. It is the mechanism behind the `title`/`type`/`status`/`updated` rule: exemptions live in each repo's `.claude/frontmatter-exempt` (a glob per line, with the reason as a comment), and anything else missing frontmatter is a defect. Report the count. **Do not accept a project CLAUDE.md that restates the schema in prose** — a rule restated instead of mechanised is the third path, the one that grows the rule list while compliance falls. The prose points at the exemption file; the file is what the check reads. This check exists because the rule was found broken 21 times across four repositories with nothing noticing.

### 5. Fix on approval
Propose concrete diffs using `references/rewrite-recipes.md`. Show the diffs; apply **only after the user approves**. Surgical changes only — touch one issue at a time, never bulk-rewrite a whole file silently. Preserve the file's existing voice and structure.

Re-baselining the surface counts as a fix: offer it, never do it silently — an auto-updated baseline erases the signal it exists to produce. The script cannot do it for you either; it prints a baseline with `--record` and the user redirects it themselves:

```
bash scripts/surface-check.sh --record > ~/.claude/surface-baseline.json.new
```

Then have them read it and move it into place. Never redirect straight onto the live baseline: the shell truncates the target before the script runs, so a record that goes wrong destroys the accepted file — and its hand-written notes are the part no re-run can reconstruct.

The recorded counts carry no notes. Offer to write the per-surface reason by hand afterwards — why an addition was accepted is the part the next diff cannot reconstruct.

## Quick rubric (one-line checklist)

1. **Size** — ≤200–300 lines; rules separated from context.
2. **Mandatory content** — build/test commands, structure, conventions, guardrails.
3. **Style** — second-person, negatives, specific not vague.
4. **Compliance** — `<important if="…">` on conditional sections; identity/structure left unwrapped.
5. **No anti-patterns** — no linter rules, stale snippets, vague text, full arch dumps.
6. **Layer hygiene** — no cross-layer duplication; overrides explicit; right content in right layer; `@`-imports.
7. **Freshness** — no dead paths, stale versions, deprecated commands.

For deep audits read all five reference files (`rubric.md`, `layer-map.md`, `rewrite-recipes.md`, `config-hygiene.md`, `enforcement.md`). For a quick pass, the checklist above is enough.
