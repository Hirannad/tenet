"""The mechanical half of the review loop: move reviewed drafts out of inbox/ and report
what needs a human. Silent when there is nothing to say."""
import os
import re
import subprocess
import time
from pathlib import Path

from tenet import ledger

WIKILINK = re.compile(r'^"\[\[[^\]]+\]\]"$')


def _git(vault, *args):
    return subprocess.run(["git", "-C", str(vault), *args], capture_output=True, text=True)


def _move(vault, draft):
    if _git(vault, "rev-parse", "--git-dir").returncode == 0:
        if _git(vault, "mv", f"inbox/{draft.name}", draft.name).returncode == 0:
            return
    os.rename(draft, Path(vault) / draft.name)


def run(vault):
    vault = Path(vault)
    inbox = vault / "inbox"
    if not inbox.is_dir():
        return [f"TENET ERROR: inbox/ missing under {vault}"]
    conv = ledger.conventions()
    heading, notice = ledger.section_heading(vault)
    found = {k: [] for k in ("promoted", "invalid", "toolong", "nosection", "unexpanded", "categories")}

    for draft in ledger.md_files(inbox):
        try:
            fm, _, body = ledger.read(draft)
        except OSError as exc:
            found["invalid"].append(f"  - {draft.name} — unreadable: {exc}")
            continue
        status, kind = fm.get("status") or "", fm.get("type")
        if kind == "decision":
            text = ledger.sections(body).get(heading)
            if text is None:
                found["nosection"].append(f"  - {draft.name} — no '## {heading}' section")
            elif ledger.words(text) > conv["cap_decision_words"]:
                found["toolong"].append(f"  - {draft.name} — ## {heading}: {ledger.words(text)} words (max {conv['cap_decision_words']})")
        if kind in ("decision", "gotcha") and ledger.words(body) > conv["cap_note_words"]:
            found["toolong"].append(f"  - {draft.name} — whole note: {ledger.words(body)} words (max {conv['cap_note_words']})")
        placeholder = re.search(r"\{\{[^}]*\}\}", draft.read_text(encoding="utf-8", errors="replace"))
        if placeholder:
            found["unexpanded"].append(f"  - {draft.name} — {placeholder.group(0)} left literal")
        if status not in conv["statuses"]:
            found["invalid"].append(f"  - {draft.name} — status: {status or '(missing)'}")
            continue
        if status in conv["keep_in_inbox"]:
            continue
        if (vault / draft.name).exists():
            found["invalid"].append(f"  - {draft.name} — a note of that name already exists in the ledger root")
            continue
        _move(vault, draft)
        found["promoted"].append(f"  - {draft.name} ({status})")

    # A category is a hub: a quoted wikilink to a root note of that name (#13). templates/ is
    # skipped: its values are placeholders.
    hubs = {p.stem for p in ledger.md_files(vault)}
    for note in [*ledger.md_files(vault), *ledger.md_files(inbox), *ledger.md_files(vault / "raw"), *ledger.md_files(vault / "_meta")]:
        _, block, _ = ledger.read(note)
        for item in ledger.raw_items(block, "categories"):
            if not WIKILINK.match(item):
                found["categories"].append(f"  - {note.relative_to(vault)} — {item} (not a quoted wikilink)")
            elif item[3:-3].split("|")[0].split("#")[0] not in hubs:
                found["categories"].append(f"  - {note.relative_to(vault)} — {item} (no hub note of that name in the ledger root)")

    digests = [p for p in ledger.md_files(vault / "_meta") if p.name.startswith("maintenance-")]
    stale = ""
    if not digests:
        stale = "never run"
    elif time.time() - digests[-1].stat().st_mtime > 7 * 86400:
        stale = "last run " + digests[-1].stem.replace("maintenance-", "")

    out = []
    for key, title in (
        ("promoted", "Promoted to the ledger root:"),
        ("invalid", f"Needs attention — left in inbox/ (valid statuses: {' '.join(conv['statuses'])}):"),
        ("toolong", "Over the length caps — rewrite or split before asking for a verdict:"),
        ("nosection", f"Decision drafts the {conv['cap_decision_words']}-word cap could not check:"),
        ("unexpanded", "Template placeholder left literal — Obsidian expands these, the agent path does not:"),
        ("categories", "Category value(s) that resolve to no hub:"),
    ):
        if found[key]:
            out += [title, *found[key]]
    if found["nosection"] and notice:
        out.append(notice)
    if stale:
        out.append(f"Maintenance is due ({stale}). Run /tenet:tenet-sweep.")
    return ["TENET INBOX", *out] if out else []
