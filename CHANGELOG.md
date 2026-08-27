# Changelog

Keyed by version, not by commit. `claude plugin update` compares `plugin.json`'s version
field, so the version is what a user can actually be on — and a version survives a
repository move, while a hash does not. Every entry below corresponds to one bump of both
manifests. Releases before 1.0.0 carry no git tag; the manifests were the whole ledger.

Dates are release dates.

## 2.1.0 — 2026-08-27

**The automatic drafting path had never run once.** The `Stop` hook `cat`-ed its gate to stdout
and exited 0, and a `Stop` hook's exit-0 stdout goes to the debug log and nowhere else: the
harness adds plain hook stdout to the model's context for `SessionStart`, `UserPromptSubmit` and
`UserPromptExpansion`, and for nothing else. So the feature that was supposed to notice a decision
at the end of a session and offer a draft has been inert since 0.1.0, while `stop-prompt.md`'s
first line asserted it was injected and the README billed 3.2 KB per response for it. Fourth
instance of this repository's signature defect — a mechanism wired in, firing on every event,
structurally unable to do its job — and the largest.

- **Found by measuring, and the measurement decided the fix.** Four candidate mechanisms, one
  probe token each, in a sandbox session: plain stdout — not delivered. `systemMessage` — not
  delivered. `hookSpecificOutput.additionalContext` — delivered. `additionalContext` with no
  re-entry guard — delivered, then re-asked itself until the turn limit. The shipped harness agrees
  with the docs, in a code path that names those three events and returns nothing for the rest.
  So: `additionalContext`, with a `stop_hook_active` guard. Verified again end to end through the
  real hook, with a marker in the gate text, before and after.
- **The gate went 3.2 KB to 0.9 KB in the same change.** Two thirds of that file was *drafting
  rules* — needed only once the gate fires, which is rare, and paid for at the end of every
  response, which is not. They moved to `references/draft-rules.md`, which the gate names by
  absolute path and the model reads only when it has something to write.
- **`hooks.json` no longer knows where the store is.** Its inline `Stop` command carried a literal
  `$HOME/Claude/brain`, because `hooks.json` cannot source `lib.sh` — one fact, two hand-kept
  copies, nothing comparing them, inside the hook config of the plugin whose whole subject is that
  failure. The fix was not to compare the copies but to delete one: the guard is now
  `hooks/on-stop.sh`, which sources `lib.sh` like everything else. **`rename-check.sh` gained an
  eighth check** that fails if any store-path resolution reappears in `hooks.json` — tested in
  both directions.
- **A library warning can no longer be silenced by the caller that needs a clean pipe.** The Stop
  hook's stdout is now a JSON channel, and `lib.sh` prints at source time. Rather than discard
  those lines, `lib.sh` collects them in `TENET_LIB_NOTICE` and `TENET_LIB_QUIET=1` suppresses only
  the printing; `on-stop.sh` prepends them to the injected gate. The first draft of this did
  discard them, and `vault_check`'s loud path then wrote a repair procedure into the middle of the
  JSON object — caught by testing the failing direction, which is the only reason it is not in this
  release.

**The store is called `ledger` now.** The plugin has been `tenet` since 0.1.0 while its store kept
advertising a different metaphor — in three skill descriptions that load in every session, and in
a crowded corner of search where `second brain` means something this deliberately is not. The
README's own first sentence already called it a commitment ledger.

- Six load-bearing sites, and the rename procedure this repository documents is what moved them.
  `BRAIN_NAME` and `brain_vault_check` became `VAULT_NAME` and `vault_check`; `BRAIN ERROR:` became
  `TENET ERROR:`; the session-start block's first line is `LEDGER:`.
- **`BRAIN_VAULT` still resolves**, and that is the point. Renaming the variable is the one
  genuinely breaking part: a user who exported it and took an update would be told "no store yet"
  and offered a bootstrap, and accepting would give them a second, empty store beside the real one.
  So it stays as the third of four sources, and `vault_check` mentions the new spelling once — on
  the interactive path only, because an unattended run has nobody to read advice and the fallback
  works.
