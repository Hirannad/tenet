"""A pattern draft, only when the user's own words are on record.

A pattern is the user's insight. The sweep lists groups of decisions that may share one; this
step looks for the user saying something about it in a transcript. With a verbatim quote it
writes a `proposed` draft that opens with the quote and leaves the rest to the user; without
one it writes nothing."""
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


def _emitted_file(vault):
    return Path(vault) / "_meta" / "observer" / "patterns.json"


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


def _draft(vault, group, quote):
    _, text, day, root = quote
    heads = ledger.template_headings(vault, "Pattern")
    cats = Counter(c for m in group["members"] for c in (ledger.read(m)[0].get("categories") or []) if c)
    top = cats.most_common(1)[0][0] if cats else ""
    derived = "".join(f'\n  - "[[{m.stem}]]"' for m in group["members"])
    blocks = [f"## {h}\n" for h in heads]
    if blocks:
        blocks[0] = f"## {heads[0]}\n\n> {text}\n\n— {day}, {Path(root).name}\n"
        if len(heads) > 3:
            blocks[3] = f"## {heads[3]}\n\n" + "\n".join(f"- [[{m.stem}]]" for m in group["members"]) + "\n"
    return (f"---\ntype: pattern\ncreated: {date.today().isoformat()}\nstatus: proposed\n"
            f"categories:\n  - \"{top}\"\nderived:{derived}\nrelated:\n---\n\n"
            + "\n".join(blocks) + f"\n<!-- pattern-key: {group['key']} -->\n")


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
        path = vault / "inbox" / f"{date.today().isoformat()}-pattern-{g['key']}.md"
        path.parent.mkdir(exist_ok=True)
        paths.write_atomic(path, _draft(vault, g, quote))
        written.append(g["key"])
    if written:
        _emitted_file(vault).parent.mkdir(parents=True, exist_ok=True)
        paths.write_atomic(_emitted_file(vault), json.dumps(sorted(done | set(written))) + "\n")
    return len(groups), len(written)
