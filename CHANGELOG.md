# Changelog

One line per version, keyed by version rather than commit. The narrative entries up to 2.2.7 are
in `git show tenet--v2.2.7:CHANGELOG.md`; the commit behind each version carries its reasoning.

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
