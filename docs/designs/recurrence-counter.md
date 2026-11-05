---
title: Recurrence counting for the tenet observer, and the cut of its measuring half
type: spec
status: active
updated: 2026-11-03
---

# Recurrence counting for the tenet observer, and the cut of its measuring half

*   **Author:** József Juhász (drafted with the Elephant-Goldfish Model: the session's model wrote, the author decided every checkpoint)
*   **Status:** Approved 2026-11-03, after two goldfish rounds
*   **Date:** 2026-11-03
*   **Review history:** round 1: 9 reviewers, 164 findings, resolved in 39 themes; round 2 (after the rewrite): 4 reviewers, 71 findings, resolved in 16 themes. Reports in the ledger: `_meta/retro/2026-11-02/egm-review/` and `egm-review/round2/`. The EGM re-audit cap (one per stage) is reached; residual trade-offs are listed in the round-2 report.

--------------------------------------------------------------------------------

## Overview

tenet is a Claude Code plugin around a decision ledger of markdown notes. A session-start hook prints a per-project brief of the notes that matter there. A Stop hook asks the author for verdicts on waiting drafts when a session is at rest. A weekly sweep skill and an audit skill do the housekeeping. The observer is a detached scan over the last 30 days of session transcripts that computes the brief. The observer also has a measuring half: a usage log of note citations found in the assistant's text, and a pattern pipeline that groups ledger notes by text similarity and drafts a `pattern` note from one verbatim user sentence. Neither measures what the author wants noticed, and this design replaces them.

The replacement is a recurrence counter over the author's own prompts, computed inside the weekly sweep's inventory from the same 30 days of transcripts, with nothing persisted. It keys every prompt by its content stems, counts each key across sessions and days, and lists the keys at threshold as a shortlist with counts, dates, projects and one filtered example. The sweep's model reads the shortlist as one more input of its "repeated deviations" check, may write one decision draft from it through the slot it already has, and copies the counter's receipt line into the weekly digest, which is the trace the January retro reads. The work ships in three releases: the cut removes the old half; the counter counts and shows; the proposer, sketched here only at its boundary, adds a validated card and a one-move verdict in its own design round. The author's private `~/.claude/dream/dream.py` already reads prompts with the rules the counter needs; those rules are ported into tenet, and dream.py is narrowed by the author's hand.

## Glossary

*   **ledger**: the directory of markdown notes. Types: decision, pattern, gotcha, open. Statuses: proposed, accepted, reversed, superseded. `inbox/` holds drafts, the root holds accepted notes, `_meta/` holds the process log (`retro.md`), the sweep digests and `observer/verdicts.jsonl`.
*   **brief**: the per-project list of relevant notes the session-start hook prints; the scan computes it.
*   **scan**: the detached background pass `cli.py observe scan`, started by the session-start hook when `run.due()` names a reason (no brief yet, brief older than seven days, a new project, notes changed). It parses every transcript of the last 30 days (3.5 s for 266 sessions, measured 2026-11-03) and writes the briefs and `status.env` to the plugin's data directory. This design changes it only by removing the measuring half.
*   **data directory**: the directory Claude Code assigns the plugin (`CLAUDE_PLUGIN_DATA`, or `TENET_DATA` for tests and manual runs); machine-local, untracked. The counter does not use it.
*   **resting point**: a Stop-hook state: at least 20 assistant turns, nothing running in the background, no open question. The verdict gate asks there at most once per session.
*   **verdict round, verdict gate**: one AskUserQuestion with one to four drafts, built by `verdict.gate`. `cli.py verdict apply` applies the answers: it rewrites a draft's `status`, removes a discarded draft, and appends date, draft name and verdict to `_meta/observer/verdicts.jsonl`. Session start promotes accepted drafts from `inbox/` to the root.
*   **ticket, claim**: the file the gate writes with the drafts it asked about (question, draft name, sha1 of the draft), and the per-session marker that prevents a second round.
*   **sweep**: the weekly skill `/tenet:tenet-sweep`. Its `!` block runs `cli.py sweep`, the dump: an inventory the model works from. The model writes a digest `_meta/maintenance-<date>.md` and may write one draft per run (check 8's draft slot). Nothing in the plugin schedules the sweep; the author's routine or a manual invocation starts it, and `promote.run` prints `Maintenance is due (last run <date>)` at session start when the newest digest is older than a week.
*   **check 6, check 8**: two of the sweep's checks: pattern candidates (retired here) and repeated process deviations (extended here).
*   **wrapper, `origin.kind`, `isMeta`**: a transcript user record whose text starts with a harness envelope (`<command-`, `<task-notification`, `<system-reminder`, …) is a wrapper and not a prompt; a prompt the author typed has `origin.kind == "human"` and no `isMeta` flag.
*   **stem, content stem**: `textindex.tokens()` folds accents, lower-cases, splits on non-alphanumerics, drops words under three characters, digits and a stopword list of Hungarian and English function words, strips common suffixes and keeps six characters. "végeztünk?" (are we done?) becomes `vegezt`; "are we done?" becomes `done` (`are` is a stopword, `we` is too short). A content stem is any token that survives.
*   **key**: the sorted set of a prompt's content stems joined by spaces; the unit the counter counts. A prompt with no content stem has no key.
*   **candidate**: a key seen in at least two sessions inside the window.
*   **key at threshold**: a candidate with at least three occurrences in at least three sessions on at least two days, whose only stem is not an acknowledgement.
*   **sensitive project**: a project whose name starts with a prefix listed in the ledger file `_meta/sensitive`. Its prompts are counted and never shown.
*   **example filter**: the text check run on an example before it is printed: the PII patterns, the authority-language pattern, and gitleaks when the binary is present.
*   **checkpoint**: a decision the author took during drafting or review; listed under "Decisions taken during drafting".
*   **J-class**: the ledger's process log classes errors; J is "a written convention with no mechanism behind it, and it broke".
*   **batch B0, B1a–d, B2a, B4**: batches of the retrospective's release plan (ledger `_meta/retro/2026-11-02/release-plan.md`); their relation to this design is stated under Prerequisites.

## The Problem

The ledger decision of 2026-09-27 ("acceptance is not an end state") set two jobs for the measuring half: archive a note that goes unused for 90 days, and propose a rule from a note that surfaces three times in 60 days. The plugin's issue #2 set the rule for patterns: the machine must never author one; it may only make the question arrive at a better moment or build the note from the author's own sentence. What shipped between 3.1.0 and 3.6.1 does neither job:

*   `tenet/observer/usage.py` records note names found in the assistant's text (225 rows; 35 percent are `related` links written at draft creation, 27 percent are same-day self-citations). Nothing reads the log. The 90-day archive and the rule consumer were never built.
*   `tenet/patterns.py` and `tenet/observer/pattern_drafts.py` group accepted notes by TF-IDF cosine (threshold 0.08) plus `related` links, then search for one verbatim user sentence; since 3.6.0 the session's model phrases the rule at a separate Stop. Result: three drafts ever (all 2026-10-13), two of them reworked by hand after an edit verdict and one set aside as unclear; two J-class entries in the process log; since 2026-10-13 the graph is one component of 99 of the 115 accepted decisions, which the size cap drops, so the weekly sweep prints "A real zero" for a detector that found everything at once. The naming Stop fired 0 times in 42 rounds.

Neither counts what the author repeats. His stated signal: at the end of most sessions he asks whether every decision is enforced, whether an open point is left, whether the work is finished end to end: "végeztünk?" (are we done?), "minden ki van kényszerítve?" (is everything enforced?), "maradt nyitott pont?" (is any open point left?). That recurrence never surfaced. He built two private skills from it by hand (`/wrap`, `/verdicts`), and what he must trigger by hand often does not happen. His success signal is not a count: anything that happened more than two or three times (an error, a misunderstanding, a new expectation) should not have to be typed a fourth time.

Measured on 2026-11-03 over his last 30 days (363 transcripts, 276 sessions after dropping 87 scheduled ones, 1050 prompts, 282 of them from sensitive projects):

| What | Prompts | Sessions | Note |
| :-- | --: | --: | :-- |
| prompts whose stems include `vegezt` (the "done" family) | 18 | 18 | 15 days; 5 from sensitive projects |
| of those, the four bare forms (végeztünk, végeztem, akkor végeztünk, végeztünk itt) | 6 | 6 | one key under stem-set keys, `vegezt`: 5 days, 4 projects, at threshold |
| the same four forms under folded-text keys (the first draft's rule) | 6 | 6 | four keys, none above 2 sessions |
| the other 12 (longer sentences: "végeztünk, mehet a wrap", …) | 12 | 12 | one key each, below threshold |
| the long paraphrases of the question (open point + enforced) | 2 | 2 | two keys, below any threshold |

The other keys at threshold are acknowledgements ("try again" 11 sessions, "mehet" 6, "kész" 4, "folytasd" 3), the platform's usage-limit continuation text (4 sessions) and "miért álltunk meg" (why did we stop; 3 sessions, 3 projects). Under stem-set keys 7 keys reach threshold, 3 after the four acknowledgements are ignored.

What the platform and the sweep already see: Claude Code's auto memory records the corrections the assistant chooses to save as `feedback` notes (32 on this machine; none mentions the end-of-session question), and the sweep's check 8 reads those notes and the ledger's process log. Neither reads prompts. A question the author types and the assistant answers without saving anything is invisible to both.

Two facts about the existing machinery shape the design. First, dream.py already reads the author's prompts with per-record timestamps, a sensitive-project list, PII and authority-language patterns and a three-session rule, and never counts them; the 2026-09-27 decision said it would become part of tenet, and it did not, so tenet grew a second reader with other rules (file modification time for dates, no sensitive exclusion). Second, the verdict round's claim is per session rather than per draft, and "Accept" only flips a status; batch B2a of the retrospective fixes the claim, and the proposer release depends on it.

## Goals

Each goal names the plan item that delivers it.

*   **G1. Count recurrence of the author's prompts, not note similarity.** A key is counted once per session; parallel sessions typing the same key within ten minutes count once; dates come from record timestamps. (Item 22.)
*   **G2. Find the known case before anything is proposed.** On the author's machine the first dump after the counter release must list `vegezt` among the keys at threshold and four ignored acknowledgement keys, the figures of 2026-11-03. A synthetic fixture covers the mechanics in CI. (Items 22 and 30; Verification Plan.)
*   **G3. Show, do not store.** The counter persists nothing: the shortlist is computed when the dump is printed, from the transcripts, and an example is printed only after the example filter and only when the ledger carries the author's sensitive list. An example may then persist in a digest or a draft, as any prompt the model quotes. (Items 22, 25 and 27.)
*   **G4. Phrase in the weekly sweep through the existing draft slot.** No new Stop-hook turn, no new writer; the sweep model writes at most one draft per run, as today. (Item 27.)
*   **G5. A loud zero and a weekly trace.** Every dump prints a receipt line with denominators and near misses, and the sweep model copies it and the shortlist's cluster lines into the digest every week, clean weeks included. (Items 22 and 27.)
*   **G6. Sensitive projects are counted and never shown.** The list lives in the ledger (`_meta/sensitive`); its presence is the consent for examples. (Items 22 and 24.)
*   **G7. The cut is one release** with a two-command upgrade note and a rollback section written from a drill. (Phase 1.)
*   **G8. One transcript reader.** The per-record window and dream.py's prompt rules go into `transcripts.read`; dream.py keeps only what tenet does not take over. (Items 22, 23 and 31.)
*   **G9. A pre-registered kill test** with the 2026-11-03 baseline, written into the ledger decision that supersedes 2026-09-27. (Item 21.)
*   **G10. The proposer is a separate release**, designed after four weekly shortlists exist. (Phase 3.)

## Non-Goals

*   The 90-day archive or any auto-archiving of notes; it is judged at the January retro.
*   A code detector for rationale overlap among accepted notes, or a code-side coverage check that matches keys against notes and skills. The sweep model reads the ledger and the installed skills itself. If a note detector is ever wanted, it is exact (the same structured key cited by three or more notes), never a similarity graph.
*   Persisted counter state, a daily counter pass, a session-start banner for the counter, or an environment switch for it. The counter runs when the sweep runs.
*   The proposer's details: the validated card, the budgets, the settle logic, the event table. They are bounded under "The proposer" and planned in their own design round.
*   Accept executing a hook, a skill, a loop or a CLAUDE.md edit by itself.
*   Delivering through the author's private `open:` queue as the only copy, or adding an `open:` reader to the plugin.
*   Counting assistant-text citations as "use", or keeping the semantics of `usage.jsonl`.
*   A monthly retro routine, a tokenizer, a stats subcommand, or changes to the brief's scoring (separate retrospective decisions).
*   Replacing `/wrap` or `/verdicts`.

## Open Questions

*   **Q1. What remains of dream.py.** Its tool-failure and hook-friction scans and its routine checks are the author's private machinery; this design states what tenet ports and that one prompt reader remains. Whether the rest stays or goes is the author's call at cut time.

Closed during review: the ledger's git remote (`github.com/Hirannad/ledger`) is private, verified on 2026-11-03 with the host's API; the fact is recorded in the ledger decision (item 21). No environment variable reaches the design any more, so whether `settings.json`'s `env` reaches hooks or `!` blocks is no longer a question of this design.

### Decisions taken during drafting

By the author, 2026-11-03, in the drafting checkpoints and the two review rounds:

1.  Exact keys first; a stem-pair index is the documented second step if a paraphrase family reaches threshold and exact keys miss it.
2.  (Superseded by 12.) The counter was to run as a daily phase of the scan.
3.  No prompt text is stored. An example is read from the transcript at the moment the dump is printed, from non-sensitive occurrences only, and passes the example filter first.
4.  The sensitive list ships empty. (Refined by 13: its source is the ledger file `_meta/sensitive`.)
5.  The cut takes the minimum path: the code stops writing and reading the three old state files, nothing moves them, the upgrade note gives the author two commands.
6.  The counter release counts and shows; the proposer is a later release with its own design round after four weekly shortlists.
7.  A proposal, when the proposer exists, is a Decision-template draft (Decision = the rule and the form, Why = the evidence, revisit = the post-settle condition). No new note type.
8.  Proposals have no Later option; the answers are accept as the form, not a pattern, or free text.
9.  An accepted proposal that keeps recurring is a shortlist line, not a separate card.
10. One threshold for every form; the standing cost is shown on the card.
11. The retrospective's artifacts live in the ledger under `_meta/retro/2026-11-02/`; this document links there.
12. The counter is stateless: computed inside the weekly dump from the 30-day window, persisting nothing; no scan phase, no status fields, no banner, no switch. The weekly trace is the digest.
13. The sensitive list is the ledger file `_meta/sensitive` (one project-name prefix per line). Its presence is the consent for examples: without the file the shortlist prints keys and counts only.

Decisions 7 to 10 apply to the proposer's design round.

## Critical User Journeys (CUJs)

### CUJ 1: The end-of-session question reaches the shortlist and a draft

*   **Given**: Thirty days of transcripts in which the author typed a bare form of the end-of-session question in at least three sessions on at least two days; `_meta/sensitive` exists in the ledger.
*   **When**: The author's weekly sweep runs.
*   **Then**: The dump's `recurrence shortlist` section opens with `recurrence 2026-11-10: examined 41 sessions, 310 prompts (12 without content stems, 0 without a timestamp), 118 keys, 9 candidates, 3 at threshold, 4 ignored as acknowledgements; nearest below: kesz (2 sessions, 2 days); examples: on (sensitive list: 2 prefixes)`, then `1. vegezt · 6 sessions · 5 days · 4 projects (tenet, ledger, atlas, +1) · 2026-10-09 .. 2026-11-02` with `   e.g. 2026-11-02 · tenet · "akkor végeztünk"`, then the month's typed command counts. The sweep model, following check 8, reads the ledger and the installed skills, finds that `/wrap` and `/verdicts` already cover the question by hand and that the reversed Stop-guard decision of 2026-09-26 tried a mechanism, judges the cluster a repeated break of a covered expectation, and writes one decision draft through its existing slot with the example line under the Why heading of the ledger's Decision template. It copies the receipt line and the cluster line into the digest. The next resting point shows that draft in the verdict round like any other.

### CUJ 2: Nothing recurs

*   **Given**: A quiet month, or a month whose repeats are all below threshold.
*   **When**: The sweep runs.
*   **Then**: The section reads `… 0 at threshold …; nearest below: <key> (2 sessions, 1 day)` and `no key at threshold`, never "a real zero"; the model copies the receipt line into the digest; `cli.py recurrence status` prints the same section.

### CUJ 3: The sensitive list is absent

*   **Given**: A fresh install, or the author's ledger without `_meta/sensitive`.
*   **When**: The sweep runs.
*   **Then**: The section prints every key at threshold with counts, dates and project names, no example lines, and the receipt line ends `examples: withheld (no _meta/sensitive in the ledger; create it, empty or with one project-name prefix per line, to allow examples)`.

### CUJ 4: A sensitive project

*   **Given**: `_meta/sensitive` lists `personal-email` and `family-finance`, and prompts from those projects recur.
*   **When**: A key reaches threshold with occurrences from them.
*   **Then**: The occurrences count toward the key; the project list shows the non-sensitive names and `+1 sensitive`; the example comes from a non-sensitive occurrence; a key whose occurrences are all sensitive prints `[sensitive projects only] · 3 sessions · 2 days` and no key, in the list and in the overflow line; the nearest list omits such keys; command counts include every project (names only).

### CUJ 5: The cut on the author's machine

*   **Given**: tenet 3.6.1 installed; the ledger holds `_meta/observer/{usage.jsonl, patterns.json, state.json, verdicts.jsonl}`, `state.json` tracked by git; no pending pattern draft in `inbox/`.
*   **When**: 3.7.0 installs and the next session starts.
*   **Then**: Both hooks run and the brief prints; no scan writes the three old files again, and the next scan drops the three retired keys from `status.env`; the sweep's dump has no pattern section and its skill text says check 6 is retired; the CHANGELOG line and the README upgrade note give the two commands (`git rm --cached _meta/observer/state.json` in the ledger; `rm _meta/observer/usage.jsonl _meta/observer/patterns.json _meta/observer/state.json`, or keep them); a draft decision superseding 2026-09-27 waits in `inbox/` for the author's verdict; the README's rollback section names the commands the rollback drill verified.

### CUJ 6: The January retro

*   **Given**: Eight or more weeks of the counter in use.
*   **When**: The retro reads the weekly digests and the ledger decision's baseline row.
*   **Then**: Each digest carries the receipt line and the cluster lines of its week and the name of the draft written from the shortlist or the reason none was; the retro compares the series against the baseline of 2026-11-03 and evaluates the pre-registered delete condition instead of reading rates off a handful of events.

## Technical Plan (Architecture)

### Shape of the change

Three releases, named by content; version numbers are assigned at release in CHANGELOG order.

1.  **The cut** (Phase 1; batches B1a and B1b of the release plan; 3.7.0). Removes the usage log, the pattern pipeline, the naming round and every sentence about them; the observer keeps the brief only. One upgrade note, one rollback section.
2.  **The counter** (Phase 2; the first minor release after the cut). Adds one module, `tenet/observer/recurrence.py`, a pure computation over the session dicts the transcript reader already produces, called by `cli.py sweep` and `cli.py recurrence status`. Check 8 gains the shortlist as an input and the digest gains the receipt line. No hook, scan, state file or switch changes.
3.  **The proposer** (Phase 3; after batch B2a and after four weekly shortlists have been read). Adds the validated card and the proposal-specific answers. Its boundary is below; its design is its own round.

### Prerequisites from the retrospective

The release plan's batches, as they touch this design:

*   **B0** (hygiene, 3.6.2): a hermetic test `setUp` (`TENET_DATA` and `CLAUDE_CONFIG_DIR` at temporary directories), Discard copies a draft before `git rm`, bootstrap refuses to overwrite, a `plugin.json`-versus-CHANGELOG version test, a hooks.json parse test, and one template `.gitignore` line (`_meta/observer/`). Item 16 of this plan supersedes that line with the final file; the rest of B0 is independent of this design and may ship before or after Phase 1. If B0 has not shipped when Phase 1 does, item 20 adds the two `setUp` lines itself.
*   **B1a** (3.6.3) and **B1b** (3.7.0): the false "A real zero" and the cut. Phase 1 covers both; if B1a ships alone first, Phase 1 omits item 9.
*   **B1c** (3.7.1): the usage-log half disappears with the cut; what remains (an unreadable transcript must not crash the scan; a corrupt `state.json`; the 30-day pin) is independent of this design.
*   **B1d** (3.7.2): the per-record window (retro issue observer-16) is folded into item 23, because the counter needs it and the brief gains from it; the dead-root, canary and recorded-fixture items stay in B1d.
*   **B2a** (3.8.0 in the plan; the number moves if the counter ships first): the claim becomes per draft, an unmatched or empty answer is reported and the ticket kept, an unedited template draft is not eligible, and the options are cut to Accept, Discard and free text (Later, To memory and the deferrals go). Phase 3 depends on it; Phases 1 and 2 do not. The plan carries no change to the card preview (the retrospective found the card must stay on every option) and no Stop-path change; nothing here assumes either.
*   **B4** (3.10.0): the README pass that removes hand-copied figures; Phase 1 and Phase 2 edit only the README sentences they must and write no new figures.

### Data flow

```text
~/.claude/projects/*/*.jsonl, last 30 days
    |  transcripts.sessions(30): per session the in-window prompt records
    |  ({text, ts}, dated per record), the typed command names, the
    |  AskUserQuestion text, the touched paths; prompts derived from records
    v
run.scan() (unchanged by Phase 2)        cli.py sweep  (weekly, the author's routine or by hand)
    |-- brief.write_all() -> briefs          |  reads the same sessions, then recurrence.shortlist():
                                            |  key_of(text) -> sorted content stems; one occurrence per
                                            |  (key, session); 10-minute collapse; candidates; keys at
                                            |  threshold; one filtered example per key; command counts
                                            v
                               "--- recurrence shortlist ---" in the dump: receipt line, keys at
                               threshold with counts, dates, projects, example; overflow line;
                               command counts; nothing written anywhere
                                            v
                               the sweep model (check 8): reads the ledger and the installed skills,
                               writes one decision draft per run through the existing slot -> inbox/,
                               copies the receipt line and the cluster lines into the digest
                                            v
                               the verdict round at a resting point (unchanged) -> verdicts.jsonl
                                            v
                               [proposer release, own design round] a validated card as a Decision
                               draft; Accept as <form> / Not a pattern / free text
```

### Components

#### `tenet/observer/transcripts.py` (modified in Phase 1 and Phase 2)

Phase 1 drops the `assistant` text list (its only reader was `usage.py`). Phase 2 makes the reader date its prompts: `read()` keeps, for each human prompt (`origin.kind == "human"`, not `isMeta`, not a wrapper), a record `{text, ts}` with `ts` parsed from the record's own `timestamp` (dream.py's `parse_ts`, ported: the `Z` suffix replaced by `+00:00`, `datetime.fromisoformat`, epoch seconds), drops records outside the window, and derives `prompts` from the kept records, so the brief stops reading months-old prompts from a long-lived session (retro issue observer-16, batch B1d). Records without a parseable timestamp are dropped and counted. A `commands` list holds the names found by dream.py's pattern (`<command-name>/?([^<\s]+)</command-name>`, anywhere in a user record's text, slash stripped). Selection stays file-based (a transcript modified in the last 30 days); dating is per record.

#### `tenet/observer/recurrence.py` (new in Phase 2)

The one new module, stdlib only, with no state and no import-time work: the key, the occurrences, the candidates, the keys at threshold, the receipt line, the example filter, the command counts and the shortlist text. Its input is the list of session dicts; its output is a list of lines. Every constant lives in one block at the top with the measurement or decision that set it. The contract is item 22.

#### `tenet/sweep.py` (modified in Phase 1 and Phase 2)

Phase 1 deletes the pattern-candidates section. Phase 2 adds `--- recurrence shortlist (the author's own prompts, last 30 days) ---`, rendered by `recurrence.shortlist()` over `transcripts.sessions(30)`, read inside `render(vault)`; the signature does not change, and the dump needs no data directory.

#### `tenet/cli.py` and `tenet/paths.py` (modified)

Phase 1 removes the `pattern` subcommand. Phase 2 adds `recurrence status` (prints the shortlist section alone, for the live check and by-hand reading) and gives `paths.py` two helpers: `project_name(root, vault)` and `sensitive_list(vault)`.

#### Skill texts (modified)

Phase 1 retires check 6 in `skills/tenet-sweep/SKILL.md` and `references/checks.md`, deletes the pending-draft line in `skills/tenet-capture/SKILL.md`, and corrects the pattern paragraph in `references/conventions.md`. Phase 2 extends check 8 with the shortlist as an input, tells the model where the evidence goes and what it must copy into the digest, and states what it may never write.

#### `~/.claude/dream/dream.py` (the author's private file, narrowed by hand)

tenet ports the prompt extraction of `read_session` (human records with timestamps, `parse_ts`), `project_of`, the sensitive prefix match (the list itself moves to the ledger file), the `PII` and `AUTHORITY` patterns, `gitleaks` and the three-session rule. dream.py keeps its tool-failure and hook-friction scans and its routine checks; its `HUMAN_KINDS` stage 2 is closed as "built in tenet". The division is written into the ledger decision, not into tenet.

### No state

The counter writes nothing. The dump computes the section from the transcripts at print time (the parse the scan also does, 3.5 s); `recurrence status` does the same. The weekly trace is the digest: the sweep model copies the receipt line and the cluster lines into it by instruction, and a test asserts the instruction is in the skill text. History beyond 30 days therefore lives in the digests and nowhere else; the proposer's round decides whether it needs more, and says why. The baseline for the kill test is the measurement of 2026-11-03, recorded in the ledger decision.

What survives an uninstall: the ledger (drafts, promoted records, `verdicts.jsonl`, the digests). The counter leaves nothing else behind.

### The proposer (Phase 3, boundary only)

The proposer's design round starts from what Phase 2 leaves it: the shortlist and the digests as its input, the existing draft slot and the verdict round as its channel, and the decisions 7 to 10 above. Its boundary with Phase 2: it may add fields to `verdicts.jsonl` rows (the key, the form); it may introduce a validated writer (`cli.py recurrence propose`) that writes a Decision-template draft; it must not change what the counter computes or make the dump depend on state. Its gates: batch B2a merged; four weekly shortlists read and at least one decision draft written from them by the sweep model; the platform's memory consolidation (feature flag `tengu_onyx_plover`, off on 2026-11-03) checked for what it records, because a platform feature that proposes rules from recurrence makes the proposer a duplication. Its kill test, pre-registered in the ledger decision, separates "no proposal delivered in eight weeks" (the sweep did not run; fix the routine, not the counter) from "proposals delivered and none accepted" (delete).

Deferred to that round, recorded here so they are not lost: the forms and their standing costs; the kind rule (a repeated break may propose only an enforcing form or deletion); the card's layout under the Decision template's first two sections (the verdict card previews exactly those); the validator's refusal list; budgets and backpressure; the loud withdrawal of an unanswered proposal; a provenance stamp on cards; the event table and the `settled:` shortlist line; Alternatives I, L, M and P below.

### The cut: what goes and what replaces it

Removed in Phase 1: `tenet/patterns.py`, `tenet/observer/pattern_drafts.py`, `tenet/observer/usage.py`, `cli.py pattern name`, `verdict._naming` and the `.pattern` session marker, the pending-marker test in `verdict.eligible`, the sweep's pattern section, the `new_uses`, `pattern_groups`, `pattern_drafts` status values (dropped from an upgraded `status.env` by the next scan), `tests/test_patterns.py` and the pattern and usage tests elsewhere, and the sentences about them in `README.md`, the two skills' texts and `conventions.md`. Kept untouched: `verdicts.jsonl`, `ledger.template_headings()` (called by `ledger.section_heading()`), `promote.py`.

Nothing moves the three old state files. The upgrade note in the CHANGELOG and the README gives the author two commands.

The cut is paired with a ledger act by the author: a draft decision superseding 2026-09-27, placed in `inbox/` by `/tenet:tenet-capture`, carrying the division with dream.py, the kill test, the baseline of 2026-11-03 and the verified fact that the ledger remote is private. The release never edits the 09-27 note.

### Rollback

The README's "Rolling back" section (item 19) is the one runbook; it is written from the rollback drill, not guessed.

## Alternatives Considered

### Alternative A: Keep the current pipeline and fix it

*   **Pros**: No cut; printing the dropped component sizes and lowering the cosine threshold are small edits; the usage log could feed the 90-day archive if its consumer were built.
*   **Cons**: It measures note-to-note topic proximity and assistant-text citations (35 percent draft links, 27 percent same-day self-citations), not the author repeating himself; three drafts ever, none accepted as drafted; two tuned constants in front of a silent zero.
*   **Reason for Rejection**: The author's intent is recurrence in his own words; no parameter change turns a note-similarity graph into that. The ledger's rule for a layer that fails its revisit clause is deletion, not more prose.

### Alternative B: Rewrite the counter in place of the pattern modules

*   **Pros**: Fewer files to add; the `pattern name` validator and the pending marker could be reused.
*   **Cons**: The pattern machinery is wired into five modules, two session markers, status keys, tests and three skill texts; an in-place rewrite inherits them, so the counter becomes as hard to delete as the old pipeline; a partial deletion kills both hooks because `cli.py` imports the modules at the top level.
*   **Reason for Rejection**: Deletion in one release and one new module keep the counter deletable.

### Alternative C: Build the prompt counter in dream.py and let tenet only deliver

*   **Pros**: dream.py already has the reader, the three-session rule and the filter; "stage 2" is small there.
*   **Cons**: Two readers with two rule sets stay; a published plugin cannot depend on a private script; dream's weekly trigger is unverified and may be manual, the flaw the author named.
*   **Reason for Rejection**: The author chose a publication-ready tenet; one reader must remain, and it must be the plugin's.

### Alternative D: Sentence shingles with per-session dedupe as the detector

*   **Pros**: Cheap, deterministic, no model.
*   **Cons**: The end-of-session family is one to three words, below any shingle floor; the long forms are paraphrases that share no trigram.
*   **Reason for Rejection**: It returns zero for exactly the recurrences the feature exists to find (measured: the four bare forms share no six-word run with anything).

### Alternative E: A stem-pair inverted index now (deferred)

*   **Pros**: Higher recall on paraphrases that share two anchor stems; no chaining into components.
*   **Cons**: Two constants (document-frequency ceiling, pair support) that need measurement; a prompt can land in several candidates; six-character stems do not unify inflected Hungarian forms ("kényszerítve" and "kikényszerítve" stem differently).
*   **Status**: Deferred. Exact keys find the acceptance case today; the paraphrase family has 2 sessions this month. The pair index is built when a paraphrase family reaches threshold and exact keys miss it.

### Alternative F: Let the sweep model cluster the raw prompts from the dump

*   **Pros**: No detector code; judgement handles paraphrases.
*   **Cons**: About a thousand prompts a month into a dump that already spills past the inline limit; recall unmeasurable; prompts from sensitive projects would sit in the dump.
*   **Reason for Rejection**: Breaks the dump's determinism and the privacy rule.

### Alternative G: A daily counter phase of the scan with persisted state (the second draft)

*   **Pros**: A receipt every day; a session-start banner with the number of keys at threshold; history beyond the 30-day window in the plugin's data directory.
*   **Cons**: Nothing in the counter release reads that state except the weekly dump; the dump runs from the skill's `!` block, whose environment is unverified and which the CI invariant forbids to carry `TENET_DATA`, so the dump could not reach the data directory; a persisted sensitive flag would be frozen at write time; a by-hand pass would race the scan's lock; `promote.run` already prints the late-sweep notice; the brief would be recomputed daily as a side effect.
*   **Reason for Rejection**: Twenty review findings against machinery with no consumer. The stateless dump costs 3.5 s a week and needs no environment.

### Alternative H: A dedicated scheduled routine as the trigger

*   **Pros**: Independent of the author's sessions.
*   **Cons**: New surface (a routine, its receipt, its supervision) in the layer under review; a published plugin cannot install a routine for its user.
*   **Reason for Rejection**: Surface growth without a benefit the weekly sweep lacks.

### Alternatives I, L, M and P (the proposer's round)

Deferred with the proposer: **I** a separate proposal store in the data directory (rejected in the brainstorm: two stores, two gate paths); **L** Accept executes the form (rejected: a harness-level change by a verdict click); **M** phrasing at the resting point through a validating command (the upgrade if the fourth typing keeps arriving before the weekly draft); **P** a "later" option with a deferral store (rejected: unused in 54 verdicts; a silent expiry is the failure the author fears).

### Alternative J: Deliver through the digest's `open:` items

*   **Pros**: The weekly path exists and its items are answered (4 of 5 measured).
*   **Cons**: The only reader is the author's private script; an item is one line and cannot carry evidence; the queue grew from 10 to 21 in a week.
*   **Reason for Rejection**: Not a channel the plugin owns. The draft is the copy of record.

### Alternative K: Deliver at session start

*   **Pros**: Autonomous and cheap to print.
*   **Cons**: Session start is context for the model, not a question to the author; the sweep nag appeared in 50 sessions and started 3 sweeps.
*   **Reason for Rejection**: It does not reach the author.

### Alternative N: Keep the note source in the first build

*   **Pros**: The author said note redundancy can signal a pattern too.
*   **Cons**: The weekly sweep model already finds note overlap by reading the ledger (the process log records a triple of "ellenpróba" notes and an "oppira" pair found that way) while the cosine dump said zero; a code detector for notes would be a graph again or an exact-key check nobody has asked for.
*   **Reason for Rejection**: The graph is deleted; check 6 is retired; the model may draft the rule it reads.

### Alternative O: "Remove it at the January retro if it is not useful"

*   **Pros**: Light.
*   **Cons**: It repeats the 2026-09-27 pattern: an open-ended revisit nothing can evaluate.
*   **Reason for Rejection**: Replaced by the baseline, the weekly digest series and a pre-registered delete condition in the ledger decision.

### Alternative Q: Rely on the platform's auto memory and check 8

*   **Pros**: No new code; the 2026-08-28 decision forbids duplicating the platform, and check 8 already turns repeated feedback into a verdict.
*   **Cons**: Auto memory records what the assistant chooses to save (32 feedback notes on this machine, none about the end-of-session question); check 8 reads those notes and the process log; neither sees a prompt the assistant answered without saving anything.
*   **Reason for Rejection**: The counter reads the one source nothing else reads. The platform's memory-consolidation flag is a gate before the proposer is built, not a reason to skip the counter.

--------------------------------------------------------------------------------

## Non-Functional Requirements

*   **Security and privacy.** The counter persists nothing. Prompt text appears only as a shortlist example: at most 100 characters, cut at a word boundary, the newest non-sensitive occurrence of a key, printed only when `_meta/sensitive` exists in the ledger and only after the example filter has passed the whole record (the PII patterns and the authority-language pattern of item 22, and gitleaks when the binary is present; without gitleaks the stdlib patterns decide and the receipt line says `gitleaks: absent`; a gitleaks error withholds the example). Sensitive projects are never shown: no key, no example, no name, in any line. An example the sweep model copies into a digest or a draft persists in the ledger, which is private (verified 2026-11-03). The README's privacy section states all of this in the words of item 28.
*   **Performance.** No hook changes in Phase 2. The dump gains the transcript parse (3.5 s for 266 sessions, measured 2026-11-03) and the keying (0.12 s for 1050 prompts); the sweep is weekly. Memory is the scan's own (the session dicts), with no retained text beyond them.
*   **Rollout and rollback.** Three releases, each a version bump with one CHANGELOG line. The cut ships with the upgrade note and the rollback section. The counter ships only after the live check (`vegezt` at threshold on the author's machine, four acknowledgement keys ignored) and with the fixture green. Nothing in the counter release changes a file 3.6.1 reads or writes. The proposer waits for its gates.
*   **Observability.** Every dump prints the receipt line; the digest keeps it, and the cluster lines, every week; `recurrence status` prints the section on demand. There is no daily signal and no banner: `promote.run`'s existing notice says when the sweep is late.
*   **Risks and mitigations.**

| Risk | Trigger | Consequence | Mitigation | Residual |
| :-- | :-- | :-- | :-- | :-- |
| The weekly sweep does not run | the author's routine dies silently | keys at threshold are never seen | `promote.run` prints `Maintenance is due` at session start after seven days | the author must still start the sweep; the counter has no signal of its own |
| Acknowledgements flood the shortlist | one-stem keys such as "kész" | the real recurrence hides below them | the stoplist of four measured acknowledgement stems; a cap of five with a count of the rest | a new acknowledgement needs a measurement to be added |
| The digest does not carry the trace | the model skips the copy instruction | the January retro has no weekly series | the instruction is in the skill text with a content test; the retro can recompute any week still inside the window | weeks older than 30 days are lost if the digest skipped them |
| Sensitive text reaches an output | the sensitive list is incomplete | an example from a project the author considers private | the list is the author's file; counts and dates never reveal text; the model never quotes a sensitive project | the author must keep the list complete |
| gitleaks absent | another machine, or a fresh install | a secret in an example passes the stdlib patterns | the receipt line says `gitleaks: absent`; the README says what the patterns cover | a secret that matches no pattern |
| A textindex change re-keys prompts | a release edits STOP or SUFFIXES | week-to-week series shift | the digest records the key strings; the retro reads them with the change date | none for the counter itself, which keeps no state |
| The platform ships recurrence proposals | memory consolidation turns on | the proposer duplicates the platform | the gate before Phase 3 | none for the counter, which still feeds the sweep |

--------------------------------------------------------------------------------

### Additional Resources

*   The retrospective of 2026-11-02 and its artifacts, in the ledger: `_meta/retro/2026-11-02/` (the Hungarian report; `release-plan.md` with batches B0, B1a–d, B2a–b, B4; `evidence/verified-all.json`, ids observer-04, -07, -16, -17, -18, -32, -45, verdict-lifecycle-01, -14, -16, -19, -20, -21, value-measure-15, -16, -17; `egm/` the concepts brief and brainstorm reviews; `egm-review/` and `egm-review/round2/` this document's two review rounds; `egm-review/spike.json` the measurement of 2026-11-03).
*   Ledger decisions: `2026-09-27-elfogadas-nem-vegallapot`, `2026-08-09-mechanizmus-vagy-torles`, `2026-08-28-nem-duplikaljuk-a-platformot`, `2026-07-26-minimalis-felulet`, `2026-09-26-dream-wrap-stop-guard` (reversed 2026-10-09); the process log `_meta/retro.md`.
*   The author's private `~/.claude/dream/dream.py`: the source of the prompt reader, `parse_ts`, `project_of`, the PII and authority patterns and `gitleaks`.
*   tenet issue #2 (no `pattern` notes after a month of use).

### Future Improvements

*   **The stem-pair index** (Alternative E) when a paraphrase family reaches threshold and exact keys miss it.
*   **Phrasing at the resting point** (Alternative M) when the digests show the fourth typing arrives before the weekly draft.
*   **A note-side exact detector** (a `related` or `derived` target cited by three or more notes), only if the sweep model stops finding note overlap by reading.
*   **The 90-day archive**, re-decided at the January retro from the digest series and the keys that never recur.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

Two phases are planned here; the proposer is not. Each phase is one version bump and one CHANGELOG line. Phase 1's items quote the code as it stands at 3.6.1 (commit 5026905); items 1 to 9 and the test deletions of item 20 land in one commit, because `cli.py` imports `sweep`, `verdict` and `run`, which import the retired modules. Phase 2's order: 24, 23, 22 with its tests, 25 and 26, then 27 to 29. Every constant lives in one block at the top of its module with a one-line comment naming the measurement or decision it came from. No production code is written from this document; the formats below are the contract.

### Phase 1: the cut (3.7.0)

#### 1. `tenet/patterns.py` (Delete)

*   **Type / Scope**: Python module, the note-similarity grouping (TF-IDF cosine 0.08, size cap 8).
*   **Proposed Changes**: Deleted. Callers: `tenet/sweep.py` (`patterns.render(vault)` in `render()`), `tenet/observer/pattern_drafts.py`, `tests/test_patterns.py`. Rationale: it detects topic proximity among notes, not recurrence; on the live ledger it collapses 99 of 115 accepted decisions into one dropped component and makes the sweep print a false zero.

#### 2. `tenet/observer/pattern_drafts.py` (Delete)

*   **Type / Scope**: Python module, machine pattern drafting from a verbatim quote, the pending marker, `name()`.
*   **Proposed Changes**: Deleted. Callers: `run.scan`, `verdict.eligible`, `verdict.gate`, `cli.py` (`pattern name`), `tests/test_patterns.py`, `tests/test_verdict.py`. It calls `ledger.template_headings`, which stays (item 10). Rationale: three drafts ever, two reworked by hand after an edit verdict and one set aside; two J-class entries; the naming Stop fired 0 times in 42 rounds.

#### 3. `tenet/observer/usage.py` (Delete)

*   **Type / Scope**: Python module, the note-citation log and `measured_since`.
*   **Proposed Changes**: Deleted. Callers: `run.scan`, `tests/test_observer.py`. Rationale: no reader outside tests; its semantics are not the recurrence signal; its read-error path erases up to 150 days of history behind a green message.

#### 4. `tests/test_patterns.py` (Delete)

*   **Proposed Changes**: Deleted with its module.

#### 5. `tenet/cli.py` (Modify)

*   **Proposed Changes**: The import `from tenet.observer import brief, pattern_drafts, run  # noqa: E402` becomes `from tenet.observer import brief, run  # noqa: E402`. The three parser lines `pat = sub.add_parser("pattern")`, `pat.add_argument("action", choices=["name"])`, `pat.add_argument("draft")` are deleted; the following line `obs = sub.add_parser("observe")` stays. The handler block starting `if args.command == "pattern":` (four lines, through `return 0`) is deleted. In `observe()`, the print after `result = run.scan(vault, data)` formats the scan's new two-tuple as `scan: {sessions} session(s), {projects} project brief(s)`. Rationale: the modules are gone; a top-level ImportError would kill both hooks before any handler runs, which is why items 1 to 9 are one commit.

#### 6. `tenet/observer/run.py` (Modify)

*   **Proposed Changes**: The imports of `usage` and `pattern_drafts` go. `_write_status(data, **values)` becomes `_write_status(data, _drop=(), **values)`: after `current = status(data)`, `for k in _drop: current.pop(k, None)`. In `scan()`, the lines `new_uses = usage.update(vault, sessions, oldest)` and `groups, drafts = pattern_drafts.write(vault, sessions)` are deleted; `sessions, _ = transcripts.sessions(30)` (nothing reads `oldest` any more); the final `_write_status(...)` call drops `new_uses`, `pattern_groups` and `pattern_drafts` from its arguments and passes `_drop=("new_uses", "pattern_groups", "pattern_drafts")`; `scan()` returns `len(sessions), count`. Rationale: the scan retained three dead products, and `_write_status` merges, so a key it stops setting would otherwise stay in `status.env` for ever.

#### 7. `tenet/observer/transcripts.py` (Modify)

*   **Proposed Changes**: In `read()`, `"assistant": []` leaves the session dict; the branch `if b.get("type") == "text": s["assistant"].append(b.get("text", ""))` is deleted and the following `elif b.get("type") == "tool_use":` becomes `if b.get("type") == "tool_use":`; the loop over assistant records stays, because it collects `paths` and `asked` from `tool_use` blocks. The module docstring's mention of what the assistant cited and `read()`'s docstring phrase "and the assistant's own text" go. Rationale: the scan retained every assistant text of 267 sessions for one deleted consumer.

#### 8. `tenet/verdict.py` (Modify)

*   **Proposed Changes**: The import `from tenet.observer import pattern_drafts, transcripts` becomes `from tenet.observer import transcripts`. In `eligible()`, the condition `and pattern_drafts.PENDING not in body` is removed and the docstring's clause "and stated (a pattern draft waits for its statement)" goes. `_naming()` is deleted whole. In `gate()`: the line `unstated = [] if (markers / f"{session}.pattern").exists() else pattern_drafts.pending(vault)` is deleted; `if not (unstated or k) or busy(payload):` becomes `if not k or busy(payload):`; the two lines `if unstated:` and `return _naming(vault, data, unstated[0]) if _claim(markers / f"{session}.pattern") else None` are deleted; the docstring's last two sentences (from "A pattern draft is stated") go. Nothing else changes; the per-draft claim and the option cut are batch B2a. Rationale: the naming round never fired, and its marker is dead text once the drafts cannot exist.

#### 9. `tenet/sweep.py` (Modify)

*   **Proposed Changes**: `from tenet import ledger, patterns, paths` becomes `from tenet import ledger, paths`. The line `out += ["", "--- pattern candidates (decisions that may share an insight) ---", *patterns.render(vault)]` is deleted; no tombstone (history belongs in the CHANGELOG, and the retired check-6 entry in the skill text tells the model what happened). Rationale: the section printed a false zero every week.

#### 10. `tenet/ledger.py` (No change)

*   `template_headings()` stays: `section_heading()` calls it (`heads = template_headings(vault, "Decision")`), and `verdict.eligible`, `promote.run`, `sweep.render` and `brief.corpus` depend on `section_heading()`. Only its callers in `pattern_drafts.py` disappear with that module.

#### 11. `tenet/promote.py` (No change)

*   A leftover draft carrying `<!-- pattern-statement: pending -->` is an ordinary proposed draft once item 8 lands; the README upgrade note tells the author to discard it. No mover, no notice.

#### 12. `skills/tenet-sweep/SKILL.md` (Modify)

*   **Proposed Changes**: The check-6 entry, from `6. **Pattern candidates.** Three or more decisions sharing a rationale…` through its last line, becomes `6. **Pattern candidates.** Retired in 3.7.0: the observer no longer groups notes or drafts patterns, and the dump has no section for it. Nothing to do.` In `## What this must never do`, the line `- Write a \`pattern\`. Propose; never author.` is deleted: the author relaxed the rule (the model may phrase a rule it finds by reading; the author's verdict decides whether it is his). Rationale: stable numbering; the never-list must not restate a rule the author withdrew.

#### 13. `skills/tenet-sweep/references/checks.md` (Modify)

*   **Proposed Changes**: Section `## 6. Pattern candidates` keeps its heading and is reduced to: `Retired in 3.7.0. The observer no longer groups notes or drafts patterns, and the dump has no section for it. A rule you find by reading three notes is an ordinary decision draft through check 8's slot: the rule under the Decision heading, the notes it rests on and the author's own words, when they are on record, under the Why heading of the ledger's Decision template (its third \`##\` heading, in the ledger's language).` The fenced question template and the paragraph `A pattern records the user's own insight…` are deleted. Section 8 is unchanged in this phase.

#### 14. `skills/tenet-capture/SKILL.md` (Modify)

*   **Proposed Changes**: The line `Skip a pattern draft still marked \`pattern-statement: pending\`: a resting point states it first.` is deleted. Rationale: no such draft is special any more.

#### 15. `skills/tenet-capture/references/conventions.md` (Modify)

*   **Proposed Changes**: In `## Evidence versus insight`, the sentences `A \`pattern\` records only the user's own insight: it is drafted only when the user's own words on it are on record, and it keeps them under Where it came from. The model may phrase the rule; the user's verdict decides whether it is theirs.` become `A \`pattern\` records an insight the user has endorsed: the model may phrase the rule, the user's own words, when they are on record, stay under Where it came from, and the user's verdict decides whether it is theirs.` The templates paragraph (`The machinery reads exactly one of them: the first \`##\` heading of \`templates/Decision Template.md\``) becomes true once item 2 lands and stays as written.

#### 16. `vault-template/.gitignore` (Modify; supersedes batch B0's one-line rule)

*   **Proposed Changes**: The final file: the five existing lines (`.obsidian/workspace.json`, `.obsidian/workspace-mobile.json`, `.obsidian/cache`, `.trash/`, `.DS_Store`), then `.obsidian/graph.json` (Obsidian rewrites it constantly; it carries no knowledge; the live ledger already ignores it), then `# observer state holds session ids and local paths: per-machine, not knowledge`, `_meta/observer/*`, `# date, draft name, verdict: the record the retro reads`, `!_meta/observer/verdicts.jsonl`. The author replaces the live ledger's `_meta/observer/` line with the last two rules by hand. Rationale: the live ledger committed observer logs once and the fix never reached the template; `verdicts.jsonl` is the one durable record and the live ledger currently ignores it with the rest.

#### 17. `README.md` (Modify)

*   **Proposed Changes**, each by its sentence: (a) in the bullet `**Nothing enters without your verdict, and the verdict comes to you.**`, delete the sentence `A pattern draft is stated first: at a resting point the session's model writes the rule its decisions share, where it holds and where it does not, and the draft is renamed after it.` (b) In the "What runs when" table's `after each response` row, delete `, or first a pattern draft's statement`. (c) In "Privacy", "What it writes": replace the text from `; the observer appends to \`_meta/observer/usage.jsonl\` in the ledger` through `renames it after the statement's title. It writes its briefs and status to the data directory Claude Code assigns the plugin (\`~/.claude/plugins/data/tenet-…/\`).` with `; the observer writes its briefs and status to the data directory Claude Code assigns the plugin (\`~/.claude/plugins/data/tenet-…/\`) and nothing to the ledger.` (d) In "What the observer reads": replace `and the file paths tools touched decide which notes matter in which project; the assistant's text is searched only for ledger note names it cited. None of that text is stored, with one exception: a pattern draft quotes the single prompt sentence it was built from. A brief holds note names and the first sentence of each note, and the usage log holds what is listed above.` with `and the file paths tools touched decide which notes matter in which project. None of that text is stored. A brief holds note names and the first sentence of each note.` (e) In "Known limits", delete the bullet `Relevance is measured, not perfect: …` (its figure came from the deleted log). (f) Under `## Configuration`, after the table, add the paragraph `**Upgrading from 3.6.x.** The observer no longer writes \`_meta/observer/usage.jsonl\`, \`patterns.json\` and \`state.json\` and does not read them. In the ledger run \`git rm --cached _meta/observer/state.json\` if it is tracked, and \`rm _meta/observer/usage.jsonl _meta/observer/patterns.json _meta/observer/state.json\` (or keep the files). A pattern draft left in \`inbox/\` with the marker \`pattern-statement: pending\` is asked as an ordinary draft; discard it.` (g) Also under `## Configuration`, add the subsection `### Rolling back` with the runbook of item 19. The remaining README corrections are batch B4 of the retrospective.

#### 18. `CHANGELOG.md`, `.claude-plugin/plugin.json` (Modify)

*   **Proposed Changes**: `- **3.7.0** (date): the observer's measuring half is gone: no usage log, no machine pattern drafts, no naming round, no \`pattern\` subcommand, no pattern section in the sweep dump; the vault template ignores observer state but tracks verdicts.jsonl; a rollback section in the README. Upgrading: in the ledger, \`git rm --cached _meta/observer/state.json\` if tracked, and delete or keep usage.jsonl, patterns.json and state.json. Decided in the ledger: <slug of the superseding decision, filled at release>.` `version` to `3.7.0`.

#### 19. The rollback runbook (README, `### Rolling back` under Configuration)

Five numbered lines, written from the rollback drill (Verification Plan) and nothing the drill did not run: (1) the commands that reinstall 3.6.1 from the tag `tenet--v3.6.1` (candidates to drill: a checkout of the tag in the marketplace clone followed by uninstall and install; the drill records what worked). (2) 3.6.1's next scan appends to `_meta/observer/usage.jsonl` again, from the last 30 days only, and writes a fresh `state.json`; it writes `patterns.json` only when it next emits a pattern draft, so a group proposed before the cut can be proposed again unless you kept your copy of the file. (3) 3.6.1 asks any proposed draft in `inbox/` as an ordinary draft; a draft the sweep wrote from the shortlist included. (4) The ledger's `.gitignore` edits are yours; 3.6.1 does not need them reverted. (5) Verdicts and ledger decisions stay as decided; rolling back code rolls back no verdict.

#### 20. Tests (Modify)

*   `tests/helpers.py`: delete `HU_PATTERN_TEMPLATE` and `PATTERN_SPEC` (orphaned); if batch B0 has not shipped, add to `VaultCase.setUp`, after the environment snapshot, `TENET_DATA` and `CLAUDE_CONFIG_DIR` pointed at temporary directories.
*   `tests/test_observer.py`: the import `from tenet.observer import brief, run, textindex, transcripts, usage` drops `usage`; the class `Usage` is deleted; `ObserverReviewFindings.test_a_damaged_usage_line_loses_nothing` is deleted; the helper `session(root, prompts=(), assistant=(), asked=(), sid="s1", day=None)` drops `assistant` if no remaining test passes it. Added: `test_scan_returns_sessions_and_briefs_and_drops_the_retired_keys` (a seeded `status.env` with `new_uses=1`, `pattern_groups=2`, `pattern_drafts=0`; after `scan` the three keys are gone and `last_ok` is set; the two-tuple is returned).
*   `tests/test_verdict.py`: `from tenet.observer import pattern_drafts, run` becomes `from tenet.observer import run`; the helpers import drops `HU_PATTERN_TEMPLATE, PATTERN_SPEC`; the class `PatternGate` is deleted. Added: `test_a_draft_with_the_old_pending_marker_is_an_ordinary_draft` (a proposed draft whose body holds `<!-- pattern-statement: pending -->` is in `eligible()`; failing direction: it was excluded in 3.6.1).
*   `tests/test_core.py`: added `test_pattern_subcommand_is_gone` (`cli.py pattern name x` exits 2); `test_template_gitignore_ignores_observer_state_but_not_verdicts` (bootstrap a temporary ledger, `git init`, `git check-ignore` exits 0 for `_meta/observer/x.jsonl` and 1 for `_meta/observer/verdicts.jsonl`); `test_sweep_has_no_pattern_section`. The leftover-name check is a verification step (below), not a permanent test.

#### 21. The ledger act (outside the repository, by the author)

A draft decision in `inbox/`, written with `/tenet:tenet-capture`, that supersedes `2026-09-27-elfogadas-nem-vegallapot`: recurrence counting replaces use counting; the archive is deferred to the January retro with `revisit` set to that date; the division with dream.py; the verified fact that the ledger remote is private (2026-11-03); the kill test (after eight weeks of the counter: the digests show keys at threshold that the sweep never drafted, or, once the proposer exists, no proposal accepted in eight weeks of delivered proposals, or an accepted key still recurring without a mechanism); the baseline row `2026-11-03: 7 keys at threshold, 3 after the four acknowledgement stems (vegezt; the usage-limit continuation text; "miért álltunk meg")`; `supersedes` pointing at the 09-27 note. The 3.7.0 CHANGELOG line names the slug. The release does not edit the 09-27 note.

### Phase 2: the counter

The first minor release after the cut. Ships only after the live check (Verification Plan) and with `tests/test_recurrence.py` green.

#### 22. `tenet/observer/recurrence.py` (Create)

*   **Type / Scope**: Python module, stdlib only, no state, no import-time work; a pure computation over session dicts. No type annotations that Python 3.9 rejects (no `X | None`).
*   **Constants** (one block): `MIN_SESSIONS = 3` (the author's "more than two or three times"; dream.py's rule), `MIN_DAYS = 2` (one afternoon is not a pattern), `COLLAPSE_SECONDS = 600` (parallel sessions typing the same key within ten minutes count once), `SHORTLIST_MAX = 5`, `NEAREST_MAX = 3`, `PROJECTS_SHOWN = 3`, `EXAMPLE_CHARS = 100`, `ACK_STEMS = ("try", "mehe", "kesz", "folyta")` (one-stem acknowledgement keys ignored at threshold; measured 2026-11-03: "try again" 11 sessions, "mehet" 6, "kész" 4, "folytasd" 3; extended only with a measurement), `GITLEAKS_TIMEOUT = 10` (seconds), and the patterns ported from dream.py with English labels: `PII = {"email": r"[\w.+-]+@[\w-]+\.[\w.-]+", "phone (HU)": r"(?:\+36|\b06)[ /-]?\d{1,2}[ /-]?\d{3}[ -]?\d{3,4}\b", "bank account (HU)": r"\b\d{8}-\d{8}(?:-\d{8})?\b", "IBAN (HU)": r"\bHU\d{2} ?(?:\d{4} ?){6}\b", "tax id (HU)": r"\b8\d{9}\b", "social security id (HU)": r"\b\d{3}[ -]\d{3}[ -]\d{3}\b|\b\d{9}\b"}` and `AUTHORITY = r"always allow|bypass(?:Permissions)?|dangerously|ignore (?:all |any )?(?:previous|prior|above)|you are (?:now )?authori[sz]ed|no need to (?:ask|confirm)|skip (?:the )?confirm|without asking|mindig engedélyez|ne kérdezz|kérdezés nélkül|hagyd figyelmen kívül|felhatalmaz|engedély nélkül"` (case-insensitive; an example that carries such language must not be shown to a model as evidence).
*   **Functions** (the contract; signatures in prose): `key_of(text)` returns the key (sorted set of `textindex.tokens(text)`, joined by spaces) and the stem count; an empty token list gives an empty key. `occurrences(sessions, now)`: for each session and each key, the earliest in-window record (`ts`, local day via `astimezone()`, the project name from `paths.project_name(session["root"], vault)`, the record's text); then the collapse: rows of one key sorted by `ts`, a row within `COLLAPSE_SECONDS` of the previously kept row of that key is dropped. `candidates(rows)`: per key with at least two sessions, the sessions, the local days, the project names, the first and last day, the occurrence count and the stem count. `at_threshold(cands)`: sessions at least `MIN_SESSIONS` and days at least `MIN_DAYS`, minus keys whose only stem is in `ACK_STEMS` (counted as ignored); sorted by sessions descending, then occurrences descending, then key. `nearest(cands)`: the keys below threshold that occur in at least one non-sensitive project, sorted by sessions then days descending, at most `NEAREST_MAX`, each with its sessions and days. `example(cand, prefixes)`: the newest occurrence of the key from a non-sensitive project; returns the cut text and an empty reason, or no text and one of the reasons `sensitive only`, `filter: <PII label>`, `filter: authority language`, `gitleaks: <RuleID>`, `gitleaks: error`; the filter runs on the whole record text before the cut; the cut is at `EXAMPLE_CHARS` on a word boundary. `filter_reasons(text)`: the PII labels that match, `authority language` when `AUTHORITY` matches, and gitleaks when present: `gitleaks stdin --no-banner --log-level error --report-format json --report-path -` with the text on stdin and `GITLEAKS_TIMEOUT`; exit status 0 means clean, 1 with parseable JSON means findings (their `RuleID` values), anything else (timeout, other status, unparseable output) is `gitleaks: error`, which withholds the example. `command_counts(sessions)`: a counter over every session's `commands`, all projects. `receipt(sessions, rows, cands, now, prefixes_present, prefixes)` and `receipt_line(...)`: one format, `recurrence <date>: examined S sessions, P prompts (N without content stems, U without a timestamp), K keys, C candidates, T at threshold, A ignored as acknowledgements; nearest below: key (n sessions, d days), …; examples: on (sensitive list: P prefixes) | withheld (no _meta/sensitive in the ledger; create it, empty or with one project-name prefix per line, to allow examples); gitleaks: present | absent`. `shortlist(sessions, vault, now)`: the section lines in the format below. `sensitive(project, prefixes)`: `project.startswith(prefixes)` when `prefixes` is non-empty.
*   **Shortlist format**: the receipt line; then per key at threshold, in rank order up to `SHORTLIST_MAX`: `1. vegezt · 6 sessions · 5 days · 4 projects (tenet, ledger, atlas, +1) · 2026-10-09 .. 2026-11-02` (the first `PROJECTS_SHOWN` non-sensitive names in alphabetical order, then `+N` for the rest and `+N sensitive` for sensitive ones), then `   e.g. 2026-11-02 · tenet · "akkor végeztünk"` when the list exists and the filter passed, else `   e.g. none shown: <reason>` (`examples withheld` when the list is absent); a key whose occurrences are all sensitive prints `1. [sensitive projects only] · 3 sessions · 2 days` and nothing else. Then, when the cap cuts, `and N more at threshold: <keys of non-sensitive ones>; K sensitive-only`. Then `no key at threshold` when none is. Then `commands typed in the last 30 days: /wrap 31, /verdicts 2, /tenet:tenet-sweep 4` (what the author triggers by hand, next to what he types; the model may propose from both).
*   Rationale: one module, no state, every number and message pinned here; what the implementer decides is nothing.

#### 23. `tenet/observer/transcripts.py` (Modify; folds batch B1d's window fix)

*   **Proposed Changes**: `read(path, cutoff)` and `sessions(days, now=None)`: `now` defaults to `time.time()`, `cutoff = now - days * 86400`. `parse_ts(value)` ported from dream.py (replace a trailing `Z` with `+00:00`, `datetime.fromisoformat`, `.timestamp()`; `None` on any failure). In `read()`, a human prompt record (the existing filter: `origin.kind == "human"`, not `isMeta`, not a wrapper) is kept as `{"text": t, "ts": parse_ts(r.get("timestamp"))}` only when `ts` is not `None` and `ts >= cutoff`; `s["records"]` is that list, `s["prompts"] = [r["text"] for r in s["records"]]`, and `s["untimed"]` counts the dropped prompts without a timestamp. `s["commands"]`: for every user record, `re.findall(r"<command-name>/?([^<\s]+)</command-name>", text)`, wrappers included. The file-mtime selection in `sessions()` stays. The test helper `session()` in `tests/test_observer.py` gains `records`, `commands` and `untimed` with defaults. Rationale: dates on a shortlist must be real; the brief stops reading months-old prompts; the manual-trigger signal must be visible.

#### 24. `tenet/paths.py` (Modify)

*   **Proposed Changes**: `project_name(root, vault)`: the first path component of `root` relative to `Path(vault).parent` when `root` is under it, `.claude` when under `config_dir()`, else the last component of `root` (dream.py's `project_of`, with the ledger's parent as the root). `sensitive_list(vault)`: reads `<vault>/_meta/sensitive`; returns `(present, prefixes)` where `present` is whether the file exists and `prefixes` is the tuple of its non-empty lines that do not start with `#`, stripped. Rationale: every entry point reads the same file; no environment variable is involved.

#### 25. `tenet/sweep.py` (Modify)

*   **Proposed Changes**: In `render(vault)`, after the existing sections, `sessions, _ = transcripts.sessions(30)` and the section `--- recurrence shortlist (the author's own prompts, last 30 days) ---` followed by `recurrence.shortlist(sessions, vault, time.time())`; the imports gain `recurrence` and `transcripts`. When the transcript directory is missing or empty, the section holds the receipt line in its `NOT EXAMINED (no transcripts under <path>)` form. Rationale: the sweep model works from the dump and must see denominators and near misses; the dump needs no data directory.

#### 26. `tenet/cli.py` (Modify)

*   **Proposed Changes**: Subparser `recurrence` with `status`: prints the shortlist section over `transcripts.sessions(30)` for the configured ledger; exit 0. Rationale: the live check and by-hand reading without running the whole dump.

#### 27. `skills/tenet-sweep/SKILL.md` and `references/checks.md` (Modify)

*   **Proposed Changes**: Check 8 becomes "Repeated process deviations and recurrences" with three inputs: the `recurrence shortlist` section (new), `_meta/retro.md` and the feedback notes (as today). For each key at threshold the model decides whether it is a real recurrence (not an acknowledgement the stoplist missed, not a pasted template such as the platform's usage-limit text), then reads the ledger and the installed skills (`~/.claude/skills/*/SKILL.md` and the plugin's `skills/`) to decide whether an existing rule, note or skill already covers it (then the two-outcome rule applies: a mechanism that fails, or deletion; never a restated rule) or whether it is a new expectation (then it names the rule in one sentence in the language of the example and the form it would take: a note, a CLAUDE.md line, a hook, a skill, a loop, a harness setting). It writes at most one decision draft per run through the existing slot, the shortlist's highest-ranked real recurrence first when several inputs compete, with the rule under the Decision heading and the example line, the counts and the covering notes or skills under the Why heading of the ledger's Decision template (its third `##` heading, in the ledger's language). The model never quotes a sensitive project and never writes counter state (there is none). The digest section gains: copy the receipt line verbatim and one line per key at threshold (key, sessions, days, projects; no example text) into the digest every week, clean weeks included, followed by the name of the draft written from the shortlist or the reason none was; the "if everything is clean, say so in one line" rule is amended to keep these lines. A content test (`tests/test_core.py`) asserts the skill text contains the copy instruction and the Why-heading instruction.

#### 28. `README.md` (Modify)

*   **Proposed Changes**: "What it does": one bullet for the counter (the weekly sweep's dump counts which of your prompts recurred across sessions in the last 30 days and lists them; the sweep's model may write one decision draft from the list; nothing enters without your verdict). "What runs when": the `a slash command` row gains `the sweep also reads your last 30 days of transcripts for the recurrence shortlist (a few seconds)`. "Configuration": `_meta/sensitive` in the ledger, one project-name prefix per line; its presence allows examples in the shortlist; without it the shortlist shows keys and counts only. "Privacy": what the counter reads (your prompts of the last 30 days with their timestamps; the names of typed commands), that it stores nothing, what it shows (one example of at most 100 characters per recurring key in the sweep dump, from projects not on your sensitive list, after the PII and authority-language patterns and gitleaks when present), that the sweep model may copy an example into a digest or a draft in the ledger, and that a sensitive project is counted and never shown. "Known limits": the detector matches exact stem sets, so a paraphrase of the same question is a different key, and the acknowledgement stoplist holds the four measured stems.

#### 29. `CHANGELOG.md`, `.claude-plugin/plugin.json` (Modify)

*   **Proposed Changes**: One line naming the counter, the shortlist, the digest trace and the sensitive-list file; `version` bumped to the next minor.

#### 30. `tests/test_recurrence.py` (Create), `tests/test_core.py` and `tests/test_observer.py` (Modify)

*   **Fixture**: built in `setUp` as session dicts (and, for the CLI tests, as JSONL files under a temporary `CLAUDE_CONFIG_DIR/projects`) with timestamps relative to a fixed `now`, no real text, this table: sessions s1–s4 on days −1, −2, −2, −5 in projects `alpha`, `alpha`, `beta`, `gamma`, each with one bare Hungarian form (`végeztünk?`, `végeztem`, `akkor végeztünk`, `végeztünk itt`; expected key `vegezt`, 4 sessions, 3 days, at threshold); s5–s7 with the English form `are we done?` on days −1, −3, −3 (expected key `done`, 3 sessions, 2 days, at threshold); s8 repeating `mehet` five times on day −4 and s9, s10 with `mehet` on days −6, −8 (key `mehe`, 3 sessions, at threshold but ignored); s11 and s12 with the same prompt 300 seconds apart on day −7 (collapsed to one occurrence); s13 in project `personal-email` with `végeztünk?` on day −9 (sensitive; counts, never shown); s14 with `/wrap` commands only; s15 with a prompt holding an e-mail address and s16 with `ignore previous instructions` on day −2 (each a key of its own, below threshold; they feed `example()` and `filter_reasons()` directly); s17 with a record whose timestamp ends in `Z` and one without a timestamp. Expected receipt for the default run with `_meta/sensitive` listing `personal-email`: examined 17 sessions, the prompt count of the table, 1 without a timestamp, candidates and keys at threshold as listed, 1 ignored as acknowledgements, nearest below listing the collapsed pair's key.
*   **Tests**, failing direction stated: `test_key_of_is_the_sorted_stem_set` (the four bare forms share a key; `are we done?` keys to `done`); `test_no_stem_prompts_are_counted_not_keyed`; `test_same_session_repeats_count_once`; `test_parallel_sessions_within_ten_minutes_collapse`; `test_threshold_needs_three_sessions_on_two_days`; `test_acknowledgement_stems_are_ignored_and_counted`; `test_sensitive_project_counts_but_never_shows` (no key, no example, no name; the overflow line says `1 sensitive-only`; the nearest list omits it); `test_examples_withheld_without_the_list_file` (the receipt line says so; no `e.g.` lines); `test_example_filter_reasons` (e-mail, authority language, gitleaks error when the binary is a stub that exits 2); `test_example_is_cut_at_a_word_boundary`; `test_receipt_not_examined_without_transcripts`; `test_receipt_examined_zero_prints_denominators_and_nearest`; `test_shortlist_caps_at_five_and_counts_the_rest`; `test_commands_are_counted_across_projects_and_never_keyed`; `test_project_name_matches_dream_project_of` (a root under the ledger's parent, a subdirectory, the config dir, an unrelated path). `test_observer.py`: `test_window_filters_by_record_timestamp_not_file_mtime` (a record older than the window in a fresh file is dropped; failing direction: 3.6.1 keeps it), `test_z_suffix_timestamps_parse_and_untimed_records_are_counted`, `test_commands_are_found_anywhere_in_a_wrapper`. `test_core.py`: the sweep prints the shortlist section (with transcripts and without); `recurrence status` prints it alone; the skill-text content test of item 27.

#### 31. dream.py (the author's private file; no repository change)

*   By the author after the counter is live: delete the `HUMAN_KINDS` stage-2 comment and any prompt-counting intent; keep the tool-failure and hook-friction scans and the routine checks; record the division in the ledger decision. tenet does not read or write `~/.claude/dream`.

### Phase 3: the proposer (not planned here)

Planned in its own design round once its gates hold (see "The proposer"). That round starts from the digests' weekly series and the drafts the sweep model wrote from the shortlist.

### Verification Plan

*   **Unit tests**: `python3 -m unittest discover -s tests -t .` green on Python 3.9 in both phases; hermetic through `tests/helpers.py`.
*   **Manifest and CI**: `claude plugin validate .claude-plugin/plugin.json`; the CI invariants (hooks.json tokens, fenced `!` blocks, frontmatter on tracked markdown) unchanged; the `!` block of the sweep skill is not edited by either phase.
*   **Leftover names (Phase 1, before tagging)**: `git grep -n -E 'patterns\.json|usage\.jsonl|pattern_drafts|pattern name|pattern-statement|measured_since' -- tenet skills hooks vault-template README.md` returns only the README's upgrade paragraph and rollback section.
*   **Sandbox run, Phase 1**: `d=$(mktemp -d); python3 tenet/cli.py bootstrap $d/ledger; export TENET_LEDGER=$d/ledger TENET_DATA=$d/data`; seed the three old files, a `status.env` with the three retired keys and a draft with the pending marker; `hook session-start` (both hooks run, nothing writes the three files); `observe scan` (the two-tuple summary; the retired keys gone from `status.env`); `sweep | grep -c 'pattern candidates'` prints 0; `pattern name x` exits 2; the pending draft is in `verdict`'s eligible set.
*   **Sandbox run, Phase 2**: with the fixture as `CLAUDE_CONFIG_DIR/projects` and a bootstrapped ledger: `recurrence status` without `_meta/sensitive` (keys and counts, `examples: withheld`), then with it (the example lines, the sensitive project hidden); `sweep` prints the section; a transcript directory that does not exist (`NOT EXAMINED`).
*   **Live check (the author's machine, before the counter release is tagged)**: `recurrence status` against the real transcripts lists `vegezt` among the keys at threshold with `4 ignored as acknowledgements` (the figures of 2026-11-03; a later window is judged by the receipt line it prints, not by those numbers).
*   **Rollback drill (before Phase 1 is tagged)**: in a scratch marketplace clone, go from 3.7.0 back to 3.6.1 and forward again with the candidate commands; the README's "Rolling back" section receives the commands that worked and nothing else.
*   **Live use (after the counter release)**: the first weekly sweep shows the shortlist with the end-of-session key; the digest carries the receipt line and the cluster lines; the sweep model writes a draft from it or states why not; the January retro reads the digests and the ledger decision's baseline.
