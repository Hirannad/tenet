"""The per-project brief: which accepted notes matter where, computed out of band so the
session-start hook only reads a file.

Relevance is content match between a note and what the user asked in that project over the
last 30 days. Citations would be circular (what is shown gets cited), so they do not score."""
import hashlib
import math
import os
import re
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from tenet import ledger, paths
from tenet.observer import textindex, transcripts

THRESHOLD = 0.10
PROJECT_MAX, CORE_MAX, MIN_CORE_SESSIONS = 20, 10, 3
FRESH_DAYS = 14
BUDGET = {"project": 2600, "core": 800, "fresh": 400}
MAX_BYTES = 4096
TYPES = {"decision": "d", "pattern": "p", "gotcha": "g", "open": "o"}


def _first_sentence(text, limit=100):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = " ".join(text.split())
    sentence = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    return sentence if len(sentence) <= limit else sentence[: limit - 1].rstrip() + "…"


def corpus(vault):
    """{slug: note} for accepted notes of the types a brief shows."""
    heading, _ = ledger.section_heading(vault)
    out = {}
    for path in ledger.notes(vault):
        fm, _, body = ledger.read(path)
        if fm.get("status") != "accepted" or fm.get("type") not in TYPES:
            continue
        sections = ledger.sections(body)
        lead = sections.get(heading) or next(iter(sections.values()), "")
        title = ledger.title(path.stem)
        links = " ".join(v for k in ("categories", "related") for v in ledger.listed(fm, k))
        terms = Counter()
        for text, weight in ((title, 3), (lead, 2), (fm.get("revisit") or "", 1.5), (body, 1), (links, 1)):
            for token, n in Counter(textindex.tokens(text)).items():
                terms[token] += n * weight
        out[path.stem] = {"type": fm["type"], "created": fm.get("created") or "", "lead": _first_sentence(lead), "terms": terms}
    return out


def _profile(root):
    """Headings of the repo's own CLAUDE.md and README, so a project with few prompts still has words."""
    words = []
    for name in ("CLAUDE.md", "README.md"):
        try:
            text = (Path(root) / name).read_text(encoding="utf-8", errors="replace")[:20000]
        except OSError:
            continue
        words += [line.lstrip("#").strip() for line in text.splitlines() if line.startswith("#")]
    return " ".join(words)


def projects(sessions):
    """{root: {"sessions": n, "prompts": n, "text": str}} from the scanned sessions."""
    out = {}
    for s in sessions:
        p = out.setdefault(s["root"], {"sessions": 0, "prompts": 0, "parts": [], "paths": set()})
        p["sessions"] += 1
        p["prompts"] += len(s["prompts"])
        p["parts"] += s["prompts"] + s["asked"]
        p["paths"].update(s["paths"])
    for root, p in out.items():
        p["text"] = "\n".join(p.pop("parts") + sorted(p.pop("paths")) + [_profile(root)])
    return out


def score(notes, projs):
    """{root: {slug: cosine}}."""
    nv = textindex.vectors({k: n["terms"] for k, n in notes.items()})
    pv = textindex.vectors({r: p["text"] for r, p in projs.items()})
    return {r: {k: textindex.cosine(nv[k], pv[r]) for k in notes} for r in projs}


def core(notes, projs, scores):
    """The decisions most broadly relevant across projects, weighted by how much each is used."""
    eligible = [k for k, n in notes.items() if n["type"] in ("decision", "pattern")]
    roots = [r for r, p in projs.items() if p["sessions"] >= MIN_CORE_SESSIONS]
    if not eligible or not roots:
        return []
    acc = Counter()
    for r in roots:
        # Only notes relevant in this project take part: rank alone would crown irrelevant ones.
        ranked = sorted((k for k in eligible if scores[r][k] >= THRESHOLD), key=lambda k: scores[r][k], reverse=True)
        weight = math.sqrt(projs[r]["sessions"])
        for i, k in enumerate(ranked):
            acc[k] += weight * (1 - i / max(len(ranked), 1))
    return [k for k, _ in sorted(acc.items(), key=lambda kv: (-kv[1], kv[0]))[:CORE_MAX]]


