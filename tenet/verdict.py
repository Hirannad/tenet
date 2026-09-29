"""The verdict at the resting point: at most once per session, when drafts wait and the work is
at rest, ask for one to four verdicts in a single AskUserQuestion call, then apply them without
the model touching frontmatter."""
import hashlib
import json
import os
import re
import subprocess
from datetime import date
from pathlib import Path

from tenet import ledger, paths, promote

MIN_WORK = 20
INTERACTIVE = ("claude-desktop", "cli")
LABELS = ("Accept", "Discard", "To memory", "Later")
TERMINAL = re.compile(r"<status>(completed|failed|stopped|killed)</status>")


def batch_size(backlog):
    """Verdicts to ask for: enough to drain a backlog, never more than one dialog holds."""
    for floor, k in ((12, 4), (6, 3), (2, 2), (1, 1)):
        if backlog >= floor:
            return k
    return 0


def _rows(transcript):
    rows = []
    with open(transcript, errors="replace") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    return rows


def _blocks(row):
    content = (row.get("message") or {}).get("content")
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def busy(payload):
    """Why this stop is not a resting point, or None when it is."""
    if payload.get("stop_hook_active") or os.environ.get("TENET_OBSERVER_RUN"):
        return "re-entry"
    transcript = payload.get("transcript_path")
    if not transcript or not os.path.isfile(transcript):
        return "no transcript"
    rows = _rows(transcript)
    entry = next((r["entrypoint"] for r in rows if r.get("entrypoint")), None)
    if entry not in INTERACTIVE:
        return "not interactive"
    first = next((r for r in rows if r.get("type") == "user" and isinstance((r.get("message") or {}).get("content"), str)), None)
    if first and first["message"]["content"].startswith("<scheduled-task"):
        return "scheduled"
    assistants = [r for r in rows if r.get("type") == "assistant"]
    if len(assistants) < MIN_WORK:
        return "little work"

    launched, finished, todos, tasks = {}, set(), None, {}
    for r in rows:
        # Completion notices arrive as user, attachment or queue-operation records alike.
        raw = json.dumps(r, ensure_ascii=False)
        if "<task-notification>" in raw and TERMINAL.search(raw):
            finished.update(re.findall(r"<(?:tool-use-id|task-id)>([^<]+)<", raw))
        for b in _blocks(r):
            name, args = b.get("name"), b.get("input") or {}
            if b.get("type") == "tool_use":
                if (name == "Agent" and args.get("run_in_background") is not False) or name == "Workflow" \
                        or (name == "Bash" and args.get("run_in_background")):
                    launched[b.get("id")] = {b.get("id")}
                if name == "TodoWrite":
                    todos = args.get("todos") or []
                if name == "TaskUpdate" and args.get("taskId") in tasks:
                    tasks[args["taskId"]] = args.get("status") or tasks[args["taskId"]]
            elif b.get("type") == "tool_result":
                result = r.get("toolUseResult") if isinstance(r.get("toolUseResult"), dict) else {}
                if isinstance(result.get("task"), dict) and result["task"].get("id"):
                    # Ids are reused once the list empties, so a new task resets the old one's status.
                    tasks[str(result["task"]["id"])] = "pending"
                if b.get("tool_use_id") in launched:
                    launched[b["tool_use_id"]].update(re.findall(r"agentId: (\w+)", json.dumps(b.get("content"))))
    # The harness lists in-flight work in the payload; older builds do not, so read the transcript.
    background = payload.get("background_tasks")
    running = bool(background) if background is not None else any(not (ids & finished) for ids in launched.values())
    if running or payload.get("session_crons"):
        return "background work"
    if todos and any(t.get("status") in ("pending", "in_progress") for t in todos):
        return "open todos"
    if any(status not in ("completed", "deleted") for status in tasks.values()):
        return "open tasks"
    last = _blocks(assistants[-1])
    if any(b.get("type") == "tool_use" and b.get("name") in ("AskUserQuestion", "ExitPlanMode") for b in last):
        return "waiting on the user"
    text = payload.get("last_assistant_message") or " ".join(b.get("text", "") for b in last if b.get("type") == "text")
    if str(text).strip().endswith("?"):
        return "waiting on the user"
    return None


