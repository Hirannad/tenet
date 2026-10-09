"""Running the observer: the scan itself, launching it in the background, and its status."""
import fcntl
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

from tenet import paths
from tenet.observer import brief, pattern_drafts, transcripts, usage

STALE_DAYS = 7
RETRY_SECONDS = 24 * 3600
NEW_NOTE_RETRY_SECONDS = 600


def _status_file(data):
    return Path(data) / "observer" / "status.env"


def status(data):
    try:
        lines = _status_file(data).read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    return dict(line.split("=", 1) for line in lines if "=" in line)


def _write_status(data, **values):
    current = status(data)
    current.update({k: str(v) for k, v in values.items()})
    f = _status_file(data)
    f.parent.mkdir(parents=True, exist_ok=True)
    paths.write_atomic(f, "".join(f"{k}={v}\n" for k, v in sorted(current.items())))


def scan(vault, data):
    """One full pass. Takes a lock and returns None without work if another pass holds it."""
    lock_path = Path(data) / "observer" / "lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return None
        _write_status(data, last_attempt=int(time.time()))
        try:
            sessions, oldest = transcripts.sessions(30)
            new_uses = usage.update(vault, sessions, oldest)
            count = brief.write_all(vault, data, sessions, date.today().isoformat())
            groups, drafts = pattern_drafts.write(vault, sessions)
        except Exception as exc:  # noqa: BLE001
            _write_status(data, error=f"{type(exc).__name__}: {exc}"[:300])
            raise
        _write_status(data, last_ok=int(time.time()), error="", sessions=len(sessions), projects=count, new_uses=new_uses,
                      pattern_groups=groups, pattern_drafts=drafts)
        return len(sessions), count, new_uses


def spawn(data):
    """Start a scan detached from the hook, so session start never waits for it. The launch is
    recorded first, so a scan that dies before writing anything still shows up as missing."""
    _write_status(data, spawned=int(time.time()))
    subprocess.Popen([sys.executable, str(paths.CLI), "observe", "scan", "--quiet"], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)


def due(vault, data, matched):
    """Why a background scan should start now, or None."""
    st = status(data)
    now = time.time()
    last_ok, last_attempt = float(st.get("last_ok") or 0), float(st.get("last_attempt") or 0)
    if not last_ok:
        return "no brief computed yet" if now - last_attempt > NEW_NOTE_RETRY_SECONDS else None
    if now - last_ok > STALE_DAYS * 86400 and now - last_attempt > RETRY_SECONDS:
        return "stale"
    if not matched and now - last_attempt > RETRY_SECONDS:
        return "new project"
    built = (Path(data) / "briefs" / "index.tsv")
    # A rename into the root keeps the file's mtime but changes the directory's.
    newest = max([Path(vault).stat().st_mtime, *(p.stat().st_mtime for p in Path(vault).glob("*.md"))])
    if built.exists() and newest > built.stat().st_mtime and now - last_attempt > NEW_NOTE_RETRY_SECONDS:
        return "notes changed"
    return None


def banners(vault, data):
    """Lines that make a stale or failing observer impossible to miss."""
    st, now, out = status(data), time.time(), []
    last_ok = float(st.get("last_ok") or 0)
    spawned, attempt = float(st.get("spawned") or 0), float(st.get("last_attempt") or 0)
    if spawned and attempt < spawned and now - spawned > 120:
        out.append(f"TENET OBSERVER FAILING: the background scan launched {date.fromtimestamp(spawned).isoformat()} never recorded a start. Run `{paths.command(vault, data, 'observe scan')}` by hand to see why.")
    if st.get("error"):
        out.append(f"TENET OBSERVER FAILING: {st['error']}")
    errors = paths.verdict_errors(data)
    if errors.is_file() and errors.stat().st_size and now - errors.stat().st_mtime < STALE_DAYS * 86400:
        out.append(f"TENET VERDICT GATE: {len(errors.read_text(errors='replace').splitlines())} error(s) logged in {errors}")
    if last_ok and now - last_ok > STALE_DAYS * 86400:
        out.append(f"TENET BRIEF STALE: last successful scan {date.fromtimestamp(last_ok).isoformat()} ({int((now - last_ok) // 86400)} days ago)")
    return out
