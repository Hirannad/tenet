---
title: Recurrence counting for the tenet observer, and the cut of its measuring half
type: spec
status: draft
updated: 2026-11-03
---

# Recurrence counting for the tenet observer, and the cut of its measuring half

*   **Author:** József Juhász (drafted with EGM; the Elephant wrote, the author decides)
*   **Status:** Proposed (awaiting egm-review)
*   **Date:** 2026-11-03

--------------------------------------------------------------------------------

## Overview

tenet is a Claude Code plugin: a decision ledger of markdown notes, a session-start hook that prints a per-project brief of the notes that matter there, a Stop hook that asks the author for verdicts on waiting drafts when a session is at rest, a weekly sweep skill and an audit skill. Its observer is a detached scan over the last 30 days of session transcripts that computes the brief. The observer also has a measuring half: a usage log that records which notes the assistant cited, and a pattern pipeline that groups ledger notes by text similarity and drafts a `pattern` note from one verbatim user sentence. That half is the subject of this design.

The design replaces the measuring half with one mechanism: a **recurrence counter over the author's own prompts**. When the same correction, expectation, question or way of deciding has recurred across enough sessions and days, the counter produces a shortlist; the weekly sweep's model phrases one proposal from it (the rule in one sentence, a proposed form, the evidence) and writes it as an ordinary inbox draft; the existing resting-point verdict round shows it to the author as a fixed, validated card; the author accepts, corrects, defers or rejects it in one move; the counter keeps watching the settled cluster so a rule that did not hold is reported, not forgotten. The old measuring half is removed in one release with an archive of its state, a rollback runbook and an off switch, and the counter is added afterwards as one module. The author's private `~/.claude/dream/dream.py`, which already reads prompts and gates what it emits, is the source of the reader and the gate; it is narrowed to what tenet does not take over.

## The Problem

The ledger decision of 2026-09-27 ("acceptance is not an end state") set two jobs for the measuring half: archive a note that goes unused for 90 days, and propose a rule from a note that surfaces three times in 60 days. The plugin's issue #2 set the rule for patterns: the machine must never author one; it may only make the question arrive at a better moment or build the note from the author's own sentence. What shipped between 3.1.0 and 3.6.1 does neither job:

*   `tenet/observer/usage.py` records note-slug citations in the assistant's text (225 rows; 35 percent are draft `related` links written at note creation, 27 percent are same-day self-citations). Nothing reads the log. The 90-day archive and the rule-graduation consumer were never built.
*   `tenet/patterns.py` and `tenet/observer/pattern_drafts.py` group accepted notes by TF-IDF cosine (threshold 0.08) plus `related` links, then search for one verbatim user sentence; since 3.6.0 the session's model phrases the rule at a separate Stop. Result: three drafts ever (all 2026-10-13), all rewritten by hand; two "J-class" entries in the ledger's process log for machine drafts with empty sections, wrong dates and foreign links; and, since 2026-10-13, a graph collapsed into one component of 99 of 115 accepted decisions that the size cap drops, so the weekly sweep prints "A real zero" for a saturated detector. The naming Stop never fired (0 markers in 42 rounds).

Neither measures what the author wants noticed. In his words: patterns were supposed to be born from recurrence in what he does and decides; the standing example is that at the end of most sessions he asks whether every decision is enforced, whether an open point is left, whether the work is really finished end to end. That recurrence never surfaced; he hand-built two private skills from it (`/wrap`, `/verdicts`), and what he must trigger by hand often does not happen, or happens out of frustration. His success signal is not a count: anything that happened more than two or three times (an error, a misunderstanding, a new expectation) is not typed a fourth time.

Two more facts shape the design. First, the counter already exists in part: `~/.claude/dream/dream.py` is a weekly, deterministic recurrence counter over the same transcripts (three-session minimum, evidence ids, "covered by" hints from the ledger, backpressure, an emit gate with gitleaks, PII and sensitive-project checks) that reads the author's prompts with per-record timestamps and never counts them; the 2026-09-27 decision said it would become part of tenet, and it did not. tenet meanwhile grew a second transcript reader with different rules (file mtime for dates, no sensitive-project exclusion). Second, the delivery machinery cannot carry a recurrence brief as built: the verdict card shows the first two sections of a draft cut at 1200 characters, repeated as the preview of every option; the gate is claimed per session rather than per draft; "Accept" only flips a note's status, which means nothing for a hook, a skill or a CLAUDE.md line.

## Goals

*   **G1. Count recurrence of the author's prompts, not note similarity.** A cluster is reportable when it has at least three occurrences in at least three distinct sessions on at least two distinct days inside the 30-day window; occurrences in parallel sessions within ten minutes collapse to one; repeats inside one session count once. Dates come from per-record timestamps, never from file modification time. Slash-command invocations (`/wrap`, `/verdicts`, `/tenet:*`) are counted as a separate labelled stream and never clustered with prose.
*   **G2. Find the known cases before the first proposal.** A replay fixture built from material that exists today (the end-of-session completeness question in its one-to-three-word and paraphrased forms; the two J-class repeats and the B, C and H sets in `_meta/retro.md`) runs as an in-process test and reports recall as a number. The end-of-session question is the acceptance test of the feature: the detector must find it from the author's real prompts.
*   **G3. One validated card per round, through the resting-point verdict round.** The card is at most 900 bytes and carries: a headline (count, span, projects), one line per occurrence (date · project · verbatim quote cut at a word boundary, or the normalised phrase for sensitive projects), the rule in one sentence, the proposed form with a one-clause reason and its standing cost, and a "covered by / previously tried" line. A validator fails closed before anything is shown. Budgets: at most one proposal per week at launch, one card per round, one round per session, backpressure while one proposal is unreviewed, back-off after two consecutive discards, a first-run cap. Session start carries at most a pointer line, never on resume, compact or clear.
*   **G4. Phrasing in the weekly sweep session.** The counter's shortlist is a section of the sweep inventory; the sweep model phrases the rule and the form and writes one draft through check 8's single draft slot; the draft rides the existing gate. No new Stop-hook model turn. The resting-point variant stays the documented upgrade path if the event table shows the fourth typing keeps arriving before the proposal.
*   **G5. Accept means one thing.** Accept records the verdict and the proposed form as text; carrying the form out (writing a hook, editing CLAUDE.md, making a skill) is an ordinary session task done with the author present, prompted by the apply output; it is never a code path in tenet. Two proposal kinds with different allowed forms: a repeated break of an existing rule may only propose a failing mechanism or deletion of the rule; a new expectation may propose a note, a rule line, a skill or the rest. A free-text correction completes the decision in the same dialog, and the card loops at most once. Option set: accept as the proposed form; not a pattern (sticky suppression under a stable key); later (one deferral, never a silent expiry); other.
*   **G6. No silent zero, and a trail the January retro can read.** Every scan writes a receipt and prints one of four states (not examined with reason; examined-zero with denominators and near misses; found-but-suppressed with reasons; proposed). The counter keeps an append-only, schema-versioned occurrence and scan ledger in the plugin data directory, loud on an unreadable or newer-schema file, with a 180-day horizon and a size cap. Every gate evaluation that had something to deliver logs one row (outcome or the busy reason). Settling a cluster changes its label, not the counting: post-settle recurrences per accepted proposal are the primary metric, target zero; a discarded cluster that keeps recurring is shown as such. The scan runs its phases in isolation with per-phase timing; a banner fires when a phase exceeds its budget or a proposal has waited more than 14 days unseen.
*   **G7. A privacy gate before any prompt text leaves the transcript.** The sensitive-project list and the gitleaks, PII and authority-language checks are ported from dream.py; from a sensitive project the card and the occurrence ledger hold the normalised phrase, counts and dates and never a quote. The README privacy section is rewritten to match.
*   **G8. The cut is one release.** `patterns.py`, `pattern_drafts.py`, `usage.py`, the `pattern name` subcommand, the Stop-hook naming branch and `.pattern` marker, the sweep's pattern section and the `new_uses` and `pattern_*` status keys, their tests, and every sentence about them in skills, references, conventions and README go in one release, with a grep test that fails on any leftover name; `verdicts.jsonl` stays; `usage.jsonl`, `patterns.json` and `state.json` are archived under the plugin data directory before deletion; the vault template ignores `_meta/observer/`; check numbering stays stable with a one-line tombstone for check 6; a pre-release check refuses to ship while an inbox draft carries the pending-pattern marker; the release ships a five-line rollback runbook and one off switch; a draft decision superseding 2026-09-27 is written to the inbox for the author's verdict and is never edited in place by the release.
*   **G9. One transcript reader.** dream.py's prompt reader and emit gate are ported into tenet; dream.py keeps only what tenet does not take over, or goes after parity, by the author's hand.
*   **G10. A pre-registered kill test.** The ledger decision that supersedes 2026-09-27 carries the event table format (one line per proposal: cluster, occurrences, first seen, proposed, form proposed and chosen, verdict, days to verdict, post-settle recurrences), today's baseline (clusters at threshold in the current window) and the delete condition: no accepted proposal after eight weeks, or any accepted key still recurring without a mechanism.