- **The three literal paths in the skills are gone entirely rather than updated.** Each skill now
  says the store's path is whatever its `!`-block printed. The scripts already resolved it
  correctly; the prose was a fourth copy.
- Nine of the ten `Claude/brain` references in this repository were live, not history — measured
  before assuming, because the reverse assumption would have added an exemption to a check that did
  not need one.
- One usability defect the rename introduced, and fixed: with `brain` retired on *both* axes, the
  vault loop and the plugin loop reported the same twenty lines each. One pattern, one owner now.
- **And one the rename created in the file describing it.** `CHANGELOG.md` is keyed by version and
  exists to say what each release changed, so this entry has to spell the old name — which made the
  release gate fire on the paragraph explaining the release. It is now excluded from the stale-name
  greps for the same stated reason the store's `retro.md` and `log.md` already were: a record is not
  a reference. `README.md` is deliberately *not* excluded, because it carries paths a reader will
  copy. Found by running the gate against a simulated fresh clone, which was also the only way it
  could be found — the working tree carried other findings that masked it.

**The store's path is a plugin option, so a fresh install has nothing to configure.** `userConfig`
in `plugin.json` declares it as a typed `directory`; Claude Code asks for it when the plugin is
enabled and exports it to every hook process as `CLAUDE_PLUGIN_OPTION_LEDGER`. `lib.sh` reads four
sources in precedence order, and "set `BRAIN_VAULT` to match" left the Getting started list.

**The injected `!`-blocks now pre-approve their own scripts.** `${CLAUDE_PLUGIN_ROOT}` is
substituted inside `allowed-tools` Bash rules as well as in the body, and an injected command whose
permission check returns anything other than *allow* aborts the whole skill invocation — `Bash`
defaults to *ask*, and ask is not allow. Whether that abort actually fires on a machine with no
matching rule is **not established**: this repository's own `settings.local.json` holds 43 grants,
none of which match the injected form, so the local evidence points the other way and the honest
answer is that it was not reproduced. The rule is the documented pattern, it costs nothing, and it
removes the question.

**Three more defects, each measured in the failing direction before the fix and after it.**

- **`bootstrap.sh` could delete a real Obsidian vault's configuration.** Its refusal guard looked
  for root-level `*.md` only, and the next lines run `rm -rf "$TARGET/.obsidian"` — so a vault
  keeping every note in subfolders passed the guard and lost its workspace, plugins and settings.
  `${TARGET:?}` guards the empty string, not the wrong directory. It now refuses on an `.obsidian/`
  at the target, and on markdown at *any* depth.
- **`bindings.md` had two parsers and they disagreed.** `rename-check.sh` skipped code fences and
  HTML comments — the shipped template keeps its format examples in both — and `resolve.sh` did
  not. So every fresh store bound two phantom topics, one of them `~/code/acme-api`, and the
  stricter parser could not report it because by its own reading there was nothing there. One
  parser in `lib.sh` now, and the proof is that it returns nothing for the shipped template and the
  one real binding for a live one, where the old one returned two phantoms.
- **`surface-check.sh` wrote invalid JSON when a plugin name contained a quote.** The same function
  escaped `keys` correctly with `jq -R .` and `note` not at all, and one note value embeds a plugin
  key read out of `settings.json` — from the script whose entire job is producing a baseline that
  can be compared later. One escaper for both, and it needs no `jq`, so `--record` now works on a
  machine without it.

**Smaller, and all of the same class.**

- `lib.sh` **sourced a file whose name came from store content** with no validation: a `_meta/locale`
  holding `../../../../tmp/x` would have executed `/tmp/x.sh`. Data does not get to choose which
  code runs.
- `on-claude-md-edit.sh` extracted `file_path` with a leading greedy `.*`, so on a one-line payload
  it captured the **last** occurrence — `tool_response`'s, not `tool_input`'s. It now asks whether
  *any* path in the payload is the target, which removes the ordering assumption rather than betting
  on it.
