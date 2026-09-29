# Scoring rubric

Seven dimensions, 100 points. Score toward full when the pass signals hold, toward zero when the
fail signals dominate; partial credit is fine, and every deduction is stated. Each dimension ends
with its fix; apply one fix per diff, show it, and wait for approval.

## 1. Size & scope — 15

Pass: the instruction count across layers is inside the budget `cli.py audit layers` prints
(adherence degrades uniformly past ~150–200 instructions, of which Claude Code's own prompt spends
~50); rules live here, deep reference (schemas, full flows) is linked; every section earns its
place. Fail: over budget or over ~300 lines and growing append-only; reference inlined; rules and
context tangled. Deduct ~5 per major overflow. A layer the script could not measure is
unexamined, not small.

Fix: move a situational section into a `paths:`-scoped rule, which loads only when a matching file
is read. An `@`-import does not shrink anything: it expands at launch.

```diff
+ # .claude/rules/api.md
+ ---
+ paths:
+   - "src/api/**/*.ts"
+ ---
+ - Validate input with the shared schema helper
```

A rule file without `paths:` loads unconditionally and saves nothing.

## 2. Mandatory content — 20

Five points each: exact build/test commands; a structure map with generated paths marked "do NOT
edit"; conventions (commits, naming); guardrails (secrets, generated files). Judge against the
file's purpose: a personal global file may legitimately lack some, and the report says so.

Fix: add the missing item, exact and copy-paste-ready; mark generated files inline.

## 3. Writing style — 15

Pass: second person ("You always check the ticket"); hard negatives for real limits ("Never
suggest a fix without reading the failing test"); specific and checkable rules. Fail: third person
or passive; exhortations with no test ("write clean code"). Deduct ~5 per pervasive problem.

Fix: rewrite the sentence in second person, as a negative if it is a bright line, and with the
concrete check (`errors.As`, not "handle errors properly").

## 4. Compliance technique — 15

CLAUDE.md arrives framed as "may or may not be relevant", so a long flat file reads as optional.
Pass: situational sections gated with a narrow `<important if="…">`; identity, structure and stack
left unwrapped; a section that applies to a file set is a `paths:` rule instead. Fail: a long file
with no gating; a condition that always matches (`if="you are writing code"`); foundational
content wrapped. A short file that needs no gating gets full marks.

Fix:

```diff
+ <important if="you are writing or modifying tests">
  - Use createTestApp() for integration tests
+ </important>
```

## 5. Anti-patterns absent — 15

Deduct ~4 each: linter-enforceable rules (indentation, quotes, line length); stale snippets; vague
instructions; architecture docs inlined.

Fix: delete a linter rule and point at the tool that enforces it; replace an inlined document with
a one-line pointer; refresh or remove a stale snippet.

## 6. Layer hygiene — 15

Pass: no rule duplicated across layers; a deviation from a global default is declared as an
override; content sits in its layer (personal → global, team → project, machine → local); the rules
directories and the managed policy were examined. `cli.py audit layers` counts the duplicates and
the negation-pair candidates; deciding which layer keeps a rule, and whether a pair really
contradicts, is this dimension's judgement. A contradiction with no shared wording is invisible to
the script, so a full score says which part you read yourself. Deduct ~5 per duplication,
misplacement or undeclared override.

Fix: delete the copy from the layer that should not own it; flag a deliberate deviation; move
misplaced content, saying where and why.

```diff
+ **Override (global default is ask-first):** this project is speed-first.
```

## 7. Freshness — 5

Fail: dead paths, stale versions or model ids, commands that no longer exist. Full marks unless
concrete rot is found. Fix: correct or delete the rotten line.

## Grades

| Total | Grade | Meaning |
| :-- | :-- | :-- |
| 90–100 | A | leave it alone |
| 75–89 | B | minor targeted fixes |
| 60–74 | C | real gaps; worth a focused pass |
| 40–59 | D | structural problems; rewrite the worst sections |
| < 40 | F | likely ignored by the model |

Always pair the grade with the two or three highest-impact fixes.
