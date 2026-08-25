# Changelog

Keyed by version, not by commit. `claude plugin update` compares `plugin.json`'s version
field, so the version is what a user can actually be on — and a version survives a
repository move, while a hash does not. Every entry below corresponds to one bump of both
manifests. Releases before 1.0.0 carry no git tag; the manifests were the whole ledger.

Dates are release dates.

## 1.0.0 — 2026-08-25

First public release. Little of the code moved; what moved is that the repository a stranger
clones is now the repository the work happens in.

- **`rename-check.sh` gained a seventh check, and it is not about renaming.** It compares
  `plugin.json` against `marketplace.json` on name, version, license and keywords. `claude
  plugin update` gates on one copy of those facts while the marketplace advertises the other,
  and nothing had ever compared them — the exact drift this tool exists to catch, sitting
  inside its own release gate. It is deliberately `jq`-free, because `jq` is declared as one
  script's dependency and a second user of it would make that claim false. Field extraction is
  pinned to the indentation `jq` emits, so a reformatted manifest yields an empty value and a
  loud finding rather than a quietly wrong comparison — an empty value is a finding here, not a
  pass. Tested in nine failing directions, including a manifest whose `keywords` is no longer
  the last key, where an earlier version of the check would have read on through the rest of
  the file and reported a confidently wrong list.
- **This changelog exists.** Until now the release history was readable only in the commit
  subjects.
- **Releases carry an annotated tag from here on**, and a GitHub Release with it. The manifests
  remain the ledger the plugin manager reads — that has not changed since 0.1.1 — but a
  published repository needs a revision a person can check out by name.
- The repository's own instructions were rewritten for a reader who is not the author.

## 0.6.1 — 2026-08-22

A neutral completeness audit over the released tree found two defects in shipped files.

- `MAX_LIST` capped the session-start note list with `head` and said nothing about it. A note
  missing from the model's context is precisely the silence this system exists to catch,
  arriving in the file that builds that context. It now reports how many notes it withheld,
  and what to do about it. Tested in both directions: quiet at thirty-five listed notes, loud
  at forty-seven.
- The README's Context cost section mispriced its own headline number — it credited the
  11.9 KB session-start block to thirty-four notes when `resolve.sh` lists thirty-five. Off by
  one in the figure that section exists to make trustworthy.

## 0.6.0 — 2026-08-21

Promises measured against the code, and the skills made to fire when they should.

- **`surface-check.sh` is new.** The README had promised since the first release that it
  "measures the surface growing behind you", and nothing measured anything: the check was
  prose asking a model to compare today's counts against a hand-kept JSON file, so on a fresh
  machine there was no baseline and therefore no measurement. The script diffs eleven surfaces
  — permission grants, plugins, marketplaces, skills, agents, hooks, MCP servers — against a
  baseline you recorded and accepted, names the added and removed items wherever the baseline
  recorded them, and **never writes**: `--record` prints to stdout and the redirect stays
  yours. Seven states, only one of which means calm: `grown`, `shrunk`, `unchanged`, `unread`,
  `unbaselined`, `unusable`, `untracked`.
- **The trigger test found the opposite of what was assumed.** The plan was to narrow the
  `tenet` description; measured against nine real competing skills across 120 blind judgements
  per cell, it never over-fired once, and narrowing it bought nothing. It stays as it is. The
  sweep's description was a real gap — "time for the housekeeping pass" and "anything stale in
  there?" reached nothing — and took three attempts to close, landing 120/120 in both
  languages on the strength of a boundary rather than a keyword: it reviews the notes as a
  set, it does not search them for a fact. It costs 266 → 590 bytes in every session, and the
  README now says so.
- **`rename-check.sh` gained a sixth check.** An unquoted `": "` inside SKILL.md frontmatter
  makes YAML read the value as a mapping; the block then fails to parse whole and the skill
  loads with *no metadata at all* — no name, no description, no error, nothing to notice. This
  release shipped one for a few minutes, and only the official validator caught it.
