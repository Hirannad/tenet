"""Where things are. The only place that resolves the ledger path."""
import json
import os
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
CLI = PLUGIN_ROOT / "tenet" / "cli.py"
DEFAULT_LEDGER = "~/Claude/ledger"


def ledger():
    """Return (path, source): the plugin option wins, then TENET_LEDGER, then the default."""
    for var, source in (("CLAUDE_PLUGIN_OPTION_LEDGER", "userConfig"), ("TENET_LEDGER", "TENET_LEDGER")):
        value = os.environ.get(var)
        if value:
            return Path(value).expanduser(), source
    return Path(DEFAULT_LEDGER).expanduser(), "default"


def data_dir():
    """The harness-assigned plugin data directory, or TENET_DATA for tests and manual runs."""
    value = os.environ.get("CLAUDE_PLUGIN_DATA") or os.environ.get("TENET_DATA")
    return Path(value).expanduser() if value else None


def write_atomic(path, text, newline=None):
    """Write via a temporary file and rename, so a reader never sees half a file. newline=""
    writes line endings as given."""
    path = Path(path)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8", newline=newline) as f:
        f.write(text)
    os.replace(tmp, path)


def observer_dir(vault):
    """The observer's records, kept in the ledger because transcripts are gone after 30 days."""
    return Path(vault) / "_meta" / "observer"


def verdict_errors(data):
    """Where the Stop hook logs a failure it must not print, for the next session start to show."""
    return Path(data) / "verdict" / "errors.log"


def config_dir():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude").expanduser()


def memory_root():
    """Return (root or None, note): where auto memory lives, or None with the reason it is off.
    The default root holds one <project>/memory/ per repository; a relocated one is the memory
    directory itself."""
    if os.environ.get("CLAUDE_CODE_DISABLE_AUTO_MEMORY"):
        return None, "auto memory is off (CLAUDE_CODE_DISABLE_AUTO_MEMORY is set)"
    settings = config_dir() / "settings.json"
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return config_dir() / "projects", f"no readable {settings}, so a relocated memory directory could not be ruled out"
    if data.get("autoMemoryEnabled") is False:
        return None, f"auto memory is off (autoMemoryEnabled false in {settings})"
    if data.get("autoMemoryDirectory"):
        return Path(data["autoMemoryDirectory"]).expanduser(), "relocated by autoMemoryDirectory"
    return config_dir() / "projects", ""


def check_ledger(path, source, quiet_when_absent=False):
    """Return (usable, message). A configured path that is missing is an error; a missing
    default is a fresh install, which only the interactive entry points mention."""
    if not path.is_dir():
        if source != "default":
            return False, (
                f"TENET ERROR: the ledger path came from {source} and points at {path}, where "
                "nothing is. If the ledger moved, fix that setting. If it does not exist yet, "
                f"create it:\n\n  python3 {CLI} bootstrap {path}"
            )
        if quiet_when_absent:
            return False, None
        return False, (
            "tenet: no ledger yet. It is an ordinary directory of markdown files; create one "
            f"(it refuses to write into an existing one):\n\n  python3 {CLI} bootstrap\n\n"
            f"Pass a path to put it somewhere other than {path}, and set the same path in /plugin."
        )
    # APFS answers is_dir() case-insensitively; the directory listing does not.
    if path.name not in os.listdir(path.parent):
        return False, (
            f"TENET ERROR: ledger path {path} differs in case from the directory on disk. It "
            "works on APFS and fails on a case-sensitive filesystem. Fix the path."
        )
    return True, None
