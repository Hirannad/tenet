"""A pattern draft, only when the user's own words are on record.

A pattern is the user's insight. The sweep lists groups of decisions that may share one; this
step looks for the user saying something about it in a transcript. With a verbatim quote it
writes a `proposed` draft that keeps the quote as evidence; without one it writes nothing. A
script cannot phrase the shared rule, so the draft waits until a session's model states it
(`name`), and only then is the user asked for a verdict."""
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from tenet import ledger, patterns, paths
from tenet.observer import textindex

MIN_HITS = 4  # distinct group terms a sentence must contain: fewer matches a topic, not an idea
MIN_WORDS, MAX_WORDS = 6, 45
SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")
PENDING = "<!-- pattern-statement: pending -->"
FIELDS = ("title", "statement", "holds", "holds_not")


def _emitted_file(vault):
    return paths.observer_dir(vault) / "patterns.json"


def _emitted(vault):
    try:
        return set(json.loads(_emitted_file(vault).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def find_quote(group, sessions):
    """The user's best-matching sentence for a group: (hits, quote, date, project) or None. Only
    human prompts are searched, since `transcripts` keeps no other author."""
    terms = set(group["terms"])
    best = None
    for s in sessions:
        for prompt in s["prompts"]:
            for sentence in SENTENCE.split(prompt):
                if not MIN_WORDS <= len(sentence.split()) <= MAX_WORDS:
                    continue
                hits = len(terms & set(textindex.tokens(sentence)))
                if hits >= MIN_HITS and (best is None or hits > best[0]):
                    best = (hits, sentence.strip(), s["date"], s["root"])
    return best


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", textindex.fold(text)).strip("-")


def _lead(group):
    """The member whose title carries most of the group's terms: it names the draft until the
    draft is stated."""
    terms = set(group["terms"])
    return max(group["members"], key=lambda m: len(terms & set(textindex.tokens(ledger.title(m.stem)))))


def _sections(heads, parts):
    """The template's headings over their parts, in order; a heading with nothing under it is left out."""
    return "\n".join(f"## {h}\n\n{t.strip()}\n" for h, t in zip(heads, parts) if t.strip())


def _draft(vault, group, quote):
    _, text, day, root = quote
    heads = ledger.template_headings(vault, "Pattern")
    cats = Counter(c for m in group["members"] for c in ledger.listed(ledger.read(m)[0], "categories") if c)
    top = cats.most_common(1)[0][0] if cats else ""
    derived = "".join(f'\n  - "[[{m.stem}]]"' for m in group["members"])
    origin = ("\n".join(f"- [[{m.stem}]]" for m in group["members"])
              + f"\n\n> {text}\n\n— {day}, {Path(root).name}\n\n<!-- pattern-key: {group['key']} -->")
    return (f"---\ntype: pattern\ncreated: {date.today().isoformat()}\nstatus: proposed\n"
            f"categories:\n  - \"{top}\"\nderived:{derived}\nrelated:\n---\n\n{PENDING}\n\n"
            + _sections(heads, ["", "", "", origin]))


def pending(vault):
    """Drafts still waiting for their statement."""
    return [d for d in ledger.md_files(Path(vault) / "inbox") if PENDING in d.read_text(encoding="utf-8", errors="replace")]


def name(vault, draft_name, spec):
    """Write the model's statement and boundaries into a pending draft, under the template's first
    three headings, and rename it after the title. Frontmatter and evidence stay as written.
    Returns output lines."""
    vault = Path(vault)
    draft = vault / "inbox" / draft_name
    if not draft.is_file() or PENDING not in draft.read_text(encoding="utf-8", errors="replace"):
        return [f"PATTERN REFUSED: inbox/{draft_name} is not a pattern draft waiting for its statement."]
    missing = [k for k in FIELDS if not str(spec.get(k) or "").strip()]
    if missing:
        return [f"PATTERN REFUSED: {', '.join(missing)} missing; pass {', '.join(FIELDS)} as JSON on stdin."]
    fm, block, body = ledger.read(draft)
    target = draft.with_name(f"{fm['created']}-{_slug(spec['title'])}.md")
    if target.exists() or (vault / target.name).exists():
        return [f"PATTERN REFUSED: {target.name} is taken in the inbox or the ledger; choose another title."]
    heads, kept = ledger.template_headings(vault, "Pattern"), ledger.sections(body)
    parts = [spec["statement"], spec["holds"], spec["holds_not"]] + [kept.get(h, "") for h in heads[3:]]
    paths.write_atomic(target, f"---\n{block}---\n\n" + _sections(heads, parts))
    draft.unlink()
    return [f"PATTERN NAMED: inbox/{target.name} (was {draft_name})."]


def write(vault, sessions):
    """Return (groups seen, drafts written). A group already proposed once, even if its draft was
    discarded since, is not proposed again."""
    vault = Path(vault)
    _, groups = patterns.candidates(vault)
    done = _emitted(vault)
    written = []
    for g in groups:
        if g["key"] in done:
            continue
        quote = find_quote(g, sessions)
        if quote is None:
            continue
        path = vault / "inbox" / f"{date.today().isoformat()}-pattern-{_slug(ledger.title(_lead(g).stem))}.md"
        if path.exists():  # an earlier group with the same lead decision, still waiting
            path = path.with_name(f"{path.stem}-{g['key']}.md")
        path.parent.mkdir(exist_ok=True)
        paths.write_atomic(path, _draft(vault, g, quote))
        written.append(g["key"])
    if written:
        _emitted_file(vault).parent.mkdir(parents=True, exist_ok=True)
        paths.write_atomic(_emitted_file(vault), json.dumps(sorted(done | set(written))) + "\n")
    return len(groups), len(written)