- **The README gained a Context cost section**: the three model-visible descriptions, the
  session-start injection, the response-end capture prompt, the enforcement hook's zero, and
  the fact that the session-start block has no brake.
- Text caught up with code throughout: nothing schedules the sweep, so it says so and names
  the session-start nag that does ship; "POSIX toolchain" became Bash 3.2 plus one optional
  `jq`; three undocumented environment variables and every file the plugin reads outside its
  own tree are tabled with what each absence means; a comparison to a tool that does not exist
  is gone.
- `resolve.sh` stopped injecting `hot.md`'s editing comments — 937 bytes of instructions for
  the person editing the file, delivered into every session inside the vault, where the sweep
  skill already carries them. A fresh vault's block went 1.8 KB to 0.9 KB.
- Drafts written on the automatic path now get a real date instead of the template's
  `{{date:…}}` placeholder, and `promote.sh` says so if one survives. The placeholder left the
  Inbox view sorting by an empty column.

## 0.5.0 — 2026-08-20

Every fix here is something that broke, alarmed, or went mute for a person installing this
plugin on a machine that never saw it.

- **The install path is no longer a README literal.** The documented command was a glob over
  the version-numbered plugin cache, and it broke the moment a second version was cached: the
  glob expanded to two paths, bash ran the first and fed it the second, `mkdir` died on "File
  exists". `/tenet:tenet` now prints the resolved bootstrap command for the running install,
  because the product knows its own path and a README cannot.
- **The one entry point a stranger reaches for first had nothing to say.** `resolve.sh` ran
  unconditionally quiet-when-absent, so on a fresh install the skill printed nothing exactly
  where it had the most to say. Hooks keep the quiet default; the skill's `!`-block passes
  `--interactive`.
- **Missing things are consistently two states now.** A missing enforcement table at the
  default path is a first run: the check reports the rule count and where the format lives,
  and the `CLAUDE.md` hook stays quiet instead of alarming about a table that never existed. A
  table explicitly pointed at that cannot be read is a table someone *had*, and that stays
  loud. Same shape for the vault: the neighbour heuristic that read any `_meta/`-bearing
  sibling as rename evidence is gone, and `BRAIN_VAULT` pointing at nothing now names both
  fixes.
