"""The session-start list until the per-project brief replaces it: every universal note
plus the topic notes bound to this directory, capped, and loud about what the cap drops."""
import os
import re
from pathlib import Path

from tenet import ledger

MAX_LIST = 40
_BINDING = re.compile(r"`([^`]+)`[^`]*→\s*(.+)$")


def bindings(path):
    """(path, topics) for each live binding; fenced and commented-out examples are not live."""
    out, fence, comment = [], False, False
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    for line in lines:
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if "<!--" in line:
            comment = True
        if comment:
            comment = "-->" not in line
            continue
        m = _BINDING.search(line)
        if m:
            out.append((m.group(1), m.group(2).strip()))
    return out


def bound_topics(vault, cwd):
    """Topics of the longest binding that is a prefix of cwd."""
    # Both sides resolved: the hook's cwd is the physical path, a binding may name a symlink.
    cwd = os.path.realpath(cwd)
    best, topics = -1, ""
    for bpath, btopics in bindings(Path(vault) / "_meta" / "bindings.md"):
        full = os.path.realpath(os.path.expanduser(bpath))
        if (cwd == full or cwd.startswith(full.rstrip("/") + "/")) and len(full) > best:
            best, topics = len(full), btopics
    return topics


def _describe(note, fm):
    line = f"- [[{note.stem}]]"
    if fm.get("type"):
        line += f" ({fm['type']}" + (f", {fm['status']}" if fm.get("status") else "") + ")"
    if fm.get("revisit"):
        line += f" — revisit when: {fm['revisit']}"
    return line


def _capped(entries, label):
    out = entries[:MAX_LIST]
    if len(entries) > MAX_LIST:
        out.append(f"({len(entries) - MAX_LIST} further {label} note(s) withheld — MAX_LIST={MAX_LIST}. Ask for them by name.)")
    return out


def render(vault, cwd):
    vault = Path(vault)
    topics = bound_topics(vault, cwd)
    names = [t.strip().strip("[]") for t in topics.split(",") if t.strip()]
    universal, topical = [], []
    for note in ledger.notes(vault):
        fm, block, _ = ledger.read(note)
        if fm.get("type") == "gotcha":
            continue
        if fm.get("scope") == "universal":
            universal.append(_describe(note, fm))
        elif names and any(n in block for n in names):
            topical.append(_describe(note, fm))
    if not universal and not topical and not topics:
        return []
    out = [f"LEDGER: {vault}"]
    out.append(f"BOUND TOPICS: {topics}" if topics else "BOUND TOPICS: none (this directory is not bound; topic notes are out of scope)")
    if universal:
        out += ["", "## Always in scope — methodology, architecture, structure", *_capped(universal, "universal")]
    if topical:
        out += ["", "## Topic notes in scope", *_capped(topical, "topic")]
    pending = len(ledger.md_files(vault / "inbox"))
    if pending:
        out += ["", f"{pending} draft(s) awaiting review in inbox/. Run /tenet:tenet-capture review."]
    return out