def eligible(vault):
    """Drafts ready for a verdict: proposed, inside the caps, no literal placeholder."""
    conv = ledger.conventions()
    heading, _ = ledger.section_heading(vault)
    out = []
    for draft in ledger.md_files(Path(vault) / "inbox"):
        fm, _, body = ledger.read(draft)
        if fm.get("status") != "proposed" or "{{" in draft.read_text(encoding="utf-8", errors="replace"):
            continue
        lead = ledger.sections(body).get(heading)
        if ledger.words(body) > conv["cap_note_words"] or (fm.get("type") == "decision" and (lead is None or ledger.words(lead) > conv["cap_decision_words"])):
            continue
        out.append(draft)
    return out


def _digest(path):
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()


def _card(vault, draft):
    fm, _, body = ledger.read(draft)
    sections = list(ledger.sections(body).items())
    text = f"{fm.get('type', '?')} · {fm.get('created', '?')} · {draft.name}\n"
    for title, content in sections[:2]:
        content = re.sub(r"<!--.*?-->", "", content, flags=re.S).strip()
        text += f"\n## {title}\n{content}\n"
    return text[:1200]


def _state(data):
    d = Path(data) / "verdict"
    for sub in ("sessions", "tickets"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    return d


def _deferrals(data):
    try:
        return json.loads((_state(data) / "deferrals.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def gate(payload, vault, data):
    """The instruction to inject at this stop, or None. The session marker is written first,
    so a failing round cannot fire twice."""
    # Cheapest first: this runs after every response, and reading the transcript is the slow part.
    session = payload.get("session_id") or ""
    if not session or (_state(data) / "sessions" / session).exists():
        return None
    drafts = eligible(vault)
    k = batch_size(len(drafts))
    if not k or busy(payload):
        return None
    deferred = _deferrals(data)
    drafts.sort(key=lambda d: (-min(deferred.get(d.name, 0), 2), d.name))
    try:  # exclusive create: two hooks racing on one stop (the plugin can load twice) fire once
        with open(_state(data) / "sessions" / session, "x") as marker:
            marker.write(date.today().isoformat() + "\n")
    except FileExistsError:
        return None
    items, questions = [], []
    for i, draft in enumerate(drafts[:k], 1):
        title = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", draft.stem).replace("-", " ")
        question = f"{title}: verdict?"
        if any(it["question"] == question for it in items):  # AskUserQuestion needs unique texts
            question = f"{title} ({draft.name[:10]}): verdict?"
        card = _card(vault, draft)
        options = [
            {"label": "Accept", "description": "Goes into the ledger now.", "preview": card},
            {"label": "Discard", "description": "Removed from the inbox; recoverable from git, or from the plugin's data directory if never committed.", "preview": card},
            {"label": "To memory", "description": "Not a ledger note: saved to this project's auto memory instead.", "preview": card},
        ]
        if deferred.get(draft.name, 0) < 2:
            options.append({"label": "Later", "description": "Ask again at a later resting point.", "preview": card})
        questions.append({"question": question, "header": f"Draft {i}/{k}", "multiSelect": False, "options": options})
        items.append({"question": question, "draft": draft.name, "sha1": _digest(draft)})
    ticket = f"{date.today().isoformat()}-{session[:8]}"
    paths.write_atomic(_state(data) / "tickets" / f"{ticket}.json", json.dumps({"session": session, "items": items}, ensure_ascii=False))
    cmd = f'python3 "{paths.CLI}" verdict apply --ticket {ticket}'
    return (
        f"TENET VERDICT — resting point. {len(drafts)} ledger draft(s) are waiting; this round asks {k}.\n"
        "Call AskUserQuestion ONCE with exactly this questions array; do not rewrite labels, previews or question texts:\n"
        f"{json.dumps(questions, ensure_ascii=False)}\n"
        "If another Stop-hook message in this same stop asks you to name the session, add that naming question as the "
        "LAST question of this same call and drop the last draft question: never two dialogs in a row.\n"
        f"Then pass the answers through unchanged: {cmd} <<'JSON'\n"
        '{"answers": <the answers object>, "afk": <true if the dialog timed out>}\nJSON\n'
        "The command writes every status and moves every file; never edit frontmatter yourself. "
        "Finish with one sentence: what was accepted, discarded or routed, and how many drafts remain."
    )


def _log(vault, draft, verdict):
    log = Path(vault) / "_meta" / "observer" / "verdicts.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps({"date": date.today().isoformat(), "draft": draft, "verdict": verdict}, ensure_ascii=False) + "\n")


def set_status(path, value):
    """Rewrite the first status line of the frontmatter, and nothing else."""
    with open(path, encoding="utf-8", newline="") as f:  # keep CRLF files CRLF
        text = f.read()
    block, _ = ledger.split(text.replace("\r\n", "\n"))
    if not block:
        raise ValueError(f"{path} has no frontmatter")
    new_text, n = re.subn(r"^status:[^\r\n]*", f"status: {value}", text, count=1, flags=re.M)
    if not n:
        raise ValueError(f"{path} has no status line")
    tmp = Path(path).with_name(f".{Path(path).name}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(new_text)
    os.replace(tmp, path)


def _remove(vault, data, draft):
    """Take a draft out of the inbox without losing it: git keeps a tracked one, the data
    directory keeps one that was never committed."""
    rel = f"inbox/{draft.name}"
    tracked = subprocess.run(["git", "-C", str(vault), "ls-files", "--error-unmatch", rel], capture_output=True).returncode == 0
    if tracked:
        subprocess.run(["git", "-C", str(vault), "rm", "-q", "-f", rel], capture_output=True)
    if draft.exists():
        keep = _state(data) / "removed"
        keep.mkdir(exist_ok=True)
        os.replace(draft, keep / draft.name)


def apply(vault, data, ticket, result):
    """Map each answer to its draft and act on it. Returns output lines for the model."""
    try:
        spec = json.loads((_state(data) / "tickets" / f"{ticket}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [f"VERDICT REFUSED: no ticket {ticket}."]
    if result.get("afk"):
        return ["VERDICT: none applied — the dialog timed out, which is not a verdict."]
    answers = result.get("answers") or {}
    vault, deferred, out, counts = Path(vault), _deferrals(data), [], {}
    for item in spec["items"]:
        draft = vault / "inbox" / item["draft"]
        answer = answers.get(item["question"])
        if answer is None:
            continue
        if not draft.exists() or _digest(draft) != item["sha1"]:
            out.append(f"VERDICT REFUSED for {item['draft']}: it changed or moved since the question was asked.")
            continue
        if answer == "Accept":
            set_status(draft, "accepted")
            verdict = "accepted"
        elif answer == "Discard":
            _remove(vault, data, draft)
            verdict = "discarded"
        elif answer == "To memory":
            body = draft.read_text(encoding="utf-8")
            _remove(vault, data, draft)
            out.append(f"TO MEMORY: save the substance of {item['draft']} as a memory of the project it came from, "
                       f"in that project's auto-memory directory, then say where. Its text:\n{body}")
            verdict = "memory"
        elif answer == "Later":
            deferred[item["draft"]] = deferred.get(item["draft"], 0) + 1
            verdict = "later"
        else:
            out.append(f"EDIT REQUESTED for {draft}: {answer}\nApply it to the body with Edit; never touch status. "
                       "The draft stays proposed and is asked again at a later resting point.")
            verdict = "edit"
        counts[verdict] = counts.get(verdict, 0) + 1
        if verdict != "later":
            _log(vault, item["draft"], verdict)
    paths.write_atomic(_state(data) / "deferrals.json", json.dumps(deferred))
    (_state(data) / "tickets" / f"{ticket}.json").unlink()  # a ticket answers once
    moved = [line for line in promote.run(vault) if line.startswith("  - ") and "(accepted)" in line] if counts.get("accepted") else []
    left = len(eligible(vault))
    summary = ", ".join(f"{n} {v}" for v, n in counts.items()) or "nothing answered"
    return [*out, f"VERDICT: {summary}; {len(moved)} promoted; {left} draft(s) left."]
