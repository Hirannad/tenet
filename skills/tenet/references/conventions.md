# Vault conventions

**Property names are English, and so is every value a script compares against** — `type`,
`status` and `scope` above all, because `.base` filters and `scripts/resolve.sh` test them as
literal strings, and a translated value silently drops a note out of the session list. Free-text
properties are different: `revisit` is only printed and tested for emptiness, so it is written in
the vault's language like any other prose. **Everything the user reads is in the vault's own
language** — prose *and* section headings.

Section headings used to be English on a compatibility argument. That argument only ever held for
properties: nothing queries a heading. A note that switches language every heading is harder to
scan, which was the whole complaint that ended it.

The headings come from the plugin's locale — English by default, or whatever `_meta/locale` names
(`locales/hu.sh` ships as a worked example). Below they are written in the English default. If your
vault runs another locale, read them as that locale's equivalents: the 60-word cap matches on the
configured heading, not on the word "Decision".

## Frontmatter

Every knowledge note carries these:

| Property | Values | Notes |
|---|---|---|
| `type` | `decision`, `pattern`, `open`, `source`, `gotcha` | Drives every saved view. `meta` and `raw` also exist, but they mark machinery rather than knowledge: `_meta/` files and admitted raw material |
| `created` | `YYYY-MM-DD` | Dates are `YYYY-MM-DD` everywhere, no exceptions |
| `status` | see [the status list](#status) | One axis: where the note stands in the review loop |
| `scope` | `universal` or `domain` | See below. Default `domain` |
| `categories` | list of `"[[Plural Noun]]"` | Always plural. The link resolves to a root file named exactly that (`Methods.md`), which is the hub — see `tenet-sweep`, check 9 |
| `related` | list of wikilinks | Link generously |

Type-specific: `revisit` and `supersedes`/`superseded` on decisions, `derived` on patterns,
`resolves` on open questions, `url`/`accessed`/`influenced`/`kept` on sources, `admission` on files
in `raw/`. A `gotcha` adds nothing — in particular no `revisit`, because there is nothing to
reconsider about a fact.

**Never use hyphens in property names.** A hyphen inside a `.base` filter expression parses as
subtraction, which silently breaks the view. This is why the fields are `revisit` and not
`revisit-when`.

## Status

Seven values, one axis: **where the note stands in the review loop.** The same list applies to
every type — `revisit` and `resolves` carry the type-specific meaning, not `status`.

| Status | Meaning | What happens to the note |
|---|---|---|
| `proposed` | A draft. Not part of the ledger yet. | Stays in `inbox/`, appears in the Inbox view |
| `unclear` | The user could not judge it. Not a rejection — the note failed, not the idea. | Stays in `inbox/`, appears in the Inbox view, needs rewriting or splitting |
| `accepted` | Approved. This is what the user works by. | `promote.sh` moves it to the vault root |
| `rejected` | Weighed and turned down before it was ever adopted. **Kept** — the reasoning is still worth having. | Vault root, excluded from Revisit |
| `superseded` | A later note replaced it. Link the replacement in `superseded`. | Vault root, excluded from Revisit |
| `reversed` | It was live, then undone. The `revisit` condition fired. | Vault root, excluded from Revisit |
| `resolved` | An open question that has been settled. | Vault root |

`rejected` and `reversed` are not the same thing: `rejected` never took effect, `reversed` did and
was then undone. That distinction is the point of keeping both.

**The user should not have to type these.** Obsidian 1.12 has no enum property type, so `status`
renders as a free text box with no dropdown and no tooltip — which is how `canceled` and `confused`
ended up in the vault on 2026-07-28. Statuses are set through `/tenet:tenet-capture review`; `promote.sh`
reports anything off-vocabulary that was written by hand. The user-facing copy of this table lives
in `_meta/statuses.md`.

## Note format — the 30-second test

A note earns its place only if the user can grasp the decision in about half a minute. The first
batch failed this test, and the rules below are what it failed on.

**Section order is reading order.** The user reads the decision first, then the reversal condition,
then the reasoning — so that is the order on the page. Context and options go last; they are for
the case where the decision is not self-explanatory.

`## Decision` → `## When to reconsider` → `## Why` → `## Background` → `## Options weighed` →
`## The dilemma`

**Length is capped.** `## Decision` at 60 words, the whole note at 400. A note that will not fit is
almost always two decisions.

**Plain, practical prose — this is the actual content of the 30-second test.** The verdict that
produced this rule, on a vault's first generation of notes: *not practical enough, not close enough
to how you would actually say it.* Write the way you would say it out loud. Concretely:

- Second person and everyday words beat nominalised abstractions. "If you catch yourself doing X"
  beats "if information of a state-like character".
- No coined vocabulary unless the note also shows the concrete case it came from. Terms like
  "silent decay" or "carrier" are assistant vocabulary and read as jargon to the person the note is
  for.
- Cut any sentence whose only job is to cross-reference another note. A wikilink in `related` does
  that without costing the reader a paragraph.
- Keep the numbers and the named cases. Plain does not mean vague — the concrete example is usually
  the most readable thing in the note.

The word caps are a **proxy** for this and provably cannot catch it: the note that failed on
2026-07-29 was 346 words, inside every limit, and still unreadable.

**One decision per note.** If two choices have separate reversal conditions, they are separate
notes. The note that produced this rule carried two, and became impossible to give a verdict on:
accepting it accepted both, rejecting it lost the good half.

**Do not hand-wrap prose.** One paragraph, one line; the editor wraps it. Hand-wrapping at 100
characters is what made the notes read as "oddly broken up", and it turns every human edit into a
reformat diff that hides the real change.

**Frontmatter in Obsidian's normalised form** — block lists, not inline arrays. Obsidian rewrites
inline arrays the first time the user touches a property, so writing them that way guarantees noise
in the next diff.

**An addendum may add evidence; it may never flip the conclusion.** If a later finding changes the
decision, rewrite `## Decision` and move the old text into `## Why` as history — or supersede the
note. A tail section that contradicts the decision above it leaves the reader with no answer, which
is exactly the shape that earns a note `unclear` at review and forces a split.

## Scope

- `universal` — methodology, architecture, structure. How the user works. Visible in every
  directory, in every session.
- `domain` — everything else. Visible only where bound.

Default to `domain`. Propose `universal` when the decision is about *how to work* rather than
*what was built*, and let the user approve it. A universal layer that swallows everything
recreates the leakage the scoping exists to prevent, so the maintenance run watches its size.

**`gotcha` is the exception, in both directions.** It defaults to `universal`, because a tool's
behaviour is not the property of one project — and `resolve.sh` skips the type anyway, so it never
reaches the session-start list. That is deliberate: the list says what has been *decided*, and a
gotcha is reference material a decision cites in `## Why`. It also means the universal count that
the maintenance run watches must exclude gotchas, or the number stops measuring what it is for.

## Naming

- Note titles are the filename. Descriptive sentences beat labels: `Isolation by binding rather
  than splitting the vault` is findable, `Scoping` is not.
- Templates end in ` Template` — the saved views exclude them by name.
- Categories are plural: `[[Decisions]]`, `[[People]]`, `[[Tools]]`.

## Layout

Knowledge notes live **flat in the vault root**. Folders are machinery only: `_meta/`, `inbox/`,
`raw/`, `bases/`, `templates/`. Never create a folder to organise knowledge — that is what
`type` and `categories` are for, and it is what keeps a note from having to live in exactly
one place.

## Linking

- Link to related notes liberally; the graph and backlinks are the payoff.
- **Link every note to its topic hub.** At scale this is what makes the graph cluster by topic
  instead of collapsing into one hairball.
- Wikilinks `[[Note]]` for anything inside the vault, Markdown links for external URLs.

## Evidence versus insight

External findings — from research, tooling, or an assistant — are **evidence**. They belong in
the `## Why` section of a decision, with their source named. They never become a `pattern`.

A `pattern` records the **user's own** insight, in their own formulation. This boundary is what
lets them look back later and tell their own thinking apart from what was handed to them.

## Enforcement

Every rule above appears in this table with what catches it when it is broken — or with `none` and
the reason. **A rule missing its enforcement cell is itself the defect**, and `promote.sh` counts
those cells so the silence is a number rather than an assumption. The principle: a convention may
enter without a mechanism, but never without being marked.

`none` is a legitimate answer and most of the table says it. Judgement calls cannot be mechanised,
and a rule that resists automation does not become invalid by resisting it. What the table removes
is the third state — a rule nobody ever asked the enforcement question about.

| Convention | What catches it |
|---|---|
| `status` from the seven-value list | `promote.sh` validates, reports off-vocabulary values |
| Reviewed notes leave `inbox/` | `promote.sh` moves them off the SessionStart hook |
| `## Decision` ≤ 60 words | `promote.sh`, drafts only (matches the locale's heading) |
| Whole note ≤ 400 words | `promote.sh`, drafts only — decisions and gotchas |
| Plain, practical prose | none — no checker reads for readability, and the word caps demonstrably miss it: one note came in at 346 words, inside every limit, and was still unreadable. A prose linter for the vault's language helps if one exists, but nothing runs it for you |
| Every rule here carries an enforcement cell | `promote.sh` counts empty cells |
| Required frontmatter properties present | none — templates supply them; a miss shows as an empty column in the `bases/` views |
| Dates are `YYYY-MM-DD` | none — Obsidian's date picker writes the format |
| No hyphens in property names | `promote.sh` — frontmatter keys across the whole vault, not just drafts |
| `status` written by review, not by hand | none — `promote.sh` catches the *consequence* (an invalid value), not a hand edit that happens to be valid |
| Section order is reading order | none — templates supply the order; deviation is visible on sight |
| One decision per note | none — judgement call. This is the stated exception, and the length caps are its proxy |
| One paragraph per line, no hand-wrapping | none — visible in any diff |
| Frontmatter as block lists | none — Obsidian normalises it on first touch |
| An addendum may not flip the conclusion | none — judgement call, and the known repeat offender is the assistant |
| `scope` defaults to `domain` | none — the user approves scope per note during review |
| `gotcha` defaults to `universal` | none — the template ships it; nothing forces a hand edit back |
| Gotchas stay out of the session-start list | `resolve.sh` skips `type: gotcha` |
| A gotcha with two viable paths is a decision | none — judgement call. The gotcha type carries its own reversal condition — below three in half a year, or a two-path entry, kills the type — and `tenet-sweep` check 1 reads that condition against the gotcha count |
| Universal layer under ~15 notes | `tenet-sweep`, check 6 — weekly, not per session, and gotchas do not count |
| Titles are descriptive sentences | none — judgement call |
| Categories are plural | none |
| Knowledge notes flat in the vault root | none — `promote.sh` only ever writes to the root, so drift needs a manual move |
| Notes link to a topic hub | `tenet-sweep`, check 9 — reports categories past five with no hub |
| Findings are evidence, never a `pattern` | none — judgement call, and the boundary the whole vault rests on |
