"""Inbox state for a capture or review run."""
from pathlib import Path

from tenet import ledger


def render(vault):
    vault = Path(vault)
    drafts = ledger.md_files(vault / "inbox")
    out = [f"Ledger: {vault}", f"Drafts pending: {len(drafts)}"]
    out += [f"  - {d.name}" for d in drafts]
    out.append(f"Existing notes: {len(ledger.notes(vault))}")
    return out
