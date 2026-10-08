"""Reading session transcripts: what the user asked, where, and what the assistant cited.

Authorship comes from record fields, never from a model: a prompt is the user's only when
origin.kind says so, it is not meta, and it is not a harness wrapper."""
import datetime as dt
import json
import os
from pathlib import Path

from tenet import paths

WRAPPERS = ("<scheduled-task", "<task-notification", "<command-", "<local-command", "Caveat:", "<system-reminder")
SYNTHETIC = ("/private/tmp", "/private/var/folders", "/tmp/")
PATH_KEYS = ("file_path", "path", "notebook_path")


def root_of(cwd):
    """The git root a directory belongs to (a worktree maps to its main repository), else cwd."""
    p = Path(cwd)
    for d in (p, *p.parents):
        git = d / ".git"
        if git.is_dir():
            return str(d)
        if git.is_file():
            target = git.read_text(errors="replace").partition("gitdir:")[2].strip()
            if "/.git/worktrees/" in target:
                return target.split("/.git/worktrees/")[0]
            return str(d)
    return str(p)


def _text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def rows(path):
    """A transcript's records; a line that does not parse is skipped."""
    out = []
    with open(path, errors="replace") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def _user_texts(records):
    """(record, text) for each user record that carries text rather than a tool result."""
    for r in records:
        content = (r.get("message") or {}).get("content")
        if r.get("type") != "user" or (isinstance(content, list) and any(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in content)):
            continue
        text = _text(content).strip()
        if text:
            yield r, text


def is_scheduled(records):
    """A scheduled task's session opens with the harness wrapper, not a person."""
    return next((t for _, t in _user_texts(records)), "").startswith("<scheduled-task")


def read(path):
    """One session as a dict: cwd, scheduled, human prompts, AskUserQuestion text,
    touched file paths, and the assistant's own text."""
    records = rows(path)
    s = {"id": Path(path).stem, "cwd": next((r["cwd"] for r in records if r.get("cwd")), ""),
         "scheduled": is_scheduled(records), "asked": [], "paths": [], "assistant": []}
    for r in records:
        content = (r.get("message") or {}).get("content")
        if r.get("type") != "assistant" or not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text":
                s["assistant"].append(b.get("text", ""))
            elif b.get("type") == "tool_use":
                args = b.get("input") or {}
                s["paths"] += [str(args[k]) for k in PATH_KEYS if isinstance(args.get(k), str)]
                if b.get("name") == "AskUserQuestion":
                    for q in args.get("questions") or []:
                        s["asked"].append(" ".join([q.get("question", "")] + [
                            f"{o.get('label', '')} {o.get('description', '')}" for o in q.get("options") or []]))
    s["prompts"] = [t for r, t in _user_texts(records)
                    if (r.get("origin") or {}).get("kind") == "human" and not r.get("isMeta") and not t.startswith(WRAPPERS)]
    return s


def sessions(days=30):
    """Top-level sessions touched within `days`, synthetic and scheduled ones left out.
    Returns (sessions, oldest file date seen) so callers can say how far back they looked."""
    root = paths.config_dir() / "projects"
    cutoff = dt.datetime.now().timestamp() - days * 86400
    out, oldest = [], None
    for f in root.glob("*/*.jsonl"):
        mtime = f.stat().st_mtime
        oldest = mtime if oldest is None else min(oldest, mtime)
        if mtime < cutoff:
            continue
        s = read(f)
        if not s["cwd"] or s["scheduled"] or s["cwd"].startswith(SYNTHETIC):
            continue
        s["root"] = os.path.realpath(root_of(s["cwd"]) if os.path.isdir(s["cwd"]) else s["cwd"])
        s["date"] = dt.date.fromtimestamp(mtime).isoformat()
        out.append(s)
    return out, (dt.date.fromtimestamp(oldest).isoformat() if oldest else None)
