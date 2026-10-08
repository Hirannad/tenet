"""Is the tool surface still the one you accepted?

The surface grows quietly, one justified addition at a time, and a count on its own cannot see
that. So the only number worth printing is a delta against a baseline the user accepted.

It never writes: re-baselining stays a human act, because a baseline that updates itself erases
the signal it exists to produce. `--record` prints a baseline to stdout and leaves the redirect
to the user. It never gates either: the exit is 0 unless the arguments are unusable.

Options: --baseline FILE (default: <config dir>/surface-baseline.json), --record.
"""
import json
import os
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from tenet import paths

# Report order. Every key matches the hand-written baseline that predates the script, so the
# history recorded there stays comparable instead of needing a migration.
SURFACES = ("permissions_allow", "permissions_deny", "permissions_ask", "enabled_plugins",
            "extraKnownMarketplaces", "global_hook_entries", "global_skills", "global_agents",
            "enabled_plugin_skills", "skills_dir_plugins", "user_scope_mcp")
# The surfaces read out of settings.json, the only ones its pre-flight reason applies to.
FROM_SETTINGS = ("permissions_allow", "permissions_deny", "permissions_ask", "enabled_plugins",
                 "extraKnownMarketplaces", "global_hook_entries", "enabled_plugin_skills")
SETTINGS_PATHS = {"permissions_allow": (("permissions", "allow"), True),
                  "permissions_deny": (("permissions", "deny"), True),
                  "permissions_ask": (("permissions", "ask"), True),
                  "enabled_plugins": (("enabledPlugins",), False),
                  "extraKnownMarketplaces": (("extraKnownMarketplaces",), False)}
RECORD = f'python3 "{paths.CLI}" audit surface --record'
NEEDS = "needs settings.json and plugins/installed_plugins.json"
# Notes this module writes itself. A baseline note matching one is re-derived, not carried
# forward: carrying it would preserve a machine remark about a state that may have changed.
GENERATED = re.compile(r"no (skills/|agents/|plugins/data) directory|no ~/\.claude\.json"
                       r"|key absent from (settings\.json|~/\.claude\.json)|" + re.escape(NEEDS) +
                       r"|\S+ (does not parse|cannot be listed)"
                       r"|[^;]+ enabled, nothing installed(; [^;]+ enabled, nothing installed)*")
MISSING, BROKEN = object(), object()


class Unread(Exception):
    """A JSON value of the wrong shape: the surface is unread, never 0."""


