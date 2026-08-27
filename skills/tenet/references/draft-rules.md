<!-- How to write one draft, once the Stop gate in stop-prompt.md has fired.

     Split out of stop-prompt.md in 2.1.0. That file is injected at the end of
     every response; this one is read only when a draft is actually being
     written, which is the rare case. The gate cost went from 3.2 KB per response
     to roughly 0.9 KB, and the part that shrank is the part that was never
     needed at the moment it was paid for. -->

Write **at most one** draft per session, to `inbox/YYYY-MM-DD-short-slug.md` inside the vault,
using the matching template from its `templates/`.

Resolve the vault path from the gate text rather than assuming a default: a note written to the
wrong directory is invisible to every check that follows.

Rules for the draft:

- `status: proposed` — always. It is a draft, not part of the ledger until the user approves it.
- **Write today's real date into every `{{date:…}}` placeholder** the template carries.
  Obsidian expands those for a human creating a note from the template; nothing expands them
  for you, and `bases/Inbox.base` sorts drafts by `created` — a literal placeholder puts every
  draft on the same non-date and the "Oldest first" view stops ordering anything.
- `scope: domain` unless the decision is about *how to work* (methodology, architecture,
  structure) rather than *what was built* — then `scope: universal`. A `gotcha` ships
  `universal` from its template; leave it.
- Fill `revisit` (decisions) or `resolves` (open questions). A decision without a reversal
  condition is half a decision. A `gotcha` carries neither.
- **Pass the 30-second test.** `## Decision` first, at most 60 words, then `## When to
  reconsider` (decisions — a gotcha keeps its template's four sections instead); the whole
  note under 400 words. One decision per note. One paragraph per line — never hand-wrap prose.
  Frontmatter as block lists, not inline arrays.
- Prose and headings in the vault's language — match the existing notes, and take the headings
  from the templates rather than translating them. Property names and values stay English.
- **Your own findings are evidence, not insight.** Anything you discovered goes in `## Why`
  with its source named. It never becomes a `pattern`.
- Write only into `inbox/`. Never touch notes in the vault root, `_meta/`, or `raw/` from here.

Do not re-run the gate after writing. One draft, then done.

What does NOT deserve a draft: routine implementation, forced moves with no alternative,
debugging, a summary of what was done, or anything already recorded in an existing note.