## Non-Goals

*   The 90-day archive or any auto-archiving of notes; it is judged at the January retro.
*   A code detector for rationale overlap among accepted notes. The similarity graph is deleted; the sweep's check 6 is relaxed in text so the sweep model may draft the one-sentence rule itself. If a note detector is ever wanted, it is exact (the same structured key cited by three or more notes), never a similarity graph.
*   Accept executing a hook, a skill, a loop or a CLAUDE.md edit by itself.
*   Delivering proposals through the author's private `open:` queue as the only copy, or adding an `open:` reader to the plugin.
*   Counting assistant-text citations as "use", or keeping the semantics of `usage.jsonl`.
*   A monthly retro routine, a tokenizer, a stats subcommand, or changes to the brief's scoring (those are separate retro decisions: the Core section only in global and no-match briefs; leads cut at word boundaries).
*   Replacing `/wrap` or `/verdicts`; their overlap with the gate is reported by the covered-by line, not resolved here.

## Open Questions

*   **Q1. Ledger remote visibility.** The author is to confirm in writing that the ledger's git remote is private. If it is public, no quote is ever stored or shown, from any project.
*   **Q3. What remains of dream.py.** Its tool-failure and hook-friction scans and its scheduled trigger are the author's private machinery; this design only states what tenet ports and that one reader remains. Whether the rest stays or goes is the author's call at cut time.
*   **Q4. The standing-cost table.** The card states the cost of the proposed form (tokens per session for a CLAUDE.md line or a skill description; milliseconds per event for a hook; tokens per firing for a loop or agent). The values are measured during implementation and written into the validator's table.

Resolved during drafting (2026-11-03, by the author): the counter pass is triggered at session start, at most once a day, detached and incremental (former Q2); one proposal threshold for every form, with the standing cost shown on the card (former Q5); proposals have no Later option; an accepted proposal of any form is promoted to the ledger root as the record of the decision; `verdicts.jsonl` rows gain `form` and `key` for proposals.

## Critical User Journeys (CUJs)

### CUJ 1: The end-of-session question becomes a proposal

*   **Given**: Thirty days of transcripts in which the author typed a variant of "végeztünk? / minden ki van kényszerítve? / maradt nyitott pont?" in at least three sessions on at least two days; the counter is on; no proposal is pending.
*   **When**: The daily counter pass runs; the weekly sweep runs; the author later reaches a resting point in any session.
*   **Then**: The scan receipt lists the cluster with its denominators (sessions read, prompts read, clusters at threshold). The sweep inventory shows the shortlist with occurrences. The sweep model writes one inbox draft through check 8's slot with every card field filled, including the covered-by line ("wrap: handoff and open items yes; enforcement check no; a Stop-hook guard for this was reversed 2026-10-09") and the proposal kind ("new expectation"). The validator passes it. At the resting point the verdict round shows the card as one of its at most four questions. The author answers accept-as-form, not-a-pattern, later, or other with free text. `verdict apply` records the verdict and the form in `verdicts.jsonl` and prints the carry-out instruction for the session model when the form needs one. The counter marks the cluster settled and keeps counting post-settle occurrences.

### CUJ 2: Nothing recurs

*   **Given**: A quiet month, or a month whose repeats are all below threshold.
*   **When**: The counter pass runs.
*   **Then**: The receipt reads "examined: N sessions, M prompts, K clusters below threshold (nearest: … at 2 sessions)", never "a real zero"; the sweep digest carries that line; no draft is written; `observe status` shows the last counter pass and its denominators.

### CUJ 3: An accepted proposal does not hold

*   **Given**: Cluster X was accepted on date D as form F.
*   **When**: At least two matching prompts occur after D.
*   **Then**: A "did not hold" card is proposed instead of a fresh one: "accepted on D as F, recurred N times since", with the options "the form failed: escalate" and "delete the rule"; the event table shows the post-settle recurrences for X.

### CUJ 4: A sensitive project

*   **Given**: Prompts from a project on the sensitive list (ported from dream.py: personal mail, family finance, banking).
*   **When**: A cluster forms from them.
*   **Then**: The card and the occurrence ledger carry the normalised phrase, the counts and the dates and no quote; the gitleaks and PII checks run on every quote from any project before it is written anywhere.

### CUJ 5: The cut release on the author's machine

*   **Given**: tenet 3.6.1 installed; the live ledger holds `_meta/observer/{usage.jsonl, patterns.json, state.json, verdicts.jsonl}`; the inbox holds no pending pattern draft.
*   **When**: 3.7.0 installs and the next session starts.
*   **Then**: Both hooks run and the brief prints; the sweep's check 6 line prints its tombstone once a week for a stated number of weeks; the three old state files are archived under the plugin data directory and gone from the ledger; the runbook tells the author to `git rm --cached` `state.json`; a draft decision superseding 2026-09-27 waits in the inbox for his verdict; the rollback runbook names the exact command to return to tag `tenet--v3.6.1`; the off switch is documented.

### CUJ 6: The January retro

*   **Given**: Eight or more weeks of the counter in use.
*   **When**: The retro reads the event table and the baseline row.
*   **Then**: It sees one line per proposal with its post-settle recurrences, compares against the baseline, and evaluates the pre-registered delete condition; it does not read rates off a handful of events.

## Technical Plan (Architecture)

### Shape of the change

Two releases. The first (the cut, 3.7.0) removes the old measuring half and leaves the observer with the brief only, plus an archive of the old state, a rollback runbook and an off switch. The second (the counter, 3.8.0) adds one module, `tenet/observer/recurrence.py`, with three touch points in existing code: one phase call in the scan, one inventory section in the sweep, and one validator subcommand that writes the proposal draft. Everything downstream of the draft (the resting-point gate, `verdict apply`, promotion, `verdicts.jsonl`) is reused, with the gate fixes the retrospective already scheduled (per-draft claim, preview on the first option only, a Stop path that does not re-parse the transcript).

Three architecture choices were put to the author and decided: the Tier 1 detector uses exact keys first (a pair index is the documented second step if the replay fixture misses the paraphrase family); the counter pass is triggered at session start, at most once per 24 hours, detached and incremental; the proposal travels as an inbox draft whose first two sections are the card.

### Data flow

```text
 ~/.claude/projects/*/*.jsonl (30 days)
        │  transcripts.read(): human prompts with record timestamps, session, project;
        │  slash commands as a separate list (name only); WRAPPERS and isMeta dropped
        ▼
 recurrence.pass_()  (observer scan, phase 2, daily, incremental over changed files)
        │  normalise → key (short prompt: folded text; long prompt: sorted stem set)
        │  one occurrence per (key, session); parallel-session repeats within 10 min collapse
        │  privacy gate: sensitive project ⇒ no quote stored
        ├──► <data>/recurrence/occurrences.jsonl   (append-only, 180 days, schema 1)
        ├──► <data>/recurrence/receipts.jsonl      (one row per pass: state + denominators)
        └──► <data>/recurrence/clusters.json       (key → sessions, days, projects, status)
                     │  clusters at threshold (≥3 sessions, ≥2 days), covered_by, previously_tried
                     ▼
 cli.py sweep  →  "--- recurrence shortlist ---" section + receipt line   (weekly routine)
        │  the sweep model phrases ONE proposal (rule, form, kind, cost) per run (check 8 slot)
        ▼
 cli.py recurrence propose <key>  (validator; JSON on stdin)  ──►  inbox/<date>-<slug>.md
        │  sections 1–2 are the card (≤900 bytes); refuses incomplete, oversize, unverifiable
        ▼
 Stop hook gate at a resting point (per-draft claim)  ──►  AskUserQuestion (card = preview of option 1)
        │  accept as <form> / not a pattern (sticky) / other (free text = accept with change)
        ▼
 cli.py verdict apply  ──►  status + form in verdicts.jsonl; recurrence.settle(key)
        │  carry-out instruction printed when the form is not a note
        ▼
 post-settle counting (same pass)  ──►  "did not hold" card  /  event table  ──►  January retro
```

### Components

