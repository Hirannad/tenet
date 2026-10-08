"""The inventory the weekly sweep works from, so the model composes no shell of its own."""
import json
import os
import re
import subprocess
import time
from collections import Counter
from pathlib import Path

from tenet import ledger, patterns, paths

WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")


def _feedback():
    root, note = paths.memory_root()
    if root is None:
        return [f"  status: {note}. Nothing was read — not the same as no deviations."]
    suffix = f" ({note})" if note else ""
    if not root.is_dir():
        return [f"  status: nothing at {root}{suffix} — no record to read, which is not a clean record."]
    notes = sorted(p for p in root.rglob("*.md") if p.is_file())
    hits = []
    for f in notes:
        block = ledger.split(f.read_text(encoding="utf-8", errors="replace"))[0]
        # type may sit under a nested metadata: key, which the flat parser does not descend into.
        if re.search(r"^\s*type:\s*feedback", block, re.M):
            hits.append((f, ledger.frontmatter(block).get("description") or "(no description)"))
    if not hits:
        return [f"  status: {root} holds {len(notes)} memory note(s){suffix}, none of type feedback. A real zero."]
    out = [f"  status: {len(hits)} feedback note(s) under {root}{suffix}; auto memory is per-repository, so these span projects."]
    for f, desc in hits:
        project = f.relative_to(root).parts[0] if len(f.relative_to(root).parts) > 1 else "."
        out.append(f"  {project:<34} {f.name:<36} {desc}")
    return out


def render(vault):
    vault = Path(vault)
    conv = ledger.conventions()
    heading, notice = ledger.section_heading(vault)
    roots = ledger.notes(vault)
    drafts = ledger.md_files(vault / "inbox")
    parsed = {n: ledger.read(n) for n in roots}
    gotchas = sum(1 for fm, _, _ in parsed.values() if fm.get("type") == "gotcha")
    raw = [p for p in (vault / "raw").glob("*") if p.is_file() and p.name != ".gitkeep"]

    out = [f"Ledger: {vault}", f"Notes: {len(roots)}", f"Drafts pending: {len(drafts)}",
           f"Gotchas: {gotchas}", f"Raw files: {len(raw)}", ""]

    out.append("--- decisions with a revisit condition ---")
    out += [f"  {n.name}: {fm['revisit']}" for n, (fm, _, _) in parsed.items() if fm.get("revisit")]
    out += ["", "--- drafts older than 14 days ---"]
    out += [f"  inbox/{d.name}" for d in drafts if time.time() - d.stat().st_mtime > 14 * 86400]

    out += ["", "--- type + status per root note ---"]
    out += [f"  {n.name:<52} type={fm.get('type', ''):<9} status={fm.get('status', '')}" for n, (fm, _, _) in parsed.items()]

    out += ["", f"--- word counts over the caps ({conv['cap_note_words']} body / {conv['cap_decision_words']} {heading}) ---"]
    for n in [*roots, *drafts]:
        fm, block, body = parsed.get(n) or ledger.read(n)
        out += [f"  {n.name}: {detail}" for kind, detail in ledger.cap_problems(fm, block, body, conv, heading) if kind != "unexpanded"]
    if notice:
        out.append(f"  {notice}")

    out += ["", "--- categories tally ---"]
    tally = Counter()
    for fm, _, _ in parsed.values():
        cats = fm.get("categories")
        tally.update(WIKILINK.sub(r"\1", c) for c in (cats if isinstance(cats, list) else []) if c)
    out += [f"  {count:>4} {cat}" for cat, count in tally.most_common()]

    out += ["", "--- dead wikilinks ---"]
    targets = set()
    for f in [*roots, *ledger.md_files(vault / "_meta"), *drafts]:
        targets |= set(WIKILINK.findall(f.read_text(encoding="utf-8", errors="replace")))
    existing = {p.stem for d in (vault, vault / "_meta", vault / "inbox") for p in ledger.md_files(d)}
    out += [f"  {t}" for t in sorted(targets) if t.split("|")[0].split("#")[0] not in existing]

    out += ["", "--- pattern candidates (decisions that may share an insight) ---", *patterns.render(vault)]

    out += ["", "--- process deviations (native auto memory, type: feedback) ---", *_feedback()]

    out += ["", "--- git status ---"]
    status = subprocess.run(["git", "-C", str(vault), "status", "--short"], capture_output=True, text=True)
    out += [f"  {line}" for line in status.stdout.splitlines()]
    return out
