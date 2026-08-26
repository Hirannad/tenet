# Layer Map & Cross-Layer Checks

The instruction files form a load order. Each layer has a job; problems arise when content lands in
the wrong layer, is duplicated across layers, or sits in a layer the audit never looked at.

**Read this before scoring, and do not score the stack from memory** — the layer set has changed
more than once, and an audit that misses a layer reports a clean bill on files it never opened.

## Load order (root-most first; everything is concatenated, not overridden)

```
1. Managed policy CLAUDE.md      macOS:   /Library/Application Support/ClaudeCode/CLAUDE.md
                                 Linux:   /etc/claude-code/CLAUDE.md
                                 Windows: C:\Program Files\ClaudeCode\CLAUDE.md
                                 or the `claudeMd` key in managed-settings.json.
                                 Cannot be excluded by any user setting.
2. ~/.claude/CLAUDE.md           user, personal — every project inherits
   ~/.claude/rules/*.md          user rules; load before project rules
3. <repo>/CLAUDE.md              project, team — committed, code-reviewed
   or <repo>/.claude/CLAUDE.md   equivalent location for the same layer
   <repo>/.claude/rules/**.md    project rules; those without `paths:` load at launch with the
                                 same priority as .claude/CLAUDE.md
4. <repo>/CLAUDE.local.md        machine-local, gitignored — appended after CLAUDE.md at its level
```

**Concatenated, not overriding.** Every discovered file enters the context window; content is
ordered from the filesystem root down to the working directory, so instructions nearer the launch
directory are read last. Nothing deletes an earlier layer's text — a "project override" only works
because the later text is read later and says so.

**Two things load on demand rather than at launch:** `CLAUDE.md` / `CLAUDE.local.md` in
subdirectories below the working directory, and rules carrying `paths:` frontmatter. Both arrive
when Claude reads a matching file, which is also why they can be absent from a `/context` listing
early in a session and appear later.

`AGENTS.md` is **not a layer** — Claude Code does not read it. See the interop section.

## What belongs in each layer

| Layer | Belongs here | Does NOT belong here |
|-------|--------------|----------------------|
| Managed policy | Org-wide standards, security and compliance rules IT must guarantee | Anything a single team or person should be able to turn off |
| `~/.claude/CLAUDE.md` | Personal preferences, autonomy rules, communication style, conventions you want everywhere | Project-specific commands, repo structure, team conventions |
| `~/.claude/rules/` | Personal rules worth splitting out by topic; personal path-scoped rules | Anything a teammate needs |
| `<repo>/CLAUDE.md` | Project scope, tech stack, build/test commands, structure, team conventions, guardrails | Personal preferences, secrets, machine-specific paths |
| `<repo>/.claude/rules/` | Topic-scoped and **path-scoped** project instructions | Rules that must apply to every file (those load unconditionally anyway — keep them in CLAUDE.md where a reader looks) |
| `<repo>/CLAUDE.local.md` | Local ports, machine-specific env, personal scratch rules for this repo | Anything the team needs (it is gitignored — they never see it) |

## AGENTS.md interop

Claude Code reads `CLAUDE.md`, not `AGENTS.md`. If a repo already keeps portable instructions in
`AGENTS.md`, the clean split is a short `CLAUDE.md` that imports it, with Claude-specific content
appended below:

```markdown
@AGENTS.md

## Claude Code

<Claude-only mechanics here>
```

A symlink works when there is nothing Claude-specific to add. `/import` (v2.1.213+) copies another
agent's configuration over once, rather than keeping two live files.

If both files exist with large overlapping content, recommend collapsing to the import pattern.

## Imports vs path-scoped rules — do not confuse them

`@path/to/file.md` imports are expanded **at launch**, recursively up to four hops. They help
organisation and they **do not reduce context** — the imported text is loaded either way. So an
import is the right answer to *"this content is duplicated in three places"* and the wrong answer
to *"this file is too long."*

What actually keeps instructions out of context until they are relevant is a rule with `paths:`
frontmatter. That is the recommendation to make when a long file carries situational sections.

One caveat worth flagging when you propose an import: in a **project-level** file, an import whose
path resolves outside the working directory is external, and the first time Claude Code sees one it
asks the user to approve the list. Declining disables them permanently and silently.

## Cross-layer findings to flag

1. **Duplication** — the same rule in two layers. Keep it in the most general layer that is still
   correct, delete the copy. A global rule restated in a project file is the common case.

2. **Undeclared override** — a project file contradicts a global default without saying so. Since
   layers are concatenated rather than replaced, an unflagged contradiction leaves two live rules
   and the model picks one. Recommend the explicit flag, or removing the contradiction.

3. **Misplaced content** —
   - Personal preference in a committed team file → move to `~/.claude/CLAUDE.md`.
   - Team-needed rule in `CLAUDE.local.md` → move to `<repo>/CLAUDE.md`; local is gitignored.
   - Secret or machine path in a committed file → move to local **and** flag as a leak.

4. **Situational content that should be a path-scoped rule** — a long CLAUDE.md whose sections only
   matter for some files. Recommend `.claude/rules/<topic>.md` with a `paths:` list. Do **not**
   recommend an `@`-import to shrink a file; it does not.

5. **A layer nobody audited** — the rules directories and the managed policy file are the two most
   commonly missed. Report them as *unexamined*, never as clean: a layer that was not opened is not
   a layer that passed.

6. **Instructions duplicating auto memory** — auto memory skips what CLAUDE.md already says, so a
   CLAUDE.md that restates accumulated preferences is paying for the same content twice. Read the
   memory directory before recommending an addition to CLAUDE.md.

## How to use this in the audit

Build a matrix: for each rule, note which layer(s) it lives in. Any rule in more than one layer is
a duplication candidate; any rule contradicting a higher layer with no explicit flag is a conflict.
Report these separately from the per-file scores — they are the findings a single-file tool misses.

Two commands settle what is loaded rather than what exists: `/context` lists the memory files that
actually loaded this session, and the `InstructionsLoaded` hook logs which files loaded, when, and
why. Use them before concluding a file is or is not in play. `claudeMdExcludes` (any settings
layer, arrays merge across layers) is the reason a file can exist, be in the load path, and still
never load — managed policy excepted, which cannot be excluded.