**`tenet/observer/transcripts.py` (modified).** `read()` returns prompts as records, not strings: `{text, ts, session, project}` with `ts` from the record's own timestamp (ported from dream.py's `read_session`: `in_window` by record time, `origin.kind == human`, not `isMeta`, not a wrapper). A second list, `commands`, holds the names of typed slash commands (`/wrap`, `/verdicts`, `/tenet:tenet-capture`) that the wrapper filter drops today; the command body is never kept. The `assistant` text list goes away with `usage.py`; `asked` and `paths` stay for the brief. The 30-day window stays file-based for selection and record-based for dating, so a long-lived session no longer contributes months-old prompts as new.

**`tenet/observer/recurrence.py` (new; the one new module).**

*   `key_of(text)`: fold accents, lower-case, strip punctuation and digits, collapse whitespace. A short prompt (at most five content stems after `textindex.tokens`) is keyed by its folded text; a longer prompt by the sorted set of its content stems. One function, zero tunable constants. The documented second step, if the replay fixture reports recall below target on the paraphrase family, is a stem-pair index with a document-frequency ceiling; it is not built now.
*   `occurrences(prompts)`: one occurrence per `(key, session)`; occurrences with the same key in different sessions within ten minutes collapse to one; each occurrence keeps `ts`, `project`, and the quote (cut at a word boundary at 160 characters) unless the project is sensitive, in which case `text` is null.
*   `clusters(occurrences, window)`: a cluster is a key with at least three occurrences in at least three distinct sessions on at least two distinct days inside the window. Status per key: `open`, `proposed`, `accepted`, `discarded` (sticky), `did_not_hold`. Settling never stops counting; `post_settle` lists occurrences after the verdict date.
*   `covered_by(key)`: ledger slugs (all statuses, including reversed and superseded) whose title or `## Miért` share the cluster's content stems, plus installed skill and hook names that match a content stem; a reversed decision on the same subject suppresses the proposal unless the card states new evidence. Ported from dream.py's `covered_by` with the status lookup added.
*   `pass_(data, sessions)`: incremental: reads only transcripts whose `(size, mtime)` differ from the last receipt's file table; writes occurrences, recomputes clusters, writes one receipt row. Idempotent and safe to re-run.
*   `receipt()`: the four states, printed by the sweep and by `cli.py recurrence status`: `NOT EXAMINED (reason)`, `EXAMINED: S sessions, P prompts, C commands, K keys, 0 clusters at threshold; nearest: key (n sessions)`, `FOUND, SUPPRESSED: K clusters, reasons: covered_by …, pending proposal …, sticky discard …`, `PROPOSED: key`.
*   `propose(key, fields)`: the validator behind `cli.py recurrence propose`. Input (JSON on stdin from the sweep model): `rule` (one sentence, at most 30 words), `form` (one of: note, claude-md-line, hook, loop, skill, agent, harness-setting, mechanism, delete-rule), `kind` (`new-expectation` or `repeated-break`), `reason` (one clause), `standing_cost` (one line, unit stated). The command assembles the card from the cluster's own evidence (it never trusts the model for dates, counts or quotes), checks every quote is a verbatim substring of the stored occurrence, enforces the form rule per kind (a repeated break may only propose `mechanism` or `delete-rule`), runs the privacy gate on the card text, refuses a card over 900 bytes, writes `inbox/<date>-<slug>.md` with `type: proposal`, `status: proposed`, `recurrence_key`, `form`, `kind` in the frontmatter, and marks the cluster `proposed`. It refuses when a proposal is already pending (backpressure), when the weekly budget is spent, or when the key is sticky-discarded. Every refusal is printed with its reason and counted in the receipt.
*   `settle(key, verdict, form, date)`: called by `verdict apply` for every verdict on a proposal draft; records the verdict and the form on the cluster; a discard is sticky under the key.
*   Privacy gate (in the same module): the sensitive-project prefix list (ported from dream.py: personal mail, family finance, the two named repos; configurable through `TENET_SENSITIVE`, a comma-separated list), the PII patterns and the authority-language pattern (ported), a six-word-shingle leak check against sensitive text, and gitleaks when the binary is present. When gitleaks is absent, no quote is written anywhere (counts, dates and the normalised phrase only), and the receipt says so; the scan never fails for a missing binary.

**`tenet/observer/run.py` (modified).** The scan runs in isolated phases, each with its own try block and status fields: `brief` first (it is the credited value), then `recurrence`; a failure in the second prints `TENET RECURRENCE FAILING: …` and leaves `last_ok` of the brief untouched. `due()` gains one condition: `counter stale` when the last recurrence receipt is older than 24 hours and the last attempt older than one hour (the scan then runs the brief only if it is due too). `status.env` gains `counter_last_ok`, `counter_error`, `counter_clusters`, `proposals_open`; per-phase wall time and bytes read are recorded in the receipt. `banners()` adds `TENET RECURRENCE FAILING` and `TENET PROPOSAL WAITING: <key> unseen for N days` (after 14 days). The one-try block and the single `error` field of today are the defect this fixes.

**`tenet/sweep.py` (modified).** A new inventory section `--- recurrence shortlist ---` prints the receipt line, then each cluster at threshold with its denominators, occurrences (date · project · quote or `[sensitive: phrase]`), `covered_by` and `previously_tried`, and the slash-command counts of the month; when nothing is at threshold it prints the nearest keys. The pattern-candidates section is replaced by a one-line tombstone for a stated number of weeks ("check 6: pattern candidates retired in 3.7.0; last run <date>; 3 drafts ever").

**`skills/tenet-sweep/SKILL.md` and `references/checks.md` (modified).** Check 8 becomes "recurrence and repeated deviations" with three inputs: the shortlist (new), `_meta/retro.md` and the feedback notes (as today). The rule stays two-outcome (a mechanism that fails, or deletion; never a restated rule) and is extended with the author's form list for a new expectation. The model may phrase the rule itself (the "I will phrase it myself" blocker is gone). At most one proposal per run, written only through `cli.py recurrence propose`; the model never writes a proposal draft by hand. The check list keeps its numbering; check 6 carries the tombstone.

