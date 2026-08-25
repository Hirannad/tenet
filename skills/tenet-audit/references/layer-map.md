# Layer Map & Cross-Layer Checks

The instruction files form a precedence stack. Each layer has a job; problems arise when content lands in the wrong layer or is duplicated across layers.

## Precedence (later overrides earlier)

```
1. ~/.claude/CLAUDE.md              global, personal — every project inherits
2. ~/.claude/settings.json          global config: permissions, hooks, model
3. <repo>/CLAUDE.md                 project, team — committed, code-reviewed
4. <repo>/.claude/settings.json     project config: permissions, hooks, MCP
5. <repo>/CLAUDE.local.md           machine-local overrides — NOT committed
6. <repo>/AGENTS.md                 portable instructions (Copilot, Codex, others read it)
7. <repo>/.github/copilot-instructions.md   editor-specific (GitHub Copilot)
```

User instructions always outrank skills and default behavior. A project layer wins over the global layer **only when the override is explicit**.

## What belongs in each layer

| Layer | Belongs here | Does NOT belong here |
|-------|--------------|----------------------|
| `~/.claude/CLAUDE.md` | Personal preferences, autonomy rules, communication style, doc conventions you want everywhere | Project-specific commands, repo structure, team conventions |
| `<repo>/CLAUDE.md` | Project scope, tech stack, build/test commands, structure, team conventions, guardrails | Personal preferences, secrets, machine-specific paths |
| `<repo>/CLAUDE.local.md` | Local ports, machine-specific env, personal scratch rules for this repo | Anything the team needs (it's gitignored — they won't see it) |
| `AGENTS.md` | The portable core other agents also read | Claude-only mechanics; keep those in CLAUDE.md |
| `.github/copilot-instructions.md` | Copilot-editor specifics | A full duplicate of CLAUDE.md |

## AGENTS.md interop pattern

The clean split when both files exist: put the real, portable content in `AGENTS.md` and have a short `CLAUDE.md` import it:

```markdown
@AGENTS.md
```

This avoids maintaining two copies. If you see CLAUDE.md and AGENTS.md with large overlapping content, recommend collapsing to this pattern.

## Cross-layer findings to flag

1. **Duplication** — the same rule appears in two layers. Recommend: keep it in the most-general layer that's still correct, delete the copy. (A global rule restated in a project file is the most common case.)

2. **Undeclared override** — a project file contradicts a global default without saying so. The user's own global convention requires overrides to be flagged explicitly (e.g. "**Override:** this project uses speed-first execution"). Recommend adding that flag, or removing the contradiction.

3. **Misplaced content** —
   - Personal preference found in a committed team file → move to `~/.claude/CLAUDE.md`.
   - Team-needed rule found in `CLAUDE.local.md` → move to `<repo>/CLAUDE.md` (local is gitignored; teammates never see it).
   - Secret / machine path in a committed file → move to local + flag as a leak.

4. **Missing `@`-import** — long shared content copy-pasted across layers or duplicated from a doc that already exists in the repo. Recommend replacing the inline copy with `@path/to/doc.md`.

5. **Copilot drift** — `.github/copilot-instructions.md` is a stale partial copy of CLAUDE.md. Recommend either keeping it deliberately minimal or pointing both at a shared `AGENTS.md`.

## How to use this in the audit

During the cross-layer step, build a quick matrix: for each rule that appears, note which layer(s) it lives in. Any rule in >1 layer is a duplication candidate; any rule contradicting a higher layer without an explicit override flag is a conflict. Report these separately from the per-file scores — they're the findings that single-file tools miss.
