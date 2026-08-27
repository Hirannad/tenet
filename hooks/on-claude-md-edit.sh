#!/usr/bin/env bash
# PostToolUse: the enforcement table can only go stale when CLAUDE.md changes,
# so the check is bound to that exact event rather than to a poll.
#
# Silent when the table still covers every rule. On a mismatch it exits 2, which
# shows stderr to Claude without blocking — the edit has already happened, and
# the point is to fix the table in the same turn, not to prevent the edit.
set -uo pipefail

TARGET="${CLAUDE_MD:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}/CLAUDE.md}"
# CLAUDE_PLUGIN_ROOT is set for hook commands, so this resolves inside the
# plugin. The old fallback pointed at ~/.claude/skills/tenet-audit, which never
# existed — the pre-plugin directory was named claude-md-auditor — so it was
# cover, not a fallback.
CHECK="${CLAUDE_PLUGIN_ROOT:?CLAUDE_PLUGIN_ROOT unset — this script only runs as a plugin hook}/skills/tenet-audit/scripts/enforcement-check.sh"

payload=$(cat)

# Every file_path in the payload, then ask whether ANY of them is the target.
# The previous form was a single sed whose leading `.*` is greedy, so on a
# one-line payload it captured the LAST "file_path" — tool_response's, not
# tool_input's. Those agree for Edit and Write today, which is why the bug was
# latent rather than live; asking about the set removes the ordering assumption
# instead of betting on it. Bound worth naming: a JSON-escaped path (a quote or a
# \u sequence in a filename) is not decoded here, so it would not match and the
# check would be skipped.
if ! printf '%s' "$payload" \
  | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' \
  | sed 's/.*"\([^"]*\)"$/\1/' \
  | grep -qxF "$TARGET"; then
  exit 0
fi

# A missing checker used to exit 0 here. That is the shape of failure this whole
# system exists to catch: the hook stays wired, fires on every edit, and reports
# nothing — indistinguishable from a clean table.
if [ ! -r "$CHECK" ]; then
  printf 'The enforcement check is missing at %s, so CLAUDE.md just changed with nothing verifying its table.\n' "$CHECK" >&2
  exit 2
fi

out=$(bash "$CHECK" 2>/dev/null)
# Both patterns anchor on the start of the output, not a floating substring.
# Floating, the success string also matched "10 unmarked rule(s), 0 orphan
# row(s), 0 empty cell(s)" — the tail of the 10 is a 0 — and the first-run
# string matched its own detail lines quoting a rule that happens to contain
# the phrase. Anchored, only the checker's own summary line can satisfy them.
case "$out" in
  "CLAUDE.md enforcement: 0 unmarked rule(s), 0 orphan row(s), 0 empty cell(s)"*) exit 0 ;;
  # First run: no table has ever existed at the default path. This hook fires
  # unattended on every CLAUDE.md edit, so it stays quiet here — the same split
  # the vault check makes. The loud path is the user-invoked one: tenet-audit
  # runs the check directly and its output says how to start a table. A table
  # that VANISHED from an explicitly pointed-at path (ENFORCEMENT_TABLE or
  # --table) prints differently and falls through to the alarm below; one
  # deleted from the default path is indistinguishable from first run without
  # state — the same trade-off the vault check accepts.
  "CLAUDE.md enforcement: no table yet at "*) exit 0 ;;
esac

{
  printf 'The global CLAUDE.md changed and its enforcement table no longer matches it.\n\n'
  printf '%s\n\n' "$out"
  printf 'Fix the enforcement table before finishing:\n'
  printf 'a rule with no enforcement row is itself the defect.\n'
  printf 'An unmarked rule needs a row saying what catches it, or `none` and the reason.\n'
} >&2
exit 2
