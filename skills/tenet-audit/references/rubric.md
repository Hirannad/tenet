# Scoring Rubric

Score each instruction file on 7 dimensions (100 points total). Sum → letter grade.
Synthesized in 2026-08 from 43 CLAUDE.md files in public repositories and three industry write-ups. The source list is not reproduced here — it was collected without permission to cite, and a rubric that needs its provenance to be convincing is the wrong rubric. Judge it on whether the dimensions catch real defects in your own files.

For each dimension, score toward **full** when all pass-signals hold, toward **zero** when fail-signals dominate. Partial credit is fine — state the deductions.

---

## 1. Size & scope — 15 pts

What it checks: the file is short enough to stay in effective context, and behavioral **rules** are not tangled with reference **context**.

**Pass signals**
- Under 200 lines. That is the documented target, and adherence drops above it; ≤300 is tolerable only for a large monorepo root.
- Rules (how to behave) live here; deep context (schemas, full deploy flows, query patterns) is in skills/docs and linked, not inlined.
- Each section earns its place — no filler.

**Fail signals**
- >300 lines, or growing append-only with no pruning. (A file over 4 MiB is skipped outright, which is a different and rarer failure — if you ever see one, that is the whole finding.)
- Schema dumps, long API tables, or tutorial-length prose inlined.
- Mixed rules + reference in the same section.

Deduct ~5 pts per major overflow (length, or rules/context entanglement).

When the finding **is** length, the fix is a `paths:`-scoped rule under `.claude/rules/`, not an
`@`-import: an imported file expands at launch and costs the same context it did inline. Recommend
the import only to remove a duplicate.

---

## 2. Mandatory content — 20 pts

What it checks: the four things present in essentially every production file. Without these, the agent works blind.

**Required (5 pts each)**
- **Build/test commands** — exact, copy-paste-ready (`make test`, `pnpm build`, etc.).
- **Project structure** — key directories, one line each; auto-generated paths flagged "do NOT edit".
- **Conventions** — commit format (conventional commits is near-universal), naming, import order.
- **Guardrails** — the hard "never" rules (secrets handling, don't edit generated files, don't leak sensitive data).

**Fail signals**
- Commands missing, wrong, or vague ("run the tests").
- No structure map, or generated files unmarked.
- No guardrails at all.

Award per item present and accurate; partial credit if present but imprecise.
(Note: a tiny library or a personal global file may legitimately lack some — judge against the file's purpose, and say so rather than penalizing blindly.)

---

## 3. Writing style — 15 pts

What it checks: phrasing that production teams found lands hardest with the model.

**Pass signals**
- **Second person**: "You always check the ticket before touching code" — not "Claude should…".
- **Negatives for hard limits**: "Never suggest a fix without reading the failing test first" beats a soft positive.
- **Specific & verifiable**: "Use typed errors (`RequestError`), check with `errors.As`" — not "handle errors properly".

**Fail signals**
- Third-person/passive ("Claude should consider…").
- Vague exhortations with no actionable test ("write clean code", "be careful").

Deduct ~5 pts per pervasive style problem.

---

## 4. Compliance technique — 15 pts

What it checks: use of conditional blocks so the model actually applies situational rules. CLAUDE.md is delivered wrapped in a system reminder framed as "may or may not be relevant"; long undifferentiated files get treated as optional. Conditional gating fixes this.

**Pass signals**
- Situational sections wrapped: `<important if="you are writing or modifying tests">…</important>`.
- Conditions are **narrow** (fire only when truly relevant).
- Foundational content (project identity, directory structure, tech stack) left **unwrapped** — it's always relevant.
- Where a section applies to a *file set* rather than a *task*, a `paths:`-scoped rule in `.claude/rules/` is the stronger form: the harness decides when it loads, instead of the model deciding whether the condition matched.

**Fail signals**
- Everything flat, no gating, in a long file → sections get ignored.
- Over-wrapping: `<important if="you are writing code">` matches everything, defeats the purpose.
- Foundational content needlessly wrapped.

Full marks for a short file that needs no gating; deduct when a long file with clearly situational sections uses none.

---

## 5. Anti-patterns absent — 15 pts

What it checks: the file is free of content that belongs elsewhere or has rotted.

**Deduct for each present (~4 pts each)**
- **Linter-enforceable rules** (indentation, quote style, line length) — belong in `.eslintrc`/`.prettierrc`, not here.
- **Stale code snippets** — examples that have drifted from the real source.
- **Vague instructions** that aren't actionable.
- **Full architecture docs** inlined — should be `@ARCHITECTURE.md` / an ADR.

**Pass signals**
- Style enforcement delegated to tooling; examples minimal and current; heavy docs linked.

---

## 6. Layer hygiene — 15 pts

What it checks: this file plays well with the other layers. (Scored per file but informed by the cross-layer pass — see `layer-map.md`.)

**Pass signals**
- No rule duplicated from another layer.
- Any deviation from a global default is **explicitly flagged as an override**.
- Content matches the layer (personal prefs → global; team rules → project; machine specifics → local).
- Content shared across layers `@`-imported once, not copy-pasted (imports deduplicate; they do not shrink).
- Rules directories (`~/.claude/rules/`, `<repo>/.claude/rules/`) and the managed policy file examined, not assumed absent.

**Fail signals**
- Global rules restated in a project file (or vice versa).
- Silent contradictions between layers.
- Personal preferences committed in a team file.

Deduct ~5 pts per duplication/misplacement/undeclared-override.

---

## 7. Freshness — 5 pts

What it checks: nothing has rotted.

**Fail signals**
- Dead file paths, renamed directories.
- Stale version pins or deprecated model IDs in examples.
- Commands that no longer exist.

Full marks unless concrete rot is found.

---

## Grade bands

| Total | Grade | Meaning |
|-------|-------|---------|
| 90–100 | A | Exemplary — leave it alone. |
| 75–89  | B | Solid; minor targeted fixes. |
| 60–74  | C | Works but has real gaps; worth a focused pass. |
| 40–59  | D | Several structural problems; recommend a rewrite of the worst sections. |
| <40    | F | Likely being ignored by the model; rework needed. |

Always pair the grade with the 2–3 highest-impact fixes — a score alone isn't actionable.