def _section(title, items, budget, limit):
    """Up to `limit` lines within `budget` bytes, and a count of every eligible item left out."""
    lines, used = [], 0
    for line in items[:limit]:
        if used + len(line.encode()) + 1 > budget:
            break
        lines.append(line)
        used += len(line.encode()) + 1
    if len(items) > len(lines):
        lines.append(f"(+{len(items) - len(lines)} more withheld; ask by name)")
    return ["", f"## {title}", *lines] if lines else []


def render(vault, root, notes, projs, scores, core_list, scanned):
    line = lambda k: f"- [[{k}]] · {TYPES[notes[k]['type']]} · {notes[k]['lead']}"
    shown, out = set(), [f"LEDGER: {vault}"]
    proj = projs.get(root)
    if root is None:
        out.append(f"TENET BRIEF · scan {scanned} · no project match for this directory")
    else:
        out.append(f"TENET BRIEF · {root} · scan {scanned} · {proj['sessions']} session(s), {proj['prompts']} prompt(s) read · {len(notes)} notes scored")
        ranked = sorted(notes, key=lambda k: scores[root][k], reverse=True)
        hits = [k for k in ranked if scores[root][k] >= THRESHOLD * (1.5 if notes[k]["type"] == "gotcha" else 1)]
        if hits:
            section = _section("This project", [line(k) for k in hits], BUDGET["project"], PROJECT_MAX)
            out += section
            shown.update(k for k in hits if any(f"[[{k}]]" in s for s in section))
        else:
            out.append(f"project matches: 0 of {len(notes)} notes above threshold ({proj['sessions']} session(s) read)")
    out += _section("Core (computed across projects)", [line(k) for k in core_list if k not in shown], BUDGET["core"], CORE_MAX)
    shown.update(core_list)
    since = (date.today() - timedelta(days=FRESH_DAYS)).isoformat()
    fresh = sorted((k for k, n in notes.items() if n["created"] >= since and k not in shown), reverse=True)
    out += _section(f"Fresh (last {FRESH_DAYS} days)", [line(k) for k in fresh], BUDGET["fresh"], len(fresh))
    text = "\n".join(out)
    if len(text.encode()) > MAX_BYTES:
        while len(text.encode()) > MAX_BYTES - 80:
            text = text[: text.rfind("\n")]
        text += f"\n(brief cut at the {MAX_BYTES}-byte cap; ask for a note by name)"
    return text + "\n"


def write_all(vault, data, sessions, scanned):
    """Write one brief per project plus _global.md and index.tsv; return the project count."""
    notes = corpus(vault)
    projs = projects(sessions)
    scores = score(notes, projs) if notes and projs else {r: {} for r in projs}
    core_list = core(notes, projs, scores)
    out = Path(data) / "briefs"
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for root in projs:
        name = re.sub(r"[^A-Za-z0-9]+", "-", Path(root).name).strip("-") + "-" + hashlib.sha1(root.encode()).hexdigest()[:6] + ".md"
        paths.write_atomic(out / name, render(vault, root, notes, projs, scores, core_list, scanned))
        # A git root covers its subdirectories; a plain directory covers only itself.
        kind = "git" if (Path(root) / ".git").exists() else "dir"
        index.append(f"{root}\t{name}\t{kind}\n")
    paths.write_atomic(out / "_global.md", render(vault, None, notes, projs, scores, core_list, scanned))
    paths.write_atomic(out / "index.tsv", "".join(sorted(index)))
    return len(projs)


def lookup(data, cwd):
    """The brief for cwd: the longest indexed root that contains it (a worktree is looked up by
    its main repository), else _global.md. Returns (text or None, matched)."""
    out = Path(data) / "briefs"
    try:
        rows = [r.split("\t") for r in (out / "index.tsv").read_text(encoding="utf-8").splitlines() if r]
    except OSError:
        return None, False
    best, name = "", None
    for probe in {cwd, os.path.realpath(transcripts.root_of(cwd))}:
        for root, file, *kind in rows:
            inside = probe.startswith(root.rstrip("/") + "/") and (kind or ["git"])[0] == "git"
            if (probe == root or inside) and len(root) > len(best):
                best, name = root, file
    try:
        text = (out / (name or "_global.md")).read_text(encoding="utf-8")
    except OSError:
        return None, False
    return (text or None), name is not None