def _load(path):
    """Parsed JSON, MISSING when the file cannot be opened, BROKEN when it does not parse."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except OSError:
        return MISSING
    except ValueError:
        return BROKEN


def _get(data, *keys):
    """`.a.b` lookup: None through a missing key or a null, Unread through anything not an object."""
    for key in keys:
        if data is None:
            return None
        if not isinstance(data, dict):
            raise Unread
        data = data.get(key)
    return data


def _each(value):
    """Items of a list, values of an object."""
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    raise Unread


def _text(value):
    """A JSON value as text: a string bare, anything else as JSON."""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def _json_surface(data, path, source, ordered):
    """(count, note, keys) for the value at `path`; an absent key is a real zero, not an unread one.
    `ordered` names the items in file order; otherwise the value is an object, named by sorted key."""
    value = _get(data, *path)
    if value is None:
        return 0, f"key absent from {source}", []
    if ordered and isinstance(value, (list, dict)):
        return len(value), "", [_text(x) for x in _each(value)]
    if not ordered and isinstance(value, dict):
        return len(value), "", sorted(value)
    raise Unread


def _hooks(settings):
    # `.hooks` is keyed by EVENT, and there are only about nine: counting those keys saturates
    # at once. Count the leaf commands; keep the event names for the naming line.
    hooks = _get(settings, "hooks")
    if hooks is None:
        return 0, "key absent from settings.json", []
    if not isinstance(hooks, dict):
        raise Unread
    n = 0
    for blocks in hooks.values():
        for block in _each(blocks):
            inner = _get(block, "hooks")
            n += len(_each([] if inner is None or inner is False else inner))
    return n, "", sorted(hooks)


def _listing(cdir, sub, keep, name=lambda n: n):
    """Non-hidden entries of a directory under the config dir, in name order."""
    where = cdir / sub
    if not where.is_dir():
        return 0, f"no {sub} directory", []
    try:
        names = sorted(e.name for e in os.scandir(where) if not e.name.startswith(".") and keep(e))
    except OSError:
        return None, f"{sub} cannot be listed", []
    return len(names), "", [name(n) for n in names]


def _plugin_skills(cdir, settings):
    # Which cached copy is live cannot be guessed: the cache keeps every version ever installed,
    # some named by commit SHA. installed_plugins.json carries the installPath; ask it.
    inst = _load(cdir / "plugins" / "installed_plugins.json")
    if settings is MISSING or settings is BROKEN or inst is MISSING:
        return None, NEEDS, []
    if inst is BROKEN:
        return None, "plugins/installed_plugins.json does not parse", []
    try:
        enabled = _get(settings, "enabledPlugins")
    except Unread:
        return None, NEEDS, []
    n, notes = 0, []
    for key, on in (enabled.items() if isinstance(enabled, dict) else []):
        if on is None or on is False:
            continue
        try:
            entries = _get(inst, "plugins", key)
            first = entries[0] if isinstance(entries, list) and entries else None
            where = _get(first, "installPath")
        except Unread:
            where = None
        if not isinstance(where, str) or not os.path.isdir(where):
            notes.append(f"{key} enabled, nothing installed")
            continue
        n += sum((dirs + files).count("SKILL.md") for _, dirs, files in os.walk(where))
    return n, "; ".join(notes), []


def measure(key, cdir, settings):
    """(count, note, keys). count is None when the surface could not be read, which is not 0."""
    try:
        if key == "global_skills":
            return _listing(cdir, "skills/", lambda e: e.is_dir())
        if key == "global_agents":
            return _listing(cdir, "agents/", lambda e: e.name.endswith(".md") and not e.is_dir(),
                            lambda n: n[:-3])
        if key == "skills_dir_plugins":
            return _listing(cdir, "plugins/data", lambda e: True)
        if key == "enabled_plugin_skills":
            return _plugin_skills(cdir, settings)
        if key == "user_scope_mcp":
            # `claude mcp add -s user` writes ~/.claude.json, in the home directory rather than
            # inside the config dir, so it is deliberately not derived from CLAUDE_CONFIG_DIR.
            home = _load(Path.home() / ".claude.json")
            if home is MISSING:
                return 0, "no ~/.claude.json", []
            if home is BROKEN:
                return None, "~/.claude.json does not parse", []
            return _json_surface(home, ("mcpServers",), "~/.claude.json", False)
        if settings is MISSING or settings is BROKEN:
            return None, "", []
        if key == "global_hook_entries":
            return _hooks(settings)
        path, ordered = SETTINGS_PATHS[key]
        return _json_surface(settings, path, "settings.json", ordered)
    except Unread:
        return None, "", []


def _parse(argv, cdir):
    baseline, record, i = f"{cdir}/surface-baseline.json", False, 0
    while i < len(argv):
        if argv[i] == "--baseline":
            if i + 1 == len(argv):
                return None, record
            baseline, i = argv[i + 1], i + 2
            continue
        record = record or argv[i] == "--record"
        i += 1
    return baseline, record


def _surfaces(base):
    """The baseline's surfaces object, or None when the file is not a baseline this can read."""
    if isinstance(base, dict) and isinstance(base.get("surfaces"), dict):
        return base["surfaces"]
    return None


def record(cdir, settings, baseline):
    base = _load(baseline)
    surfaces = _surfaces(base)
    # stderr, because stdout is the baseline itself and usually redirected into a file.
    if base is MISSING:
        print(f"audit surface: no baseline at {baseline}, so there was no note to carry forward.", file=sys.stderr)
    elif surfaces is None:
        print(f"audit surface: {baseline} is not a surface baseline this can read, so no note was "
              "carried forward from it. Merge its notes by hand.", file=sys.stderr)
    # Everything written by hand survives a re-record: per-surface fields such as source or note,
    # and top-level fields such as _comment. Only what this module measures is replaced.
    top = {k: v for k, v in (base.items() if isinstance(base, dict) else []) if k not in ("recorded", "recorded_by", "surfaces")}
    out = {"recorded": date.today().isoformat(),
           "recorded_by": "tenet audit surface — counts and item lists as measured; every hand-written field "
                          "carried forward from the baseline this replaces.",
           **top, "surfaces": {}}
    for k in SURFACES:
        count, note, keys = measure(k, cdir, settings)
        if count is None:
            print(f"audit surface: {k} could not be read; recording null, which will read as unbaselined next time.",
                  file=sys.stderr)
        old = (surfaces or {}).get(k)
        entry = {f: v for f, v in (old.items() if isinstance(old, dict) else []) if f not in ("count", "keys", "note")}
        entry["count"] = count
        keys = [x for x in keys if x]
        if keys:
            entry["keys"] = keys
        old_note = old.get("note") if isinstance(old, dict) else None
        if isinstance(old_note, str) and old_note and not GENERATED.fullmatch(old_note):
            entry["note"] = old_note
        elif note:
            entry["note"] = note
        out["surfaces"][k] = entry
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def _was(entry):
    """The baseline count as text, or None when the baseline holds none."""
    if not isinstance(entry, dict):
        return None
    count = entry.get("count")
    return None if count is None or count is False else _text(count)


