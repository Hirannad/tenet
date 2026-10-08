# Changelog

One line per version, keyed by version rather than commit. The narrative entries up to 2.2.7 are
in `git show tenet--v2.2.7:CHANGELOG.md`; the commit behind each version carries its reasoning.

- **Unreleased**: the sweep lists groups of accepted decisions that may share an insight (a `related` link plus text overlap, 3-8 members), and the observer writes a `proposed` pattern draft for a group only when a verbatim human-prompt quote on the idea exists; the draft opens with that quote and leaves the boundaries empty. No quote, no draft; a group proposed once is not proposed again.
- **3.3.0** (2026-09-29): the verdict comes to the user. A Stop hook checks, cheapest condition
  first, whether drafts wait and the session is at rest (enough work, no background task, no open
  task or todo, the last message not a question); if so it asks for one to four verdicts in a single
  AskUserQuestion, once per session, and `cli.py verdict apply` writes the statuses, deletes
  discarded drafts and logs each verdict to `_meta/observer/verdicts.jsonl`.
- **3.2.0** (2026-09-29): the audit half runs in Python (`cli.py audit layers|surface|enforcement|
  frontmatter`), so no shell script and no `jq` remain. `--record` on the surface baseline now keeps
  every hand-written field of the baseline it replaces (#10). Symlinked rule files and directories
  are counted, as Claude Code loads them; `audit frontmatter` skips gitignored files and reports a
  missing directory as not examined. The audit's references went from 834 to 280 lines.
- **3.1.0** (2026-09-27): the session start prints a per-project brief instead of every universal
  note. An observer (`tenet/observer/`) scans the last 30 days of transcripts in a detached
  background run, scores each accepted note against what was asked in each project, adds a
  computed core and the notes of the last 14 days, and caps the brief at 4 KB. It also records
  which notes were cited in work sessions, in the ledger, as the input for archiving unused notes
  later. A category that names no hub note is now reported (#13).
- **3.0.0** (2026-09-27): rebuilt the ledger half in Python (`tenet/cli.py`) and removed the Stop
  hook that asked for a capture after every response, the PostToolUse hook, the `/tenet:tenet`
  skill, `rename-check.sh`, the locale files, the seven `.base` views and the example notes. The
  Decision heading the length cap checks now comes from the ledger's own template. The note model
  lives in one file, `skills/tenet-capture/references/conventions.md`. The marketplace entry no
  longer repeats the version. `BRAIN_VAULT` is no longer read.
- **2.2.7** (2026-08-28): the Privacy section's auto-memory read documented literally.
- **2.2.6** (2026-08-28): `/tenet:tenet` reported an empty ledger instead of failing; a file mode.
- **2.2.5** (2026-08-28): the Privacy section became a submitted policy, and two inaccuracies in it were fixed.
- **2.2.4** (2026-08-28): answers to two skeptic's questions, one of them an overpromise.
- **2.2.3** (2026-08-28): the Known limits preamble promised an issue behind every bullet.
- **2.2.2** (2026-08-28): the README's front door quoted two numbers its sources no longer said.
- **2.2.1** (2026-08-28): the categories rule got a checker after it broke.
- **2.2.0** (2026-08-28): `layer-check.sh` put a counter behind the layer-hygiene rubric dimension.
- **2.1.0** (2026-08-27): the capture gate finally reached the model; the store was renamed to ledger.
- **2.0.0** (2026-08-26): stopped duplicating the platform's auto memory.
- **1.0.0** (2026-08-26): first public release.
- **0.6.1** (2026-08-22): two defects in shipped files from a completeness audit.
- **0.6.0** (2026-08-21): promises measured against the code; skill descriptions made to fire.
- **0.5.0** (2026-08-20): fixes for what broke or went mute on a fresh install.
- **0.4.2** (2026-08-20): category hubs got names the dead-link check resolves.
- **0.4.1** (2026-08-19): three checks that could not fail made able to fail.
- **0.4.0** (2026-08-19): the saved views entered the repository.
- **0.3.0** (2026-08-16): the `gotcha` note type.
- **0.2.1** (2026-08-16): active threads offered at session start.
- **0.2.0** (2026-08-16): installable by someone other than the author.
- **0.1.1** (2026-08-16): the version bump became the release.
- **0.1.0** (2026-08-16): first release.
