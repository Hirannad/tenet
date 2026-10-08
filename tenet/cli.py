#!/usr/bin/env python3
"""The one entry point for hooks and skills: python3 tenet/cli.py <command>."""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tenet import bootstrap, inbox, ledger, paths, promote, sweep, verdict  # noqa: E402
from tenet.observer import brief, run  # noqa: E402


def _ledger(quiet_when_absent):
    path, source = paths.ledger()
    usable, message = paths.check_ledger(path, source, quiet_when_absent)
    if message:
        print(message)
    return path if usable else None


def _step(name, render):
    """Run one hook step; a crash is reported and never takes the other step down with it."""
    try:
        lines = render()
    except Exception as exc:  # noqa: BLE001
        lines = [f"TENET ERROR: {name} failed: {type(exc).__name__}: {exc}"]
    if lines:
        print("\n".join(lines), flush=True)


def briefing(vault, compact):
    """The session-start block: the precomputed brief for this directory. Launches a background
    scan when one is due, never after a compaction."""
    data = paths.data_dir()
    if data is None:
        return [f"LEDGER: {vault}", "TENET BRIEF: CLAUDE_PLUGIN_DATA is not set for this hook, so no brief can be read or computed."]
    text, matched = brief.lookup(data, os.path.realpath(os.getcwd()))
    reason = None if compact else run.due(vault, data, matched)
    out = []
    if reason:
        try:
            run.spawn(data)
        except OSError as exc:
            reason = None
            out.append(f"TENET OBSERVER FAILING: cannot launch a scan from {data}: {exc}")
    out += run.banners(data)
    if text is None:
        out += [f"LEDGER: {vault}", "TENET BRIEF: none computed yet" + (" — a first scan was launched" if reason else "") + "; ask for a note by name."]
    else:
        out.append(text.rstrip("\n"))
    pending = len(ledger.md_files(vault / "inbox"))
    if pending:
        out.append(f"{pending} draft(s) awaiting review in inbox/. Tell the user to run /tenet:tenet-capture review: it is user-invoked, so the Skill tool cannot start it.")
    if reason and text is not None:
        out.append(f"(brief refresh launched in the background: {reason})")
    return out


def session_start(compact):
    # A hook must never block a session, and must never fail silently either.
    try:
        vault = _ledger(quiet_when_absent=True)
    except Exception as exc:  # noqa: BLE001
        print(f"TENET ERROR: resolving the ledger failed: {type(exc).__name__}: {exc}")
        return 0
    if vault is None:
        return 0
    if not compact:
        _step("promote", lambda: promote.run(vault))
    _step("brief", lambda: briefing(vault, compact))
    return 0


def stop_hook():
    """The verdict gate. Silent unless it fires; a failure is logged and shown at the next session
    start, because printing it here would interrupt a session that is just ending a turn."""
    import json
    data = paths.data_dir()
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        vault, source = paths.ledger()
        if data is None or not paths.check_ledger(vault, source, True)[0]:
            return 0
        text = verdict.gate(payload, vault, data)
    except Exception as exc:  # noqa: BLE001
        if data is not None:
            log = paths.verdict_errors(data)
            log.parent.mkdir(parents=True, exist_ok=True)
            with open(log, "a") as f:
                f.write(f"{type(exc).__name__}: {exc}\n")
        return 0
    if text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": text}}))
    return 0


def observe(vault, args):
    data = paths.data_dir()
    if data is None:
        print("tenet: no data directory. The hook gets CLAUDE_PLUGIN_DATA from Claude Code; by hand, set TENET_DATA.")
        return 1
    if args.action == "status":
        print("\n".join(f"{k}={v}" for k, v in sorted(run.status(data).items())) or "no scan has run yet")
        return 0
    result = run.scan(vault, data)
    if not args.quiet:
        print("another scan holds the lock" if result is None else
              "scan: {} session(s), {} project brief(s), {} new use(s) recorded".format(*result))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tenet")
    sub = parser.add_subparsers(dest="command", required=True)
    hook = sub.add_parser("hook")
    hook.add_argument("event", choices=["session-start", "stop"])
    hook.add_argument("--compact", action="store_true")
    sub.add_parser("promote")
    sub.add_parser("inbox")
    sub.add_parser("sweep")
    sub.add_parser("brief")
    ver = sub.add_parser("verdict")
    ver.add_argument("action", choices=["apply"])
    ver.add_argument("--ticket", required=True)
    obs = sub.add_parser("observe")
    obs.add_argument("action", choices=["scan", "status"])
    obs.add_argument("--quiet", action="store_true")
    audit = sub.add_parser("audit")
    audit.add_argument("check", choices=["layers", "surface", "enforcement", "frontmatter"])
    audit.add_argument("args", nargs=argparse.REMAINDER)
    boot = sub.add_parser("bootstrap")
    boot.add_argument("target", nargs="?")
    args = parser.parse_args(argv)

    if args.command == "hook":
        return stop_hook() if args.event == "stop" else session_start(args.compact)
    if args.command == "audit":
        # The audit reads instruction files, not the ledger, so it runs without one.
        import importlib
        return importlib.import_module(f"tenet.audit.{args.check}").main(args.args)
    if args.command == "bootstrap":
        code, lines = bootstrap.run(args.target)
        print("\n".join(lines))
        return code
    vault = _ledger(quiet_when_absent=False)
    if vault is None:
        return 1
    if args.command == "observe":
        return observe(vault, args)
    if args.command == "verdict":
        import json
        data = paths.data_dir()
        if data is None:
            print("tenet: no data directory; set TENET_DATA when running this by hand.")
            return 1
        print("\n".join(verdict.apply(vault, data, args.ticket, json.loads(sys.stdin.read() or "{}"))))
        return 0
    render = {
        "promote": lambda: promote.run(vault),
        "brief": lambda: briefing(vault, compact=True),
        "inbox": lambda: inbox.render(vault),
        "sweep": lambda: sweep.render(vault),
    }[args.command]
    print("\n".join(render()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