def _old_keys(entry):
    try:  # anything but a list or an object, a missing key included, names no items
        items = _each(entry.get("keys") if isinstance(entry, dict) else None)
    except Unread:
        items = []
    return sorted(t for t in map(_text, items) if t)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cdir = paths.config_dir()
    baseline, recording = _parse(argv, cdir)
    if baseline is None:
        print("audit surface: --baseline needs a FILE", file=sys.stderr)
        return 1
    settings = _load(cdir / "settings.json")
    if recording:
        return record(cdir, settings, baseline)

    # Three states, not two: a file that exists but does not parse (a truncated redirect leaves
    # exactly that) must not read as a baseline and then report "0 grown" about nothing compared.
    base = _load(baseline)
    surfaces = _surfaces(base)
    why = "no settings.json" if settings is MISSING else "settings.json does not parse" if settings is BROKEN else ""
    grown = shrunk = same = unread = counted = 0
    body = []

    def row(state, key, text):
        body.append(f"  {state:<12}{key:<23} {text}")

    for k in SURFACES:
        count, note, keys = measure(k, cdir, settings)
        paren = f" ({note})" if note else ""
        if count is None:
            unread += 1
            cause = f" — {why}" if why and k in FROM_SETTINGS else ""
            row("unread", k, f"not measured{cause}{paren}")
            continue
        entry = surfaces.get(k) if surfaces is not None else None
        was = _was(entry)
        if was is None:
            unread += 1
            counted += 1
            row("unbaselined", k, f"{count} now{paren}")
            continue
        if not re.fullmatch(r"[0-9]+", was):
            unread += 1
            row("unusable", k, f"baseline holds {was}, which is not a count")
            continue
        d = count - int(was)
        if d == 0:
            same += 1
            row("unchanged", k, f"{count}{paren}")
            continue
        if d > 0:
            grown += 1
        else:
            shrunk += 1
        row("grown" if d > 0 else "shrunk", k, f"{was} -> {count} ({'+' if d > 0 else ''}{d})")
        # Name the items where the surface is a list: a bare "+12" says look, the twelve names
        # say whether to keep them. Either side may be empty; a surface that emptied still lost items.
        now, old = [x for x in keys if x], _old_keys(entry)
        if now or old:
            if not old:
                body.append("               (the baseline recorded a count but no item list, so the change cannot be named)")
            else:
                body += [f"               added:   {x}" for x in sorted((Counter(now) - Counter(old)).elements())]
                body += [f"               removed: {x}" for x in sorted((Counter(old) - Counter(now)).elements())]

    # A surface the baseline tracks and this does not measure would otherwise just vanish from
    # the report: the quiet kind of gap this check exists to prevent, arriving from the inside.
    for bk in sorted(surfaces or {}):
        if bk and bk not in SURFACES:
            unread += 1
            row("untracked", bk, "in the baseline, never measured here — it will never be diffed")

    if surfaces is not None:
        when = base.get("recorded")
        when = "undated" if when is None or when is False else _text(when)
        head = f"Claude surface: {grown} grown, {shrunk} shrunk, {same} unchanged, {unread} unmeasured (baseline {when})"
    elif base is not MISSING:
        head = (f"Claude surface: {baseline} exists but is not a surface baseline this can read (no .surfaces object).\n"
                "Nothing was compared — the counts below are today only. Re-record it, or point --baseline at\n"
                f'the real one:\n\n  {RECORD} > "{baseline}.new"\n')
    else:
        head = (f"Claude surface: no baseline yet at {baseline} — {counted} of {len(SURFACES)} surfaces counted below, nothing to\n"
                "compare them against. Record them once you have accepted this surface as intentional:\n\n"
                f'  {RECORD} > "{baseline}.new"\n\n'
                "Then read it and move it into place yourself. The redirect truncates its target, so a\n"
                "record that goes wrong must not be pointed at the file you would lose.\n")
    print("\n".join([head] + body))
    return 0
