"""Which notes were used, persisted in the ledger because transcripts are gone after 30 days.

A use is a note's slug in the assistant's text in a work session, or a new draft linking the
note in `related`. Sessions in the ledger repository itself are not work: reviewing notes
mentions them all."""
import json
import re
from datetime import date, timedelta
from pathlib import Path

from tenet import ledger, paths

KEEP_DAYS = 180


def _files(vault):
    d = paths.observer_dir(vault)
    return d / "usage.jsonl", d / "state.json"


def _read(vault):
    """(events, unparseable lines). A damaged line is kept verbatim, never dropped with the rest."""
    log, _ = _files(vault)
    try:
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return [], []
    events, bad = [], []
    for line in lines:
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            if not isinstance(e, dict) or not {"date", "note", "source"} <= e.keys():
                raise ValueError
            events.append(e)
        except ValueError:
            bad.append(line)
    return events, bad


def load(vault):
    return _read(vault)[0]


def measured_since(vault):
    _, state = _files(vault)
    try:
        return json.loads(state.read_text(encoding="utf-8")).get("measured_since")
    except (OSError, ValueError):
        return None


def update(vault, sessions, oldest):
    """Append the uses these sessions show and return how many were new."""
    vault = Path(vault)
    log, state = _files(vault)
    log.parent.mkdir(parents=True, exist_ok=True)
    # Only dated knowledge notes: a hub called "Tools" or the README would match ordinary prose.
    slugs = {n.stem for n in ledger.notes(vault) if re.match(r"\d{4}-\d{2}-\d{2}-", n.stem)}
    pattern = re.compile("|".join(re.escape(s) for s in sorted(slugs, key=len, reverse=True))) if slugs else None
    events, bad = _read(vault)
    seen = {(e["note"], e["source"]) for e in events}
    ledger_root = str(vault.resolve())
    fresh = []
    for s in sessions:
        if pattern is None or s["root"] == ledger_root or s["root"].startswith(ledger_root + "/"):
            continue
        for slug in set(pattern.findall("\n".join(s["assistant"]))):
            if (slug, s["id"]) not in seen:
                fresh.append({"date": s["date"], "note": slug, "project": s["root"], "source": s["id"]})
                seen.add((slug, s["id"]))
    for draft in ledger.md_files(vault / "inbox"):
        fm, _, _ = ledger.read(draft)
        for link in ledger.listed(fm, "related"):
            m = ledger.WIKILINK.search(link)
            note = m and ledger.link_target(m.group(1))
            if note in slugs and (note, draft.name) not in seen:
                fresh.append({"date": fm.get("created") or date.today().isoformat(), "note": note,
                              "project": "draft", "source": draft.name})
                seen.add((note, draft.name))
    cutoff = (date.today() - timedelta(days=KEEP_DAYS)).isoformat()
    kept = [e for e in events + fresh if e["date"] >= cutoff]
    body = "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in sorted(kept, key=lambda e: e["date"]))
    paths.write_atomic(log, body + "".join(line + "\n" for line in bad))
    if measured_since(vault) is None and oldest:
        paths.write_atomic(state, json.dumps({"measured_since": oldest}) + "\n")
    return len(fresh)
