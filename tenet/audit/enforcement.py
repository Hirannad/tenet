"""Does every rule in the global CLAUDE.md carry a row in the user's enforcement table?

Prints three numbers: unmarked rules (the defect), orphan rows (the table went stale), empty
cells. Reports only and always exits 0: a missing table is a finding, not a failure.

Options: --rules FILE (default: <config dir>/CLAUDE.md, or $CLAUDE_MD),
         --table FILE (default: <config dir>/enforcement.md, or $ENFORCEMENT_TABLE).
"""
import os
import re
import sys

from tenet import paths

SECTION, HEADER = "## The table", "Rule"
WS = "[ \t\n\r\f\v]"
# The alignment row may carry colons (`---`, `:--`, `--:`, `:-:`); a user copying either style
# must not get a permanent orphan-row alarm.
SKIP_CELL = re.compile(f"{WS}*({HEADER}|:?-+:?){WS}*")
REFERENCES = paths.PLUGIN_ROOT / "skills" / "tenet-audit" / "references"


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace", newline="") as fh:
            return fh.read()
    except OSError:
        return None


def norm(line):
    """Identical on both sides: drop markdown noise and the list bullet, collapse whitespace,
    lowercase, keep 40 characters, so long rules stay readable in the table and still match."""
    s = re.sub(r"[*`_]", "", line)
    s = re.sub(f"^{WS}*-{WS}*", "", s)
    s = re.sub(f"{WS}+", " ", s)
    s = s[1:] if s.startswith(" ") else s
    return s.rstrip(" ").lower()[:40]


def _normed(lines):
    return sorted({n for n in map(norm, lines) if n})


def rules(text):
    """Top-level `- ` bullets outside fenced code."""
    out, fenced = [], False
    for line in text.split("\n"):
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("- "):
            out.append(line)
    return _normed(out)


def table_rows(text):
    """The rows under the table's own heading; prose and other tables are not rules."""
    out, inside = [], False
    for line in text.split("\n"):
        if line == SECTION:
            inside = True
            continue
        if inside and line.startswith("## "):
            inside = False
        if inside and line.startswith("|"):
            out.append(line)
    return out


def _cells(row):
    fields = row.split("|")
    return (fields[1] if len(fields) > 1 else ""), (fields[2] if len(fields) > 2 else "")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cdir = str(paths.config_dir())
    claude_md = os.environ.get("CLAUDE_MD") or f"{cdir}/CLAUDE.md"
    table = os.environ.get("ENFORCEMENT_TABLE") or f"{cdir}/enforcement.md"
    # A table someone pointed at (env var or --table) and the default path are different states
    # when the file is missing: the first is a table someone HAD, the second may never have existed.
    explicit = bool(os.environ.get("ENFORCEMENT_TABLE"))
    i = 0
    while i < len(argv):
        if argv[i] in ("--table", "--rules") and i + 1 < len(argv):
            if argv[i] == "--table":
                table, explicit = argv[i + 1], True
            else:
                claude_md = argv[i + 1]
            i += 2
            continue
        i += 1

    source = _read(claude_md)
    if source is None:
        print(f"audit enforcement: cannot read {claude_md}")
        return 0
    wanted = rules(source)
    text = _read(table)
    if text is None:
        if explicit:
            print(f"audit enforcement: the table was pointed at {table} and it cannot be read — moved or "
                  f"mistyped? {len(wanted)} rule(s) are uncovered until it is back.")
        else:
            print(f"CLAUDE.md enforcement: no table yet at {table} — {len(wanted)} rule(s) with nothing recorded "
                  f"to catch them. Format and a worked example: {REFERENCES}/enforcement.md.")
        return 0

    cells = [_cells(r) for r in table_rows(text)]
    empty = sum(1 for first, second in cells if not SKIP_CELL.fullmatch(first) and not second.strip(" \t\n\r\f\v"))
    rows = _normed(first for first, _ in cells if "¶" not in first and not SKIP_CELL.fullmatch(first))
    unmarked = sorted(set(wanted) - set(rows))
    orphans = sorted(set(rows) - set(wanted))
    print(f"CLAUDE.md enforcement: {len(unmarked)} unmarked rule(s), {len(orphans)} orphan row(s), {empty} empty cell(s)")
    for r in unmarked:
        print(f"  unmarked rule: {r}")
    for r in orphans:
        print(f"  orphan row:    {r}")
    return 0
