"""Create a ledger where there is none. Refuses anything that already holds notes."""
import shutil
from pathlib import Path

from tenet import paths

TEMPLATE = paths.PLUGIN_ROOT / "vault-template"


def refusal(target):
    """Why target must not be written into, or None."""
    if not target.exists():
        return None
    if (target / ".obsidian").is_dir():
        return "it is already an Obsidian vault (.obsidian/ is there)"
    if any(target.rglob("*.md")):
        return "it already holds markdown files, at some depth"
    return None


def run(target=None):
    """Return (exit code, output lines)."""
    default, _ = paths.ledger()
    target = Path(target).expanduser() if target else default
    if not TEMPLATE.is_dir():
        return 1, [f"tenet: vault-template/ is missing from the plugin at {TEMPLATE} — the install is incomplete."]
    why = refusal(target)
    if why:
        return 1, [f"tenet: refusing to write into {target} — {why}.",
                   "This creates a ledger; it does not merge into one. Pass a different path for a second ledger."]
    shutil.copytree(TEMPLATE, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".obsidian"))
    for sub in ("inbox", "raw"):
        (target / sub).mkdir(exist_ok=True)
        (target / sub / ".gitkeep").touch()
    out = [f"tenet: ledger created at {target}", "",
           "Next: `git init` in it if you want history; decide something, then run /tenet:tenet-capture."]
    if target != default:
        out.append(f"This is not the configured path: set the ledger path in /plugin, or export TENET_LEDGER={target}.")
    return 0, out
