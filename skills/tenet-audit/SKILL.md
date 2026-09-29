---
name: tenet-audit
description: Use when auditing, reviewing, iterating on, or improving CLAUDE.md and related instruction files (CLAUDE.local.md, .claude/rules/, AGENTS.md, managed policy) across global and project layers. Use when the user mentions CLAUDE.md audit, instruction-layer review, memory-file cleanup, checking Claude config against best practices, or whether the tool surface (permissions, plugins, skills, MCP servers) has grown.
allowed-tools: Read, Grep, Glob, Bash(python3 ${CLAUDE_PLUGIN_ROOT}/tenet/cli.py audit *)
---

# Instruction-layer audit

Scores every instruction layer against a rubric, counts what the layers load and duplicate, counts
rules nothing enforces, and diffs the tool surface against a baseline the user accepted. It proposes
fixes; it applies them only on approval. The checks run as
`python3 ${CLAUDE_PLUGIN_ROOT}/tenet/cli.py audit <check> [args]`.

## 1. Discover

Run `audit layers <repo>...` first. Its table is the layer set and each layer's state; only
`measured` means counted, and `absent`, `unreadable`, `excluded`, `unmeasured` are gaps to report,
never a pass. It misses nested monorepo `**/CLAUDE.md` files below the repo root: Glob for those.
`/context` in the audited session shows what actually loaded.

## 2. Score

Apply [the rubric](references/rubric.md) to each file: seven dimensions, 100 points, a grade.
Read it first; do not score from memory.

## 3. Cross-layer check

From the same `audit layers` output: the instruction budget per layer, the duplication clusters and
the negation-pair candidates. Then apply [the layer map](references/layer-map.md) for what the
script does not judge: which layer keeps a duplicate, whether a pair really contradicts, content in
the wrong layer, situational content that should be a `paths:` rule.

## 4. Report

- A table of files by the seven dimensions, with a grade per file, then the cross-layer findings,
  then a fix list ordered by impact.
- Every audited repo: the budget line from `audit layers`, and `audit frontmatter <repo>...`, the
  count of `.md` files missing `title/type/status/updated` that `.claude/frontmatter-exempt` does
  not cover. A CLAUDE.md that restates that schema in prose instead is itself a finding.
- A global audit adds [config hygiene](references/config-hygiene.md), led by the delta from
  `audit surface`, and `audit enforcement`: unmarked rules, orphan rows, empty cells for the user's
  `~/.claude/enforcement.md` ([format](references/enforcement.md)). No table yet is a missing
  mechanism, not a pass; offer to start one.

## 5. Fix on approval

Use the fix under each rubric dimension. Show one diff per issue, apply only after approval, and
keep the file's voice and structure. Re-baselining is a fix too, and the user's to make:

```
python3 ${CLAUDE_PLUGIN_ROOT}/tenet/cli.py audit surface --record > ~/.claude/surface-baseline.json.new
python3 ${CLAUDE_PLUGIN_ROOT}/tenet/cli.py audit layers --record <repo> > ~/.claude/instruction-baseline.json.new
```

They read it and move it into place; never redirect onto the live baseline, which the shell
truncates before the command runs.
