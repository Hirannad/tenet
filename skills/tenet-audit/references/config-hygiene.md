# Config hygiene checks

For a global or config audit: the config around the instruction files. Report findings; fix only
on approval, one issue at a time.

1. **Permission cruft.** One-off, file-specific or stale `permissions.allow`/`deny` entries go;
   generic patterns stay.
2. **Nested `~/.claude/.claude/`.** Normal when `~/.claude` is itself opened as a working directory
   (a project slug for it exists under `~/.claude/projects/`): then it is that directory's
   project-local settings, so audit its contents instead. Flag it only if nothing reads it; verify
   against a transcript record before calling it an artifact.
3. **Broken hooks.** Every hook `command` must point at a path that exists from where it runs.
4. **Plugin and MCP over-load.** Domain-heavy or unused plugins and servers enabled globally; the
   default home for domain tools is the project layer.
5. **Memory staleness.** Resolve the memory directory (`autoMemoryDirectory` relocates it). Flag
   `MEMORY.md` entries that no longer match reality; only its first 200 lines or 25 KB load. Auto
   memory switched off is a setting, not a clean record: say which it was.
6. **Surface growth.** Run `cli.py audit surface` and lead the section with its delta, naming the
   added items. Only `unchanged` means nothing grew; `grown`, `shrunk`, `unread`, `unbaselined`,
   `unusable` and `untracked` are all reported as such. Re-baselining is the user's: `--record`
   prints to stdout, the user redirects it to a `.new` file, reads it, and moves it into place.

Output: a "Config hygiene" section in the audit report, one line per finding with the file, the
line and the remedy, led by the surface delta when there is one.

A check here earns its place by having caught something on this machine. One that never fires after
a few audits is measuring someone else's problem; delete it rather than run it.
