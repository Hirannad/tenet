<!-- Injected by the brain skill's Stop hook. Only reaches the model when the vault exists. -->

BRAIN CHECK — run this silently, then continue.

Did this session contain any of the following?

**A.** A real decision: at least two genuinely viable paths, where one was chosen for a reason.
**B.** An insight *the user themselves* arrived at and stated — a formulation of theirs worth
keeping, not a finding you produced.
**C.** A tool that surprised you and will again — behaviour nobody would predict, not specific
to this repository, and with no second viable path. That is a `gotcha`. Test it against A
first: if two viable ways existed and one was picked, it is a decision, not a gotcha.

**If none: do nothing. Output nothing about this. Stop here.** Most sessions qualify for
none, and that is the expected outcome.

If one applies, write **at most one** draft per session to `inbox/YYYY-MM-DD-short-slug.md` inside
the vault, using the matching template from its `templates/`, then mention in one short sentence
that a draft is waiting. The vault is `$BRAIN_VAULT` when that is set and `~/Claude/brain`
otherwise — resolve it rather than assuming the default, because a note written to the wrong
directory is invisible to every check that follows.

Rules for the draft:

- `status: proposed` — always. It is a draft, not part of the brain until the user approves it.
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
  note under 400 words. One decision per note. One paragraph per line — never
  hand-wrap prose. Frontmatter as block lists, not inline arrays.
- Prose and headings in the vault's language — match the existing notes, and take the headings from
  the templates rather than translating them. Property names and values stay English.
- **Your own findings are evidence, not insight.** Anything you discovered goes in `## Why`
  with its source named. It never becomes a `pattern`.
- Write only into `inbox/`. Never touch notes in the vault root, `_meta/`, or `raw/` from here —
  the retro check below is the single exception, and it only ever appends.

Do not re-run this check after writing. One draft, then done.

What does NOT deserve a draft: routine implementation, forced moves with no alternative,
debugging, a summary of what was done, or anything already recorded in an existing note.

---

RETRO CHECK — a separate question, under the same silence rule.

Did the user have to **enforce a rule by hand** this session? That is: something only came out
right because they pointed it out — a language rule, a convention, a repo rule, or something they
had already stated earlier and had to state again.

**If not: do nothing. Output nothing about this.** That is the expected outcome for most sessions.

If yes, append **one** dated section to the vault's `_meta/retro.md`, newest on top, in the
format that file already uses. One bold-led paragraph per correction, each naming four things:
what deviated, which rule it touched, which error class it falls into (the class table in that
file — add a row if none fits; it ships empty, so the first deviation names the first class),
and what would have caught it — or `none`. **Append only; never edit an existing entry.**

A rejection on the merits is not a deviation, and neither is the user changing their mind. Both
are normal operation.