**`tenet/verdict.py` (modified; the retrospective's gate fixes plus three proposal rules).** (1) `eligible()` admits `type: proposal` drafts with the card's own cap (900 bytes for sections 1–2) instead of the 60/400 word caps. (2) `_card` shows sections 1–2 (the card by construction) and attaches the preview to the first option only. (3) The claim is per draft: a ticket names its drafts, and a draft named in another session's open ticket of the same day is excluded. (4) The Stop path is O(1) in transcript size: payload-only checks first, then a size threshold, then a tail read of the last 64 KB. (5) Options for a proposal: accept as `<form>`, not a pattern (sticky), other (free text; treated as accept-with-change: the model applies the change, re-runs `recurrence propose --revise`, and the verdict is recorded as `accepted-edited` in the same stop). (6) `apply` writes `form` into the `verdicts.jsonl` row, calls `recurrence.settle`, and prints a carry-out instruction when the form is not a note ("the author accepted <form>: <rule>; make the change in this session with the author present; changes outside the repository are a new question"). Accept of a `note` form promotes the draft as today. Later and To memory are gone (retrospective decision 2).

**`tenet/cli.py` (modified).** `recurrence pass|status|propose` subcommands; `pattern name` removed; `observe status` prints the counter keys. Every printed command carries `TENET_LEDGER` and `TENET_DATA` as today.

**Off switch.** `TENET_RECURRENCE=off` (environment; and a `recurrence` userConfig boolean mirroring it, since whether userConfig reaches hooks is unverified): the scan skips the pass and prints `recurrence: off` in the receipt line; the gate does not ask about proposal drafts; the sweep section says it is off.

**dream.py (the author's private file, narrowed by hand).** tenet ports `read_session`'s prompt extraction, the `SENSITIVE` list, `pii`, `AUTHORITY`, `gitleaks`, `leaks_sensitive`, `covered_by` and the backpressure rule. dream.py keeps its tool-failure and hook-friction scans and its routine checks; its `HUMAN_KINDS` stage 2 is closed as "built in tenet". The division is written into the ledger decision, not into tenet.

### The cut (3.7.0), what goes and what replaces it

Removed: `tenet/patterns.py`, `tenet/observer/pattern_drafts.py`, `tenet/observer/usage.py`, `cli.py pattern name`, `verdict._naming` and the `.pattern` session marker, the `PENDING` gate in `eligible()`, the sweep's pattern section (tombstone instead), the `new_uses`, `pattern_groups`, `pattern_drafts` status keys and the scan's 3-tuple, `tests/test_patterns.py` and the pattern and usage tests elsewhere, and every sentence about them in `README.md`, `CHANGELOG.md` (one new line), `skills/tenet-sweep/SKILL.md`, `references/checks.md`, `skills/tenet-capture/SKILL.md` (the pending-skip line), `references/conventions.md` (the Pattern template claim), and the Pattern template's positional dependence. Kept untouched: `verdicts.jsonl`. Archived before deletion under `<data>/archive/observer-3.6.1/`: `usage.jsonl`, `patterns.json`, `state.json`; the runbook then has the author `git rm --cached _meta/observer/state.json` in the ledger. Added: `_meta/observer/` to `vault-template/.gitignore`; a pre-release check (a test over the author's ledger path when `TENET_LEDGER` points at it, and a session-start notice) that refuses to ship while an inbox draft carries the pending-pattern marker; a grep test that fails on any leftover name of the removed pieces; a tombstone line in the sweep for four weeks. The 3.7.0 release is paired with a ledger act: a draft decision superseding 2026-09-27 (recurrence counting replaces use counting; the archive deferred to the January retro with a revisit date; the kill test and the event-table format written into it) is placed in `inbox/` for the author's verdict and is never edited in place by the release.

### Rollback runbook (shipped in README, five lines)

1. Return to the previous version: reinstall from the `tenet--v3.6.1` tag (the exact plugin-manager syntax is verified and written during implementation; the fallback is a checkout of that tag in the marketplace clone followed by `claude plugin update tenet@tenet`).
2. Restore `patterns.json` from `<data>/archive/observer-3.6.1/` if the old pipeline is wanted back; `usage.jsonl` and `state.json` are optional, 3.6.1 rebuilds them.
3. The counter's files under `<data>/recurrence/` are ignored by 3.6.1; delete them if unwanted.
4. Proposal drafts in `inbox/` (type `proposal`) are ignored by 3.6.1's gate (unknown type is not eligible); move them to `<data>/verdict/removed/` or delete them.
5. The ledger decision stays whatever the author decided; rolling back code does not roll back a verdict.

## Non-Functional Requirements

*   **Security and privacy.** Prompt text leaves a transcript only as an occurrence quote of at most 160 characters, only from non-sensitive projects, only after the PII and authority checks, and only into the plugin data directory (never into the git-tracked ledger) until a proposal is written; a proposal quote reaches `inbox/` only through the validator, which repeats the checks on the whole card and runs gitleaks when present; without gitleaks no quote is written at all. The occurrence ledger is reversible-free for sensitive projects (phrase keys only). The README's privacy section names all of this. The author confirms the ledger remote is private (Open Question 1); if it is not, quotes are disabled globally by default.
*   **Performance.** Hooks stay under 100 ms: the session-start hook only reads status and prints; the Stop hook is O(1) in transcript size after the gate fix. The counter pass is incremental: budget +0.5 s over changed files, +1 s worst case for a full pass, measured and written into the receipt; no growth in peak memory beyond today's scan (about 115 MB), because the pass streams prompts and keeps keys, not texts. State: at most about 2 MB across the three files with a 180-day horizon; the oldest rows are dropped with a receipt note, never silently.
*   **Rollout and rollback.** Two releases, each a version bump with one CHANGELOG line. 3.7.0 (the cut) ships with the archive, the pending-draft check, the runbook, the off switch, and the ledger draft. 3.8.0 (the counter) ships only after the replay fixture reports recall on the known cases and with the first-run cap (no proposal in the first pass; the first proposal only from the second weekly sweep); the weekly budget and backpressure are constants in one block with the measurement that set them. Rollback is the runbook above; nothing in 3.8.0 changes a file 3.6.1 reads.
*   **Observability.** Every pass writes a receipt; every gate evaluation with something to deliver writes a row; `cli.py recurrence status` prints the last receipt, the open proposals and the event table; banners cover a failing counter and a proposal unseen for 14 days. The January retro reads the event table and today's baseline row, both produced by the same module.

## Alternatives Considered

### Alternative A: Keep the current pipeline and fix it

*   **Pros**: No cut; the existing tests and skill text stay; printing the dropped component sizes and lowering the cosine threshold are small edits; the usage log could feed the 90-day archive if its consumer were built.
*   **Cons**: It measures note-to-note topic proximity and assistant-text citations, not the author repeating himself; three drafts ever, none accepted as drafted, two J-class process-log entries from this path; two tuned constants (threshold, size cap) in front of a silent zero; the archive needs a 60-day history that only exists if the biased log is kept.
*   **Reason for Rejection**: The author's intent is recurrence in his own words; no parameter change turns a note-similarity graph into that. The ledger's own rule (a layer that fails its revisit clause goes, it does not get more prose) applies.

### Alternative B: Rewrite the counter in place of the pattern modules

*   **Pros**: Fewer files to add; the `pattern name` validator, the pending marker and the sweep hook-in could be reused for proposals.
*   **Cons**: The pattern machinery is wired into five modules, two session markers, status keys, tests and three skill texts; an in-place rewrite inherits the PENDING gate, the naming Stop and the status keys, so the new counter becomes as hard to delete as the old one; a partial deletion kills both hooks because `cli.py` imports the modules at the top level.
*   **Reason for Rejection**: Deletion in one release followed by one new module with three touch points keeps the counter deletable; a rewrite would not.

### Alternative C: Build the prompt counter in dream.py and let tenet only deliver

*   **Pros**: dream.py already has the prompt reader, the three-session rule, the evidence ids, the emit gate and backpressure; "stage 2" is a small addition there.
*   **Cons**: Two transcript readers with two rule sets (record timestamps versus file mtime, sensitive exclusion versus none) stay; a published plugin cannot depend on a private script under `~/.claude/dream`; dream's weekly trigger is unverified and may be manual, the very flaw the author named.
*   **Reason for Rejection**: The author chose a publication-ready tenet; one reader must remain, and it must be the plugin's.

### Alternative D: Sentence shingles with per-session dedupe as the detector

*   **Pros**: Cheap, deterministic, no model.
*   **Cons**: The "are we done?" family is one to three words, below any shingle floor; the long forms are paraphrases that share no trigram; the retro log's B-class pair is a paraphrase; raw counts are dominated by acknowledgements ("kész").
*   **Reason for Rejection**: It would return clean-looking zeros for exactly the recurrences the feature exists to find.

### Alternative E: A stem-pair inverted index now (gate 1, option 2)

*   **Pros**: Higher recall on paraphrases that share two anchor stems (open point + enforced); no chaining into components, so no saturation.
*   **Cons**: Two constants (document-frequency ceiling, pair support) that need measurement comments; a prompt can land in several candidates; six-character stems do not unify inflected Hungarian forms.
*   **Reason for Rejection**: Not rejected, deferred: exact keys first, and the pair index is the documented second step if the replay fixture reports recall below target on the paraphrase family.

### Alternative F: Let the sweep model cluster the raw prompts from the dump (gate 1, option 3)

*   **Pros**: No detector code; judgement handles paraphrases.
*   **Cons**: About a thousand prompts a month into a dump that already spills past the inline limit; recall is unmeasurable and non-deterministic (the sweep already skipped the rubric scoring it was told to do); prompts from sensitive projects would sit in the dump.
*   **Reason for Rejection**: Breaks "work from the dump" determinism and the privacy gate.

### Alternative G: Run the counter only inside the weekly sweep (gate 2, option 2)

*   **Pros**: Least code; no daily pass, no incremental state.
*   **Cons**: Adds 4.5–6 s to the sweep dump; latency is always a week; when the routine dies silently (four Mondays in the record) the counter stops with it.
*   **Reason for Rejection**: The author wants a more autonomous direction; a daily detached pass at session start costs nothing new in surface and the receipt shows when it last ran.

### Alternative H: A dedicated scheduled routine as the trigger (gate 2, option 3)

*   **Pros**: Independent of the author's sessions.
*   **Cons**: New surface (a routine, its receipt, its supervision) in the layer the author is reviewing; a published plugin cannot install a routine for its user.
*   **Reason for Rejection**: Surface growth without a benefit the session-start trigger lacks.

### Alternative I: A separate proposal store in the plugin data directory (gate 3, option 2)

*   **Pros**: The ledger root never receives a "proposal" note; the sweep model writes plugin state, not the ledger.
*   **Cons**: Two stores, two selection paths in the gate, two apply paths, two logs; the sweep model writing a plugin state file instead of a draft breaks the one rule the sweep has (it writes the digest and one draft).
*   **Reason for Rejection**: One container (an inbox draft whose first two sections are the card) reuses the gate, the ticket, the sha1 guard and `verdicts.jsonl` unchanged.

### Alternative J: Deliver through the digest's `open:` items (gate 3, option 3; the brief)

*   **Pros**: The weekly path exists and its items are the best-answered output measured (4 of 5).
*   **Cons**: The only reader is the author's private script; an item is one line with two to four options and cannot carry quotes and dates; the queue grew from 10 to 21 in a week and a ledger decision reverses itself on two weeks of growth.
*   **Reason for Rejection**: Not a channel the plugin owns, and not one that can carry the card. A pointer line in the digest is allowed; the draft is the copy of record.

### Alternative K: Deliver at session start

*   **Pros**: Autonomous and cheap to print.
*   **Cons**: Session start is context for the model, not a question to the author; the sweep nag appeared in 50 sessions and started a sweep in 3; the block is re-injected on resume and compact.
*   **Reason for Rejection**: It does not reach the author; at most a pointer line.

### Alternative L: Accept executes the form

*   **Pros**: One click from recurrence to mechanism.
*   **Cons**: A harness-level change (a hook, a CLAUDE.md edit) applied by a verdict click outside the plugin's write scope; a per-form state machine in `verdict.apply` that tracks platform features.
*   **Reason for Rejection**: Accept records the verdict and the form; the carry-out is a session task with the author present.

### Alternative M: Phrase the rule at the resting point through a validating command

*   **Pros**: Immediate: the proposal is phrased in the same stop that asks; no weekly latency.
*   **Cons**: A second model turn at every qualifying stop, a new Stop-side validator, and the naming-round shape that never fired in 42 rounds.
*   **Reason for Rejection**: Deferred, not rejected: the weekly sweep phrases first; this is the upgrade if the event table shows the fourth typing keeps arriving before the proposal.

### Alternative N: Keep the note source in the first build

*   **Pros**: The author said note redundancy can signal a pattern too.
*   **Cons**: The weekly sweep model already finds the triples by reading the ledger; the only broken part is the similarity graph that prints a false zero; a code detector for notes would be a graph again or an exact-key check nobody has asked for.
*   **Reason for Rejection**: The graph is deleted, check 6 is relaxed so the model may draft the rule itself, and a note detector waits for a case the sweep cannot handle by reading.

### Alternative O: "Remove it at the January retro if it is not useful"

*   **Pros**: Light.
*   **Cons**: It repeats the 2026-09-27 pattern: an open-ended revisit that nothing can evaluate; the retro would read rates off a handful of events.
*   **Reason for Rejection**: Replaced by the event table, today's baseline row and a pre-registered delete condition written into the ledger decision.

### Alternative P: A "later" option and a deferral store for proposals

*   **Pros**: Lets the author postpone without discarding.
*   **Cons**: The existing Later and deferrals were never used in 54 verdicts and are being removed (retrospective decision 2); backpressure and the weekly budget already pace proposals; a silent expiry is the failure the author fears.
*   **Reason for Rejection**: Proposals use the same three answers as every draft (accept as the form, not a pattern, other with free text); an unanswered proposal stays open and is shown again, with a banner after 14 days.

--------------------------------------------------------------------------------

### Additional Resources

*   The retrospective of 2026-11-02 (`scratchpad/retro/tenet-retrospektiva-2026-11-02.md`), its verified issues (`scratchpad/verified/all.json`, ids observer-17, observer-18, observer-04, observer-07, observer-16, observer-45, verdict-lifecycle-01, -14, -16, -21, value-measure-15, -16, -17) and its release plan (`scratchpad/gap/plan/release-plan.md`, batches B0, B1a–d, B2a).
*   The concepts brief (`scratchpad/egm/concepts_brief.md`) and the Goldfish brainstorm reviews (`scratchpad/egm/brainstorm_goldfish.json`).
*   Ledger decisions: `2026-09-27-elfogadas-nem-vegallapot`, `2026-08-09-mechanizmus-vagy-torles`, `2026-08-28-nem-duplikaljuk-a-platformot`, `2026-07-26-minimalis-felulet`, `2026-09-26-dream-wrap-stop-guard` (reversed 2026-10-09); the process log `_meta/retro.md`.
*   The author's private `~/.claude/dream/dream.py` (the source of the prompt reader, the sensitive list, the PII and authority patterns, the leak check, `covered_by` and backpressure).
*   tenet issue #2 (no `pattern` notes after a month of use).

### Future Improvements

*   **The stem-pair index** (Alternative E) when the replay fixture shows the paraphrase family is missed by exact keys.
*   **Phrasing at the resting point** (Alternative M) when the event table shows the fourth typing arrives before the weekly proposal.
*   **A note-side exact detector** (a `related` or `derived` target cited by three or more notes), only if the sweep model stops finding note overlap by reading.
*   **The 90-day archive**, re-decided at the January retro from the event table and the counter's zero end (keys that never recur).

--------------------------------------------------------------------------------

## Detailed Implementation Plan

Two phases, two releases, each one version bump and one CHANGELOG line. Phase 1 needs no decision beyond the ones taken here and ships first. Phase 2 depends on two retrospective gate fixes that ship in their own batches before it (the per-draft claim and the O(1) Stop path, batch B2a; the Discard copy-before-`git rm`, batch B0); the plan names them where it relies on them. Every constant lives in one block at the top of the module that uses it, with a one-line comment naming the measurement or decision it came from. No production code is written from this document; schemas and pseudocode below are the contract.

### Phase 1: the cut (3.7.0)

#### 1. `tenet/patterns.py` (Delete)

*   **Type / Scope**: Python module, the note-similarity grouping (TF-IDF cosine 0.08, size cap 8).
*   **Proposed Changes**: Deleted. Rationale: it detects topic proximity among notes, not recurrence; on the live ledger it collapses 99 of 115 accepted decisions into one dropped component and makes the sweep print a false zero. Its only callers are `tenet/sweep.py:75` and `tenet/observer/pattern_drafts.py`.

#### 2. `tenet/observer/pattern_drafts.py` (Delete)

*   **Type / Scope**: Python module, machine pattern drafting from a verbatim quote, the pending marker, the `name()` rename path.
*   **Proposed Changes**: Deleted. Rationale: three drafts ever, all rewritten by hand; two J-class process-log entries; the naming Stop never fired. Callers: `run.scan`, `verdict.eligible`, `verdict.gate`, `verdict._naming`, `cli.py pattern name`.

#### 3. `tenet/observer/usage.py` (Delete)

*   **Type / Scope**: Python module, the note-citation log and `measured_since`.
*   **Proposed Changes**: Deleted. Rationale: no reader outside tests; semantics (assistant-text citations, draft links) are not the recurrence signal; the read-error path erases up to 150 days of history behind a green message. The archive step (item 6) preserves the data.

#### 4. `tests/test_patterns.py` (Delete)

*   **Type / Scope**: Unit tests of the deleted grouping.
*   **Proposed Changes**: Deleted with its module.

#### 5. `tenet/cli.py` (Modify)

*   **Type / Scope**: The single entry point for hooks and skills.
*   **Proposed Changes**: Remove the `pattern_drafts` import (line 11) and the `pattern` subparser with its `name` handler (lines 126–129 and the handler near 162–165). `observe status` and the `observe scan` summary stop printing `new_uses`, `pattern_groups` and `pattern_drafts`. No new subcommand in this phase. Rationale: the modules are gone; the CLI must not import them (a top-level ImportError would kill both hooks before any handler runs, so the deletions and this edit are one commit).

#### 6. `tenet/observer/run.py` (Modify)

*   **Type / Scope**: The detached scan, its status file and banners.
*   **Proposed Changes**: (a) `scan()` drops the `usage.update` and `pattern_drafts.write` calls and returns `(sessions, projects)` instead of the 3-tuple. (b) A one-time migration `_archive_legacy(vault, data)` runs at the start of every scan: if any of `_meta/observer/usage.jsonl`, `patterns.json`, `state.json` exists in the ledger, copy it to `<data>/archive/observer-3.6.1/` (created with the same names), then delete the original with `os.remove`, and record `legacy_archived=<unix time>` in `status.env`; `verdicts.jsonl` is never touched. The next session start prints one line: `TENET: old observer state archived to <path>; run \`git rm --cached _meta/observer/state.json\` in the ledger if it was tracked.` (printed by `briefing()` while `status.env` has `legacy_archived` and no `legacy_notified`; then `legacy_notified` is set). (c) `_write_status` is called once with the keys `new_uses`, `pattern_groups`, `pattern_drafts` removed from the existing file (a one-time prune, since `_write_status` merges and never drops keys). (d) The single try block is split so that the brief phase sets `last_ok`/`error` on its own; this is the phase isolation the counter needs later, done now while the code is open. Rationale: no silent deletion of history, no dead keys, one honest notice.

#### 7. `tenet/observer/transcripts.py` (Modify)

*   **Type / Scope**: The transcript reader.
*   **Proposed Changes**: `read()` no longer collects the `assistant` text list (its only reader was `usage.py`); `PATH_KEYS`, `asked`, `paths` and `prompts` stay for the brief. Rationale: the scan retained every assistant text of 267 sessions for one deleted consumer.

#### 8. `tenet/verdict.py` (Modify)

*   **Type / Scope**: The Stop-hook gate and `verdict apply`.
*   **Proposed Changes**: Remove the `pattern_drafts` import, the `PENDING` test in `eligible()` (line 99), the naming branch in `gate()` (lines 172–178), `_naming()` (lines 143–160) and the `.pattern` session marker. Nothing else changes in this phase; the per-draft claim, the first-option preview and the O(1) Stop path are batch B2a of the retrospective and remain separate commits. Rationale: the naming round never fired and its marker is dead text once the drafts cannot exist.

#### 9. `tenet/sweep.py` (Modify)

*   **Type / Scope**: The weekly inventory.
*   **Proposed Changes**: Replace the `pattern candidates` section (line 75) with a tombstone printed until `TOMBSTONE_UNTIL = "2026-12-01"` (constant, comment: "four weekly runs after 3.7.0"): `--- pattern candidates: retired in 3.7.0 (3 drafts ever, last 2026-10-13); recurrence shortlist arrives in 3.8.0 ---`. After the date the section is omitted. Rationale: the weekly digest must not report an absence it cannot tell from success (the silent-zero-by-deletion the Goldfish named).

#### 10. `tenet/ledger.py` (Modify)

*   **Type / Scope**: The shared note reader.
*   **Proposed Changes**: Remove `template_headings()` (lines 132–140); its only caller was `pattern_drafts`. `section_heading()` (the Decision heading the caps use) stays. Rationale: dead function; `conventions.md`'s "the machinery reads exactly one heading" becomes true again.

#### 11. `tenet/promote.py` (Modify)

*   **Type / Scope**: Session-start promotion and inbox report.
*   **Proposed Changes**: Add to `run()` a check over `inbox/*.md`: a file whose text contains `<!-- pattern-statement: pending -->` is moved to `<data>/verdict/removed/` (the discard location, so it is recoverable) and reported under `TENET INBOX` as `Moved a pending pattern draft to removed/ (pattern drafting retired in 3.7.0): <name>`; when `TENET_DATA` is unset the file is left and the line says so. Rationale: a leftover pending draft would otherwise either be asked as a bare quote or sit forever (Goldfish, migration).

#### 12. `skills/tenet-sweep/SKILL.md` (Modify)

*   **Type / Scope**: Skill text the sweep model follows.
*   **Proposed Changes**: Check 6 becomes one line: `6. Pattern candidates: retired in 3.7.0; the dump prints a tombstone until December. Nothing to do.` The never-list keeps "never write the pattern" out: the sentence is deleted (the author relaxed the rule; the model may phrase a rule in 3.8.0). Rationale: stable numbering, no restated prohibition.

#### 13. `skills/tenet-sweep/references/checks.md` (Modify)

*   **Type / Scope**: The check reference.
*   **Proposed Changes**: Section `## 6. Pattern candidates` is reduced to the same tombstone sentence; the lines describing the observer drafting patterns from a quote (56–74) are deleted. Section 8 is unchanged in this phase.

#### 14. `skills/tenet-capture/SKILL.md` (Modify)

*   **Type / Scope**: The capture skill.
*   **Proposed Changes**: Delete the review-mode line that skips a pattern draft "waiting for its statement" (line 32). Rationale: no such draft can exist.

#### 15. `skills/tenet-capture/references/conventions.md` (Modify)

*   **Type / Scope**: The note model.
*   **Proposed Changes**: In the templates paragraph (lines 63–65) keep "The machinery reads exactly one of them: the first `##` heading of the Decision template", now true. In the pattern paragraph (around line 87) replace "the observer drafts a pattern only from a verbatim quote" with "a pattern is proposed by the weekly sweep from a recurrence (3.8.0) or written by the author; the statement may be phrased by the model, the author's own words stay under Where it came from." Rationale: the text must match the code at every release.

#### 16. `vault-template/templates/Pattern Template.md` (Modify)

*   **Type / Scope**: Ledger template copied by bootstrap.
*   **Proposed Changes**: The leading comment changes from "the user's own insight" to "an insight the author has endorsed; the statement may be phrased by the model; the author's own sentence stays under Where it came from; findings from research or a tool are evidence for a decision instead." No heading changes. Rationale: the glossary pass found the template contradicting the 3.6.0 flow and the author's relaxed rule.

#### 17. `vault-template/.gitignore` (Modify)

*   **Type / Scope**: Template copied into every new ledger.
*   **Proposed Changes**: Append `_meta/observer/` (comment: session ids and local paths) and `.obsidian/graph.json`. Rationale: the live ledger committed observer logs once; the fix never reached the template (retrospective value-measure-16).

#### 18. `README.md` (Modify)

*   **Type / Scope**: The published contract.
*   **Proposed Changes**: In "What it does" delete the pattern-draft bullet (lines 25–28). In "Privacy" delete the usage-log and pattern-quote paragraphs (lines 85–99) and add one sentence: "The observer keeps no log of citations and drafts no notes; it writes briefs and its status to the plugin's data directory, and from 3.7.0 archives the pre-3.7.0 state files there." Add a "Rolling back" subsection under "Configuration" with the five-line runbook (item 24). The remaining README corrections are batch B4 of the retrospective and stay out of this release. Rationale: the privacy text must not describe writes that no longer happen.

#### 19. `CHANGELOG.md` (Modify)

*   **Type / Scope**: One line per version.
*   **Proposed Changes**: `- **3.7.0** (date): the observer's measuring half is gone: no usage log, no machine pattern drafts, no naming round; old state archived to the data directory; the sweep prints a tombstone for check 6 until December; the vault template ignores _meta/observer/; a rollback runbook. Decided in the ledger: <slug of the superseding decision>.`

#### 20. `.claude-plugin/plugin.json` (Modify)

*   **Type / Scope**: Manifest.
*   **Proposed Changes**: `version` to `3.7.0`. Nothing else.

#### 21. `tests/test_observer.py` (Modify)

*   **Type / Scope**: Observer tests.
*   **Proposed Changes**: Delete the usage and pattern-draft tests (the `Usage` cases, `pattern_drafts.write` cases, `measured_since`). Add: `test_scan_archives_legacy_state_once_and_leaves_verdicts_jsonl` (sandbox ledger with the three files and `verdicts.jsonl`; after `scan`, the three are under `<data>/archive/observer-3.6.1/`, the ledger has only `verdicts.jsonl`, `status.env` has `legacy_archived`; a second scan changes nothing); `test_session_start_prints_the_archive_notice_once`; `test_status_env_drops_the_retired_keys`; `test_brief_phase_records_its_own_ok_and_error` (a raised exception in a stubbed second phase leaves `last_ok` set).

#### 22. `tests/test_verdict.py` (Modify)

*   **Type / Scope**: Gate tests.
*   **Proposed Changes**: Delete the `PatternGate` cases (naming round, `.pattern` marker, pending exclusion). Add `test_a_draft_with_the_old_pending_marker_is_not_special` (it is eligible like any proposed draft once promote has moved it; in practice promote moves it first, so the test asserts the move happened at session start via `test_core`).

#### 23. `tests/test_core.py` (Modify)

*   **Type / Scope**: Hook and CLI tests.
*   **Proposed Changes**: Add `test_pending_pattern_draft_is_moved_to_removed_with_a_notice` (inbox file with the marker; after `hook session-start` with `TENET_DATA`, it is under `<data>/verdict/removed/` and the output names it; without `TENET_DATA` it stays and the output says so); `test_no_leftover_names_of_retired_modules` (greps `tenet/`, `skills/`, `README.md`, `vault-template/`, `hooks/` for `patterns.json`, `usage.jsonl`, `pattern_drafts`, `pattern name`, `pattern-statement`, `measured_since`; allowed only in `CHANGELOG.md` and in the archive notice string); `test_template_gitignore_ignores_meta_observer` (bootstrap a temp ledger, `git init`, create `_meta/observer/x.jsonl`, assert `git check-ignore` exits 0); `test_pattern_subcommand_is_gone` (`cli.py pattern name x` exits 2).

#### 24. The rollback runbook (in `README.md`, item 18)

Five lines, verified before release in a scratch marketplace clone: (1) `claude plugin marketplace update tenet`, then `claude plugin uninstall tenet@tenet`, then `git -C ~/.claude/plugins/marketplaces/tenet checkout tenet--v3.6.1`, then `claude plugin install tenet@tenet` (installs 3.6.1 from the clone; the implementer verifies this sequence and, if `install` refuses an older version, documents `claude plugin install tenet@tenet --accept-command` or the `--plugin-dir` route instead); (2) restore `<data>/archive/observer-3.6.1/patterns.json` to `_meta/observer/` if the old pipeline is wanted; (3) `<data>/recurrence/` (3.8.0) is ignored by 3.6.1; (4) proposal drafts in `inbox/` are ignored by 3.6.1's gate; (5) ledger verdicts are not rolled back by code.

#### 25. The ledger act (outside the repository, by the author)

A draft decision in `inbox/`, written by the author with `/tenet:tenet-capture` (or dictated to the session and written there on his instruction), that supersedes `2026-09-27-elfogadas-nem-vegallapot`: recurrence counting replaces use counting; the archive is deferred to the January retro with `revisit` set to that date; the kill test (no accepted proposal after eight weeks, or an accepted key still recurring without a mechanism), the weekly budget and the event-table format are in its body; `supersedes` points at the 09-27 note. 3.7.0's CHANGELOG line names the slug. The release does not edit the 09-27 note.

### Phase 2: the counter (3.8.0)

Depends on batch B2a of the retrospective (per-draft claim, preview on the first option only, Stop path O(1) in transcript size) and batch B0 (Discard copies to the data directory before `git rm`). Ships only after the replay fixture (item 36) reports its recall numbers.

#### 26. `tenet/observer/recurrence.py` (Create)

*   **Type / Scope**: Python module, stdlib only; the counter, its state, the receipt, the validator, the privacy gate.
*   **Proposed Changes**: Constants (one block): `MIN_SESSIONS = 3`, `MIN_DAYS = 2`, `COLLAPSE_SECONDS = 600`, `SHORT_MAX_STEMS = 5`, `QUOTE_CHARS = 160`, `CARD_BYTES = 900`, `RULE_WORDS = 30`, `KEEP_DAYS = 180`, `STATE_CAP_BYTES = 2_000_000`, `WEEKLY_BUDGET = 1`, `FIRST_RUN_GRACE_DAYS = 7`, `BACKOFF_AFTER_DISCARDS = 2`, `WAITING_BANNER_DAYS = 14`, `FORMS = ("note", "claude-md-line", "hook", "loop", "skill", "agent", "harness-setting", "mechanism", "delete-rule")`, `KINDS = ("new-expectation", "repeated-break")`, `KIND_FORMS = {"repeated-break": ("mechanism", "delete-rule"), "new-expectation": FORMS minus those two}`, `SENSITIVE = ("personal-email", "family-finance", "buxa", "hovege")` overridden by `TENET_SENSITIVE` (comma-separated prefixes), `PII` and `AUTHORITY` patterns ported verbatim from dream.py with their comments. Files under `<data>/recurrence/`: `occurrences.jsonl` (rows `{"schema":1,"key":…, "session":…, "ts":"ISO", "project":…, "kind":"prompt"|"command", "text": str|null}`), `receipts.jsonl` (rows `{"schema":1,"ts":…, "state":"not_examined"|"examined"|"found_suppressed"|"proposed", "reason":…, "files_read":n, "files_skipped":n, "sessions":n, "prompts":n, "commands":n, "keys":n, "at_threshold":n, "nearest":[[key,sessions]…], "suppressed":{reason: n}, "duration_ms":n, "bytes":n, "gitleaks": true|false}`), `clusters.json` (`{"schema":1, "clusters": {key: {"first":…, "last":…, "sessions":[…], "days":[…], "projects":[…], "n":n, "status":"open"|"proposed"|"accepted"|"discarded"|"did_not_hold", "proposed_on":…, "draft":…, "verdict":…, "form":…, "post_settle":[ts…]}}}`), `files.json` (`{path: [size, mtime]}` for the incremental pass). Functions: `key_of(text)`, `occurrence_rows(prompts)`, `pass_(data, sessions, now)`, `clusters(data, now)`, `covered_by(vault, key_stems)` (ledger slugs across all statuses plus skill and hook names under the config dir; a `reversed` or `superseded` match yields `previously_tried`), `receipt(data)`, `propose(vault, data, key, fields, revise=False)`, `settle(data, key, verdict, form, date)`, `budget_ok(data, now)`, `gate_text(card)` (the PII, authority, leak and gitleaks checks; `gitleaks` optional: absent means `text` is stored as null everywhere and the receipt says `gitleaks: false`). A damaged or newer-schema state file raises `RecurrenceStateError`, caught by `run.scan` into `counter_error` and the FAILING banner; it is never read as empty. The card layout written by `propose`: frontmatter `type: proposal`, `created`, `status: proposed`, `recurrence_key`, `kind`, `form`, `categories: []`; section 1 `## Recurrence` with the headline line (`N times · S sessions · D days · P projects · first–last`) and one line per occurrence (`YYYY-MM-DD · project · "quote"` or `YYYY-MM-DD · project · [sensitive: normalised phrase]`); section 2 `## Proposal` with the rule, `Form: <form> — <reason>`, `Standing cost: <line>`, `Covered by: <slugs/skills or none>`, `Previously tried: <slug (status)> or none`, `Kind: <kind>`. The validator refuses with one printed reason per failure (missing field, rule over `RULE_WORDS`, form not allowed for the kind, quote not a verbatim substring of its occurrence row, fewer than `MIN_SESSIONS`, card over `CARD_BYTES`, budget spent, proposal pending, key sticky-discarded, gate hit) and counts refusals in the receipt. Rationale: one module, one state directory, every number and message pinned here so the implementer decides nothing.

#### 27. `tenet/observer/transcripts.py` (Modify)

*   **Type / Scope**: The transcript reader.
*   **Proposed Changes**: `read()` returns `prompts` as records `{"text", "ts", "session", "project"}` (`ts` from the record's `timestamp`; `project` is the session root), and a `commands` list of command names taken from `<command-name>` wrappers (name only). `sessions()` keeps the file-mtime selection and adds a per-record window (`ts >= cutoff`) applied by `recurrence.pass_`; the brief's inputs are unchanged. Rationale: dates on a card must be real; the manual-trigger signal must be visible (Goldfish, observability).

#### 28. `tenet/observer/run.py` (Modify)

*   **Type / Scope**: Scan scheduling and status.
*   **Proposed Changes**: `scan()` gains phase 2: `recurrence.pass_` in its own try block writing `counter_last_ok`, `counter_error`, `counter_clusters`, `proposals_open` (and never touching `last_ok`); when `TENET_RECURRENCE == "off"` the phase is skipped and the receipt row has `state: not_examined, reason: off`. `due()` gains `COUNTER_STALE_SECONDS = 86400` and `COUNTER_RETRY_SECONDS = 3600`: returns `"recurrence pass"` when the last receipt is older than a day and the last attempt older than an hour; `scan` then runs the brief phase only if the brief is also due. `banners()` adds `TENET RECURRENCE FAILING: <counter_error>` and `TENET PROPOSAL WAITING: <key> unseen for N days` (from `clusters.json`, `proposed_on` older than `WAITING_BANNER_DAYS` with no verdict). Rationale: the counter must not take the brief down; its lag must be visible.

#### 29. `tenet/sweep.py` (Modify)

*   **Type / Scope**: The weekly inventory.
*   **Proposed Changes**: Remove the tombstone; add `--- recurrence shortlist ---` printing: the last receipt line in words (`examined 2026-11-10: 41 sessions, 310 prompts, 118 keys, 2 at threshold; nearest: kesz (2 sessions); gitleaks present`), then per cluster at threshold: key, `N times · S sessions · D days · P projects`, each occurrence line, `covered by`, `previously tried`, `status`; then `commands typed this month: /wrap 31, /verdicts 2, …`; when nothing is at threshold, `no cluster at threshold; nearest: …`; when the counter is off or failing, the receipt's reason. Rationale: the sweep model works from the dump and must see denominators and near misses.

#### 30. `tenet/verdict.py` (Modify)

*   **Type / Scope**: The gate and apply, on top of batch B2a.
*   **Proposed Changes**: `eligible()` admits `type: proposal` drafts when sections 1–2 are at most `CARD_BYTES` (the 60/400 word caps do not apply to them); `_card` is unchanged (sections 1–2 are the card). For a proposal the three options are `Accept as <form>` ("records the verdict and the form; the carry-out is this session's next task when the form is not a note"), `Not a pattern` ("removes the draft and never proposes this recurrence again"), and free text through Other ("accept with this change: the rule or the form"). `apply`: on Accept, `set_status(accepted)`, write `{"date", "draft", "verdict": "accepted", "form": <form>, "key": <recurrence_key>}` to `verdicts.jsonl`, call `recurrence.settle`, and when the form is not `note` print `CARRY OUT: the author accepted <form> for "<rule>". Make that change now in this session with the author present; a change outside this repository is a new question to the author, not a silent write.`; a `note` form promotes as today. On Not a pattern, `_remove` (B0 semantics) plus `settle(discarded)` (sticky). On free text, print `EDIT REQUESTED` as today but followed by `then run: cli.py recurrence propose <key> --revise` and, on that command's success, record `accepted-edited` in the same stop; the card loops at most once (a second free text is recorded as `accepted-edited` without re-asking). Rationale: Accept means one thing; correction completes in one dialog.

#### 31. `tenet/cli.py` (Modify)

*   **Type / Scope**: Entry point.
*   **Proposed Changes**: Subparser `recurrence` with `pass` (runs `pass_` for the current window, prints the receipt), `status` (prints the last receipt, open proposals, the event table rows from `clusters.json` and `verdicts.jsonl`, and `--baseline` which prints only the at-threshold count for the ledger decision), `propose <key> [--revise]` (JSON on stdin: `rule`, `form`, `kind`, `reason`, `standing_cost`; prints the draft path or the refusal reasons; exit 1 on refusal). `observe status` prints the counter keys. All printed commands carry `TENET_LEDGER` and `TENET_DATA`.

#### 32. `skills/tenet-sweep/SKILL.md` and `skills/tenet-sweep/references/checks.md` (Modify)

*   **Type / Scope**: Skill text and reference.
*   **Proposed Changes**: Check 6's tombstone line is removed. Check 8 becomes "Recurrence and repeated deviations": inputs are the `recurrence shortlist` section, `_meta/retro.md` and the feedback notes; for each shortlist cluster the model decides whether it is a real recurrence (not an acknowledgement, not a template paste), names its kind (`repeated-break` when an existing rule, note or skill already covers it; else `new-expectation`), chooses the form from `KIND_FORMS`, writes the one-sentence rule in the language of the quotes, and runs `python3 ${CLAUDE_PLUGIN_ROOT}/tenet/cli.py recurrence propose <key>` with the JSON on stdin; at most one proposal per run; the model never writes a proposal draft by hand and never edits `clusters.json`. The two-outcome rule for repeated deviations stays. The description of check 8's draft slot now names the validator as the only writer. Rationale: the sweep phrases, the code validates and writes.

#### 33. `skills/tenet-capture/references/conventions.md` (Modify)

*   **Type / Scope**: The note model.
*   **Proposed Changes**: Add `proposal` to the `type` table: "a recurrence proposal written by `cli.py recurrence propose` from the weekly sweep; sections 1–2 are the verdict card; frontmatter `recurrence_key`, `kind`, `form`. On Accept the draft is promoted to the ledger root as the record of the decision with its `form` kept in the frontmatter; proposal notes are not scored for the brief (the brief corpus takes decision, pattern, gotcha and open notes only) and are visible to the sweep." State that proposal drafts are exempt from the word caps and bound by the card byte cap.

#### 34. `README.md` (Modify)

*   **Type / Scope**: Published contract.
*   **Proposed Changes**: "What it does": one bullet for the counter (what recurs, how it is proposed, the three answers). "What runs when": a row for the daily counter pass (session start, at most once a day, detached, incremental). "Configuration": `TENET_RECURRENCE=off`, `TENET_SENSITIVE`. "Privacy": what the counter reads (the author's prompts of the last 30 days with their timestamps; command names), what it stores (`<data>/recurrence/`: keys, sessions, dates, projects, a quote of at most 160 characters from non-sensitive projects only, none without gitleaks), what reaches the ledger (one proposal draft at a time, through the validator), the sensitive-project rule. "Known limits": recall is measured on the replay fixture and stated with its number.

#### 35. `CHANGELOG.md`, `.claude-plugin/plugin.json` (Modify)

*   **Proposed Changes**: One 3.8.0 line naming the counter, the card, the budget and the recall figure; `version` to `3.8.0`.

#### 36. `tests/test_recurrence.py` and `tests/fixtures/recurrence/` (Create)

*   **Type / Scope**: Unit tests and a replay fixture.
*   **Proposed Changes**: Fixture: a synthetic, anonymised transcript corpus (JSONL records in the harness shape, no real text) with at least: four sessions on three days containing the short "are we done?" forms; three sessions with the long paraphrase forms; a single session repeating one prompt five times; two sessions within ten minutes with the same prompt; a sensitive-project session; a session whose prompts are only `/wrap` commands; a pasted template repeated in two sessions. Tests (failing direction stated for each): `test_key_of_short_and_long_prompts`; `test_same_session_repeats_count_once`; `test_parallel_sessions_within_ten_minutes_collapse`; `test_cluster_needs_three_sessions_on_two_days` (two sessions or one day must not reach threshold); `test_sensitive_project_stores_no_quote`; `test_without_gitleaks_no_quote_is_stored`; `test_receipt_not_examined_when_no_transcripts` (the state is `not_examined`, not an examined zero); `test_receipt_examined_zero_prints_denominators_and_nearest`; `test_incremental_pass_skips_unchanged_files`; `test_damaged_state_raises_not_empty`; `test_settle_keeps_counting_post_settle`; `test_discard_is_sticky`; `test_budget_one_per_week_and_backpressure`; `test_first_run_grace`; `test_propose_refuses_each_missing_or_bad_field` (one case per refusal reason); `test_propose_card_is_under_900_bytes_and_quotes_are_verbatim`; `test_repeated_break_may_only_propose_mechanism_or_delete`; `test_previously_tried_reversed_decision_suppresses`; `test_replay_recall_on_known_cases` (asserts the short family is found; records the paraphrase family's result as a number in the assertion so a change is visible; the recall figure is copied into the README by hand).

#### 37. `tests/test_verdict.py`, `tests/test_core.py`, `tests/test_observer.py` (Modify)

*   **Proposed Changes**: `test_verdict.py`: proposal eligibility by byte cap, the three option labels, `apply` writing `form` and `key`, the `CARRY OUT` line for a non-note form, promotion for the note form, sticky discard, `accepted-edited` after `--revise`. `test_core.py`: the sweep prints the shortlist section in each receipt state; `recurrence status --baseline` prints one number; `TENET_RECURRENCE=off` yields `not_examined: off`. `test_observer.py`: `due()` returns `recurrence pass` after a day; a counter exception sets `counter_error` and the FAILING banner while `last_ok` stays; the waiting banner after 14 days.

#### 38. dream.py (the author's private file; no repository change)

*   **Proposed Changes**: By the author, after 3.8.0 is live: delete the `HUMAN_KINDS` stage-2 comment and any prompt-counting intent; keep the tool-failure and hook-friction scans and the routine checks; record the division in the ledger decision. tenet does not read or write `~/.claude/dream`.

### Verification Plan

*   **Unit tests**: `python3 -m unittest discover -s tests -t .` green on Python 3.9 (the macOS system interpreter) in both phases; the suite is hermetic (`TENET_DATA` and `CLAUDE_CONFIG_DIR` pointed at temp dirs by `tests/helpers.py`, batch B0).
*   **Manifest and CI**: `claude plugin validate .claude-plugin/plugin.json`; the CI invariants (hooks.json tokens, fenced `!` blocks, frontmatter on tracked markdown) unchanged; the new `test_no_leftover_names_of_retired_modules` runs in CI through the suite.
*   **Sandbox run, phase 1**: `d=$(mktemp -d); python3 tenet/cli.py bootstrap $d/ledger; export TENET_LEDGER=$d/ledger TENET_DATA=$d/data`; seed the three legacy files and a pending pattern draft; `hook session-start` twice (archive notice once, the draft moved, no retired keys in `status.env`); `observe scan` (no usage or pattern output); `sweep | grep 'pattern candidates'` shows the tombstone; `pattern name x` exits 2.
*   **Sandbox run, phase 2**: with the fixture corpus as `CLAUDE_CONFIG_DIR/projects`: `recurrence pass` (receipt `examined`, two clusters at threshold), `sweep` (shortlist section), `recurrence propose <key>` with a hand-written JSON (draft written; a second call refused by backpressure), a hand-written ticket through `verdict apply` with each of the three answers (`verdicts.jsonl` rows carry `form` and `key`; `clusters.json` status changes; `CARRY OUT` printed for a hook form), `recurrence status` (event table), `TENET_RECURRENCE=off` (receipt `not_examined: off`).
*   **Rollback drill**: in a scratch marketplace clone, run the five-line runbook from 3.7.0 back to 3.6.1 and forward again; record the exact commands that worked in the README before release.
*   **Live acceptance (author's machine, after release)**: the first weekly sweep after 3.8.0 shows the shortlist with the "are we done?" cluster; no proposal in the first-run grace week; the second sweep writes one proposal; the next resting point shows the card; the event table has one row. The January retro reads the table against the baseline recorded in the ledger decision.