- **`CLAUDE_CONFIG_DIR` is honoured by every script that reads Claude Code's config tree.** It was
  one of five, and the one that ignored it was `surface-check.sh` — whose entire job is reading that
  tree, and which therefore reported eleven surfaces as unmeasured on a relocated config dir.
- **`checks.md` claimed `inventory.sh` dumps `_meta/retro.md`. It does not**, and no script reads
  that file, `_meta/log.md` or `_meta/statuses.md`. Telling a reader a file has been put in front of
  them when nothing opened it is worse than the gap it was covering.
- `tenet-capture`'s description claimed it "promotes approved drafts into the vault", which its own
  body forbids at step 4 — `promote.sh` owns that.

**The README's Context cost section was wrong about the fourth skill**, and the correction came from
the platform's own tooling. It concluded that `disable-model-invocation` means the skill "costs
nothing until you call it"; `claude plugin details` prices it at **~90 tokens always-on**, because
the flag stops Claude choosing the skill and does not remove its description from the listing.
Every figure in that section is now either printed by that command or counted from the shipped
files.

**Stated gap, carried forward deliberately.** The word `brain` left all three model-visible
descriptions and **no blind trigger test was run** — the same confession 2.0.0 made. The difference
is that the next release wires up `claude plugin eval` with an ablation arm, which turns 0.6.0's
promise into something that can fail rather than something that gets re-promised.

## 2.0.0 — 2026-08-26

**Breaking: what the platform already does, this no longer does.** Claude Code's auto memory is on
by default, writes its own notes about your preferences and corrections, and loads a `MEMORY.md`
index into every session. This plugin had been shipping its own version of that since 0.1.0. Two
records of the same thing is the drift class the whole tool is about, so the duplicate went — and
the same pass found something worse than duplication.

- **`_meta/hot.md` and its session-start injection are gone.** A 500-word working-state cache,
  overwritten rather than appended, injected inside a bound directory — which is, feature for
  feature, what the native `MEMORY.md` index does, except machine-local and per-repository. Removed
  from `resolve.sh`, the capture skill's post-approval steps, the sweep's checks, the inventory
  dump, the vault template and the reference docs. **Your existing `hot.md` is not deleted**: it
  stays in your vault as an ordinary note that nothing reads any more. Move what still matters into
  `_meta/log.md`, which is where history was always supposed to live.
- **The Stop hook's retro half is gone, and the sweep took over its job.** The hook used to ask
  whether you had enforced a rule by hand this session — which is the native `feedback` memory
  type, definitionally: *corrections you give Claude and approaches you confirm*. So collection went
  back to the platform, and the sweep's ninth check now reads `~/.claude/projects/*/memory/` for
  `feedback` notes and does the part the platform does not: turning a repeat into a verdict, a
  mechanism that fails when the rule breaks or deleting the rule. This is an upgrade rather than a
  handover. `_meta/retro.md` was vault-global; native feedback is per-repository, and the check now
  counts across all of them. Measured on the author's machine while writing this: eleven `feedback`
  notes across six repositories, one of them named `inferred-tool-behavior-as-fact` — which is,
  independently arrived at, the same error class `retro.md` had labelled A.
- **That check can fail loudly now, which took more code than the check itself.** A missing memory
  directory, one relocated by `autoMemoryDirectory`, and auto memory switched off all produce zero
  entries and mean three different things; a fourth state, *read it and found no corrections*, is a
  real zero. All four print a distinct status line, because reporting a clean sweep on a record you
  never opened is the failure this system exists to prevent. It stays `jq`-free — `jq` is declared
  as exactly one script's dependency and a second user would make that claim false — so the two
  settings come out of a `sed` capture, and a settings file that exists but yields nothing says so.
  Verified against all four branches plus the populated case.
