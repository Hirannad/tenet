#!/usr/bin/env bash
# Inbox state for a capture/review run.
#
# This lives in a script rather than a ```! block in SKILL.md because that block
# is preprocessed by a shell that rejects expansions it would have to perform —
# ${VAR:-default} and $(...) both fail with "Contains expansion". The inline
# block therefore never ran, and the skill body never loaded at all.
#
# ${CLAUDE_PLUGIN_ROOT} is the exception, verified 2026-08-16: the plugin loader
# substitutes it before the check, so the shell never sees an expansion. That is
# what the SKILL.md invocation uses. $HOME and $(...) still fail — rename-check.sh
# check 3 knows the difference and scans both skill trees.

set -uo pipefail

# Vault location comes from the shared lib (one copy, not four); it also does
# the loud existence + case-exactness check that the 2026-08-10 silent failure
# earned. Plugin-relative only: the pre-plugin ~/.claude/skills copies are gone,
# and a fallback to a path that no longer exists is worse than none — it hides
# which layout actually resolved.
_lib="$(dirname "$0")/../../tenet/scripts/lib.sh"
[ -r "$_lib" ] && . "$_lib"
if [ -z "${VAULT:-}" ]; then
  echo "BRAIN ERROR: cannot find tenet/scripts/lib.sh — was the tenet skill renamed? Run rename-check.sh."
  exit 1
fi
V="$VAULT"
echo "Vault: $V"

brain_vault_check || exit 1

drafts=$(find "$V/inbox" -maxdepth 1 -name '*.md' 2>/dev/null | sort)
n=$(printf '%s' "$drafts" | grep -c . || true)
echo "Drafts pending: $n"
[ "$n" -gt 0 ] && printf '%s\n' "$drafts" | sed 's|.*/|  - |'

echo "Existing notes: $(find "$V" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
