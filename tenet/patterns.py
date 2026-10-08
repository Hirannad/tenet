"""Pattern candidates: groups of accepted decisions that share a rationale.

Tooling only proposes. A pattern is the user's own insight, so nothing here writes one without a
verbatim quote of the user's, and the sweep merely lists the groups."""
import hashlib
from pathlib import Path

from tenet import ledger
from tenet.observer import textindex

THRESHOLD = 0.08  # cosine of two decisions' texts, on top of a `related` link between them
MIN_SIZE, MAX_SIZE = 3, 8
TERMS = 12  # shared terms kept per group


def _targets(text):
    return {ledger.link_target(t) for t in ledger.WIKILINK.findall(text)}


def _covered(vault, members):
    """A group a pattern already derives from is not a candidate any more."""
    names = {m.stem for m in members}
    for p in ledger.notes(vault):
        fm, _, _ = ledger.read(p)
        if fm.get("type") != "pattern":
            continue
        linked = _targets(p.read_text(encoding="utf-8", errors="replace"))
        if len(names & linked) >= 2:
            return True
    return False


def key(members):
    return hashlib.sha1("|".join(sorted(m.stem for m in members)).encode()).hexdigest()[:10]


def candidates(vault, threshold=THRESHOLD):
    """Return (decisions examined, [{members, terms, key}]). An edge needs both signals: the
    author linked the two in `related`, and their texts overlap. Related links alone chain the
    whole ledger into one component; text alone misses decisions that name an idea differently.
    Groups are the connected components of MIN_SIZE..MAX_SIZE members: a larger one is a topic,
    not a shared rationale, and is left to the topic check."""
    vault = Path(vault)
    docs, related = {}, {}
    for p in ledger.notes(vault):
        fm, block, body = ledger.read(p)
        if fm.get("type") == "decision" and fm.get("status") == "accepted":
            # Headings are template words every decision shares, so they would swamp the terms.
            prose = "\n".join(l for l in body.splitlines() if not l.startswith("## "))
            docs[p] = p.stem.replace("-", " ") + " " + prose
            related[p] = _targets("\n".join(ledger.raw_items(block, "related")))
    vec = textindex.vectors(docs)
    by_stem = {p.stem: p for p in docs}
    parent = {p: p for p in docs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    names = list(docs)
    for a in names:
        for stem in related[a]:
            b = by_stem.get(stem)
            if b and textindex.cosine(vec[a], vec[b]) >= threshold:
                parent[find(a)] = find(b)
    groups = {}
    for p in names:
        groups.setdefault(find(p), []).append(p)
    out = []
    for members in groups.values():
        if not MIN_SIZE <= len(members) <= MAX_SIZE or _covered(vault, members):
            continue
        # Terms several members use, heaviest first: what the group actually shares.
        need = max(2, -(-len(members) // 2))
        weight = {}
        for m in members:
            for t, w in vec[m].items():
                weight[t] = weight.get(t, 0.0) + w
        uses = {t: sum(1 for m in members if t in vec[m]) for t in weight}
        terms = sorted((t for t in weight if uses[t] >= need), key=weight.get, reverse=True)[:TERMS]
        out.append({"members": sorted(members), "terms": terms, "key": key(members)})
    return len(docs), sorted(out, key=lambda c: -len(c["members"]))


def render(vault):
    examined, found = candidates(vault)
    if not examined:
        return ["  not examined: no accepted decision to compare."]
    if not found:
        return [f"  {examined} accepted decision(s) compared (related link and cosine >= {THRESHOLD}); no group of {MIN_SIZE}-{MAX_SIZE}. A real zero."]
    out = [f"  {examined} accepted decision(s) compared (related link and cosine >= {THRESHOLD}); {len(found)} group(s). Propose as a question, never write the pattern."]
    for c in found:
        out.append(f"  [{c['key']}] " + ", ".join(m.stem for m in c["members"]))
        out.append(f"      shared terms: {' '.join(c['terms'][:8]) or '(none in common)'}")
    return out