- **The instruction-layer audit was giving outdated advice, and that is worse than a duplicate.**
  `references/layer-map.md` is what the audit reads to reason about layers, and it was wrong in four
  ways at once: it was **missing two layers** — the managed policy `CLAUDE.md`, the one layer no
  user setting can exclude, and `.claude/rules/` with `paths:` frontmatter, at both user and project
  scope; it listed `AGENTS.md` as a precedence layer when Claude Code does not read it at all; it
  framed the stack as *later overrides earlier* when discovered files are concatenated; and its
  fourth finding type told you to convert long content into an `@`-import, which loads at launch and
  reduces context by nothing. An audit that cannot see two layers reports a passing grade on files
  it never opened, so the discovery step now names them and the rule is that an unopened layer is
  *unexamined*, never clean.
- **The other four reference docs were measured against the same yardstick.** `rubric.md` anchors
  its size dimension to the documented target and names path-scoped rules as what actually shortens
  a file; `rewrite-recipes.md` retitles the import recipe as a de-duplication tool and gains a tenth
  recipe for the mechanism that genuinely defers cost; `config-hygiene.md`'s memory check resolves
  `autoMemoryDirectory`, knows the 200-line/25 KB load limit and the `modified` timestamp, and
  distinguishes *switched off* from *clean*; `enforcement.md` now names hooks as the strongest
  available answer to "what catches this", which was missing from a document whose entire subject is
  that question.
- **Copilot came out entirely — six references across two files.** The plugin's mechanisms are
  Claude Code mechanisms, and an audit advertising a file it has no opinion about is noise in a
  description that loads every session. `tenet-audit`'s description lost 54 bytes and gained the two
  layers that are real. One caveat stated plainly: 0.6.0 established that description changes get a
  blind trigger test, and **no trigger test was run for this one.**
- **`bootstrap.sh` was caught by its own release.** Its inventory line claimed "the three journals"
  under `_meta/`, and removing `hot.md` left two. Two counted numbers sat directly above a hardcoded
  third — 0.4.0's defect, one line away. It counts now.
- **Both injection points got cheaper, and one did so while the corpus grew.** Session start went
  from 11.9 KB at thirty-five universal notes to **8.5 KB at thirty-seven**; the response-end prompt
  went from 4.2 KB to **3.2 KB**. Measured in a sandbox vault rather than this repository, because
  the plugin loads twice when the working directory is its own tree and every local figure doubles.
- **Four known limits are now public issues** rather than sentences in a README — including the one
  that matters most: a native `DECISIONS.md` was requested in
  [claude-code#15222](https://github.com/anthropics/claude-code/issues/15222) and the request
  expired unanswered, auto-closed for inactivity with no position taken. That is the reversal
  condition for two of these four skills, and it is written down where something will read it back.
- **Tags are made by `claude plugin tag` from here on, and the naming seam is deliberate.** The
  harness ships a release-tagging command that refuses on a dirty tree, writes the annotation and
  pushes — so `v1.0.0` was the last hand-made tag and `tenet--v2.0.0` is the first in the harness's
  format. Mixed tag list, stated here rather than quietly reconciled.
  It does **not** subsume `rename-check.sh`'s seventh check, and that was measured rather than
  assumed: on a sandbox clone with one manifest field broken at a time, the native command caught
  the `version` mismatch and passed clean on `name`, `license` and `keywords` — all three would have
  been tagged. The check that exists to catch two hand-kept copies drifting is a superset of the
  platform's on three of four fields, so it stays. Worth recording as the counter-example to this
  release's own principle: *ami natív, az nem maradhat* only holds where the native thing actually
  does the job, and the way to find out is to break it on purpose.
- **The README stopped claiming something that is no longer true.** It said tools that re-read
  decision records do not exist. They do now — two of the popular Obsidian systems search past
  reversals and lint for stale facts, and one of them ships a linter for it. What none of them ask
  for is the condition, named at decision time, that would make a different choice correct. The
  comparison table says so with every cell checked against the tools' own templates, and it names
  where a competitor goes further than this does.

## 1.0.0 — 2026-08-26

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
