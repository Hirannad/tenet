#!/usr/bin/env python3
"""The one entry point for hooks and skills: python3 tenet/cli.py <command>."""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tenet import bootstrap, inbox, legacy_list, paths, promote, sweep  # noqa: E402


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
    _step("session list", lambda: legacy_list.render(vault, os.getcwd()))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tenet")
    sub = parser.add_subparsers(dest="command", required=True)
    hook = sub.add_parser("hook")
    hook.add_argument("event", choices=["session-start"])
    hook.add_argument("--compact", action="store_true")
    sub.add_parser("promote")
    sub.add_parser("list")
    sub.add_parser("inbox")
    sub.add_parser("sweep")
    boot = sub.add_parser("bootstrap")
    boot.add_argument("target", nargs="?")
    args = parser.parse_args(argv)

    if args.command == "hook":
        return session_start(args.compact)
    if args.command == "bootstrap":
        code, lines = bootstrap.run(args.target)
        print("\n".join(lines))
        return code
    vault = _ledger(quiet_when_absent=False)
    if vault is None:
        return 1
    render = {
        "promote": lambda: promote.run(vault),
        "list": lambda: legacy_list.render(vault, os.getcwd()),
        "inbox": lambda: inbox.render(vault),
        "sweep": lambda: sweep.render(vault),
    }[args.command]
    print("\n".join(render()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
