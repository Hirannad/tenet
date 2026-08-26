# Rewrite Recipes

Concrete before/after transforms for the fix step. Apply one at a time, show the diff, get approval. Preserve the file's voice.

---

## 1. Third person → second person

Second person lands harder with the model.

```diff
- Claude should check the Linear ticket before touching code.
+ You always check the Linear ticket before touching code.
```

```diff
- It is recommended that the agent runs the tests after each change.
+ Run the tests after each change.
```

---

## 2. Soft positive → hard negative (for real limits)

Negatives read as bright lines; reserve them for things that must not happen.

```diff
- Remember to read the failing test before fixing.
+ Never suggest a fix without reading the failing test first.
```

```diff
- Try to keep secrets out of logs.
+ Never log anything derived from secrets.ejson.
```

---

## 3. Vague → specific & verifiable

Every rule should be checkable.

```diff
- Handle errors properly.
+ Use typed errors (e.g. RequestError); check with errors.As. User-facing errors go to stderr.
```

```diff
- Write good tests.
+ Use testify/require; mock HTTP with httptest.NewServer; one behavior per test.
```

---

## 4. Flat section → conditional `<important if>`

Gate situational rules so they fire only when relevant. Keep the condition narrow.

```diff
- ## Testing
- - Use createTestApp() for integration tests
- - Mock the database with dbMock from packages/db/test
- - Fixtures live in __fixtures__/
+ <important if="you are writing or modifying tests">
+ - Use createTestApp() for integration tests
+ - Mock the database with dbMock from packages/db/test
+ - Fixtures live in __fixtures__/
+ </important>
```

Do **not** wrap project identity, directory structure, or tech stack — those are always relevant. Do **not** use a condition so broad it always matches (`if="you are writing code"`).

---

## 5. Duplicated doc → `@`-import

Stop keeping two copies of content that lives elsewhere. Note what this does **not** buy: the
imported file is expanded at launch, so context cost is unchanged. Reach for this when the same
text appears in more than one place, never to make a long file shorter — recipe 10 does that.

```diff
- ## Testing Guide
- (40 lines describing the full test setup, Docker, fixtures, coverage…)
+ ## Testing
+ See @docs/TESTING.md for the full setup. Quick commands:
+ - `make test` — unit + integration
```

---

## 6. Linter rule → delete + delegate

Style enforcement belongs in tooling, not in the instruction file.

```diff
- ## Code Style
- - Use 2-space indentation
- - Single quotes for strings
- - Max line length 100
- - Trailing commas in multiline
+ ## Code Style
+ Enforced by .prettierrc / .eslintrc — run `make fmt` before committing.
```

---

## 7. Mark auto-generated files

Stops the agent from editing generated output.

```diff
- - pkg/cmd/resources_cmds.go — CLI resource commands
+ - pkg/cmd/resources_cmds.go — Auto-generated from OpenAPI spec. Do NOT edit manually.
```

---

## 8. Undeclared override → flagged override

When a project rule deviates from the global default, say so.

```diff
- ## Execution
- Move fast; don't ask before implementing.
+ ## Execution
+ **Override (global default is ask-first):** this project is speed-first —
+ implement without asking on unambiguous tasks.
```

---

## 9. Misplaced content → move to the right layer

Not a text edit — a relocation. Propose it explicitly:

> "`~/.claude/CLAUDE.md` contains `pnpm build` and a `src/` structure map — these are project-specific. Recommend moving them to `<repo>/CLAUDE.md` and keeping the global file to personal preferences only."

> "`CLAUDE.local.md` contains the commit-message convention — teammates won't see it (gitignored). Recommend moving it to the committed `<repo>/CLAUDE.md`."

---

## 10. Situational section → path-scoped rule

When a section only matters for some files, move it out of CLAUDE.md entirely. Unlike an import,
this genuinely defers the cost: the rule enters context when Claude reads a matching file.

```diff
  # CLAUDE.md
- ## API handlers
- - All endpoints must validate input with the shared schema helper
- - Use the standard error envelope
- - Every handler needs an OpenAPI comment block
+ (section removed — see .claude/rules/api.md)
```

```diff
+ # .claude/rules/api.md
+ ---
+ paths:
+   - "src/api/**/*.ts"
+ ---
+ - All endpoints must validate input with the shared schema helper
+ - Use the standard error envelope
+ - Every handler needs an OpenAPI comment block
```

A rule file with no `paths:` list loads unconditionally, at the same priority as
`.claude/CLAUDE.md` — so omitting `paths:` moves the text without saving anything. If the rule
really does apply everywhere, leave it in CLAUDE.md where a human reader looks for it.

---

## Application rules

- One issue per diff; never bundle unrelated changes.
- Show the diff and wait for approval before writing.
- Keep the surrounding wording, headings, and ordering intact — change only what the finding requires.
- After applying, re-state which dimension/finding it resolved.