- **An adversarial review of the diff caught a third defect wearing the same mask.** The
  hook's success match was a floating substring, and `10 unmarked rule(s), 0 orphan row(s), 0
  empty cell(s)` contains `0 unmarked` — ten uncovered rules would have passed silently. Both
  hook patterns are now anchored to the start of the checker's summary line.
- The table alignment-row regex accepts `:--` as well as `---`; this README's own table style
  had been producing a permanent orphan-row alarm.
- Every documented command name is the registered `/tenet:tenet` form, with one exception: a
  line in the vault template rode 0.6.0 instead, so the Obsidian validation gate would open
  once rather than twice.

## 0.4.2 — 2026-08-20

- **Category hubs got a name the dead-link check can resolve.** The sweep proposed an
  `_index`-style hub, but `[[Methods]]` resolves against `./Methods.md`, `_meta/Methods.md`
  and `inbox/Methods.md` and nowhere else — so an `_index` suffix, a date prefix or a `hubs/`
  folder each left the link dead forever. Hubs are now named exactly after the category, with
  `type: meta` and no `scope`, and they carry the category's meaning rather than a
  hand-written index that goes stale.
- **`locales/hu.sh` says what a locale does not do.** It does not translate
  `vault-template/templates/` — `bootstrap.sh` copies those verbatim. Choosing a locale means
  translating the templates in your own vault by hand, once; until you do, notes written from
  an English template carry English headings while the checks look for the translated ones.
- **The 60-word decision cap is guarded to `type: decision`.** Run unguarded it scored every
  gotcha, source and open note at zero words — a number that could never fail, which is not a
  passing check. A decision missing the heading entirely now says to check the locale rather
  than the note.
- The categories tally stops at the closing `---` as well as at the next key. A `categories`
  block sitting last in the frontmatter used to run the scan into the body, so every wikilink
  in the prose landed in the tally as if it were a category.
- Fresh vaults ship a `.gitignore` and a `.claude/frontmatter-exempt` of their own.

## 0.4.1 — 2026-08-19

Three checks that could not fail, made able to fail. All three were the same defect in
different clothing: a mechanism wired in, reporting nothing, structurally unable to report the
thing it was built for.

- **`PostCompact` was never an event**, so the hook named after it never ran once — after a
  compaction, nothing put the brain block back in front of the model. It is now a second
  `SessionStart` entry matching `compact`, verified against the hooks reference rather than
  assumed, because writing a matcher on a guess is how the bug was made. `clear` stays
  unmatched on purpose: there the user asked for a clean slate, while compaction takes the
  context without asking.
- **The sweep's inventory globbed `./2026-*.md`**, so a note written in any other year was
  invisible to two of its sections, and both reported nothing rather than failing. Now a
  date-prefixed glob, plus a line that says so when the glob matches nothing — "no notes" and
  "looked past them all" must not print the same way.
- **`bootstrap.sh` drops `.obsidian` from the vault it creates.** The human-validation gate
  means opening `vault-template/` in Obsidian, which leaves app state behind every time;
  `.gitignore` stops it shipping, but `cp -R` does not read `.gitignore`, so one person's
  window layout would have seeded every vault made on that machine.

## 0.4.0 — 2026-08-19

- **The seven saved views are in the repository.** `bases/` existed on disk and in three
  documents but not in git: the README, the vault template's README and `bootstrap.sh` all
  described seven saved views that no install would ever have received. They are now tracked,
  and validated by a human in Obsidian before the release — a release that touches
  `vault-template/` is not done until someone has looked at what it ships.
- `bootstrap.sh` counts its inventory instead of asserting it. A hardcoded manifest is how a
  directory goes missing for a release without anything saying so.
- The Stop hook's capture prompt gained gate C, worded identically to the manual
  `/tenet:tenet-capture` gate, so a gotcha can be drafted unprompted. Until now the fifth note
  type had a template, a view, a counter and a cap, and nothing that could produce one.

## 0.3.0 — 2026-08-16

- **The fifth note type exists: `gotcha`** — for knowledge of the shape "there is one path
  that works, and it is not the obvious one". The decision to add it had been accepted two
  days earlier and never built, which is the same class of failure as a script that goes
  quiet, one layer up: a verdict going unexecuted.
- Gotchas stay out of the session-start list, and that is the design rather than an omission.
  `resolve.sh` prints what has already been *decided*; a gotcha is a fact about a tool and it
  arrives when its subject does. Including them would spend context in every session on
  reference material, permanently and growing.
- `inventory.sh` counts decisions and gotchas separately, which is what makes the new type's
  own reversal condition observable: it reverses below three in half a year, and until this
  line nothing could see that. Building the type without it would have reproduced the defect
  one level down.

## 0.2.1 — 2026-08-16

- **`hot.md`'s Active threads are offered, not just printed.** A `SessionStart` hook injects
  context; it does not act on it. The section named exactly what was half-finished and nothing
  picked it up, so the answer to "where do I continue" kept having to come from outside the
  system that already knew. `resolve.sh` counts the section and adds one line — the
  instruction was the missing piece. It counts unindented lines, so a fresh vault whose
  Active threads holds only the template comment stays silent.
- **No fifth skill for it.** `/tenet-next` was the obvious shape and fails on its own terms:
  twelve characters against a forty-character sentence is a shortcut, not a mechanism, and
  "what should I do now" is the function the note types rule out in as many words.
- The README documented four skills and never mentioned `hot.md`, so an installed user got the
  file in their vault with no idea what it was for. It has a section now, including the sharp
  edge: the state loads only in the vault or a bound directory, so work done anywhere else
  leaves it unreachable from the place it describes.

## 0.2.0 — 2026-08-16

Installable by someone who is not the author. Three separate reasons, all of them invisible
from the inside.

- **There was nothing to install.** No templates, no vault skeleton, no bootstrap — yet the
  shipped docs referenced `templates/`, `bases/`, six `_meta/` files and another repository's
  README, none of which were in the repository. A fresh install printed a repair procedure for
  a vault that had never existed, twice per session start, forever. `vault-template/` is what
  `bootstrap.sh` copies: templates, the `_meta` scaffolds, and three worked example notes. Two
  are `scope: universal` and one is `domain`, so the first `/tenet:tenet` in a fresh vault
  demonstrates the scope gate rather than describing it.
- **"No vault" became two states.** A rename must be loud — that exact silence killed a
  scheduled run — while a first run has nothing to repair. `brain_vault_check` tells them
  apart and names the candidate when it suspects a break. Unattended callers pass
  `--quiet-when-absent`; the user-invoked ones do not, so bootstrap instructions arrive
  exactly when someone reaches for the tool.
- **Section headings were Hungarian, in the machinery.** Two scripts matched a literal
  `Döntés`, and three reference documents mandated Hungarian prose. Headings now come from
  `lib.sh` with English defaults, and the locale belongs to the vault rather than the machine —
  `_meta/locale` holds one word — so a vault carries its language to whatever machine clones
  it. `locales/hu.sh` is the worked example and the whole interface: six strings.
- **The enforcement table was the author's real one.** Forty-nine rows of one person's rules,
  their permission lists, their job title, a private repository name, and their own unmitigated
  secret-scanning gap. It moved to `~/.claude/enforcement.md`, beside the `CLAUDE.md` it
  describes, which is where data belongs. The shipped file is the format and one worked
  example, kept because it shows what a good cell does: names the mechanism, names what the
  mechanism does not reach, and says whether the gap is closable.
- Seven decision slugs from the author's vault, cited as authority in shipped code, were
  replaced by the reasoning they pointed at — no reader outside that vault could resolve them.
- `.claude/frontmatter-exempt` was born here: the audit reported 72 violations against two
  repositories that deliberately run other schemas, which is the false-alarm rate that teaches
  you to stop reading the report.

## 0.1.1 — 2026-08-16

**The version bump is the release.** `claude plugin update` answered "already at the latest
version" against a repository whose HEAD had moved: it compares `plugin.json`'s version field,
not the commit, so the previous fix would have sat in the remote indefinitely while the
installed copy kept running the code that fix repaired. The answer was not to abandon the
plugin path but to make the bump part of it.

## 0.1.0 — 2026-08-16

First release.

- **The machinery got version control.** It lived only under `~/.claude`, which is not a git
  repository: a machine loss would have restored the notes and not the thing that reads them.
- **The decision journal and the `CLAUDE.md` audit ship as one plugin**, because they were
  already one system — the same empty-enforcement-cell count ran twice, once against the
  vault's conventions and once against the global `CLAUDE.md`. A rule and a decision are the
  same object at two altitudes.
- **The name split in two.** The working name lasted a day before becoming `tenet`, and
  `lib.sh` now holds two name pairs — one for the machinery, one for the vault — each with a
  previous-names list, so a rename is a supported operation with a check behind it rather than
  an outage. The vault keeps its own name and its own repository: it holds content, the plugin
  holds machinery, and they have separate lifetimes.
- **Fallbacks that nobody could reach were deleted with the code they backed.** One had never
  resolved at all — it pointed at a directory name that no layout ever used. A fallback nobody
  can reach is indistinguishable from no fallback, except that it reads like cover.
- `rename-check.sh` learned it was wrong about itself: its rule said any `$` inside a `` ```! ``
  block silently truncates the skill, but the plugin loader substitutes `${CLAUDE_PLUGIN_ROOT}`
  before the permission check ever sees it. `$HOME` and `$(...)` still fail. The check also
  started scanning this repository's own `skills/`, which it had never done — it was
  structurally unable to see a violation in its own tree.
- The hook behind `CLAUDE.md` edits exited 0 when its checker was missing: wired, firing on
  every edit, reporting nothing, indistinguishable from a clean table. It is loud now.
