#!/usr/bin/env bash
# on-stop.sh — inject the capture gate at the end of a response.
#
# Why this file exists at all. Until 2.1.0 hooks.json did the whole job inline:
# a `[ -d .../inbox ] && cat stop-prompt.md || true`. Two things were wrong with
# it, and the second one is the reason the plugin's automatic-drafting path had
# never run:
#
#   1. It carried its own literal copy of the default vault path, because
#      hooks.json cannot source lib.sh. One fact, two hand-kept copies, nothing
#      comparing them — the exact drift class this plugin exists to catch, in its
#      own hook config. A script can source lib.sh, so the copy is gone rather
#      than merely checked. rename-check.sh check 8 now enforces that hooks.json
#      never grows one back.
#   2. It wrote the gate to STDOUT and exited 0. For a Stop hook that goes to the
#      debug log and nowhere else: the shipped harness passes hook stdout to the
#      model for SessionStart, UserPromptSubmit and UserPromptExpansion only.
#      Measured on 2026-08-27, four mechanisms, one prompt each — stdout: not
#      delivered; systemMessage: not delivered; additionalContext: delivered;
#      additionalContext with no re-entry guard: delivered and looped until the
#      turn limit. So it is additionalContext, with the guard.
#
# Always exits 0. A capture nudge must never be able to block a session.
set -uo pipefail

LIB="${CLAUDE_PLUGIN_ROOT:?CLAUDE_PLUGIN_ROOT unset — this script only runs as a plugin hook}/skills/tenet/scripts/lib.sh"
PROMPT="$CLAUDE_PLUGIN_ROOT/skills/tenet/references/stop-prompt.md"
RULES="$CLAUDE_PLUGIN_ROOT/skills/tenet/references/draft-rules.md"

payload=$(cat 2>/dev/null || true)

# The re-entry guard. Injecting on a stop that this hook itself caused would
# re-ask the gate forever; the harness gives up after 8 consecutive rounds
# (CLAUDE_CODE_STOP_HOOK_BLOCK_CAP) and overrides the hook, which is a worse
# failure than not firing. Verified in both directions: without this line the
# probe ran to the turn limit, with it the injection landed exactly once.
if printf '%s' "$payload" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then
  exit 0
fi

# emit MESSAGE — the only channel out of a Stop hook that reaches the model.
#
# Escapes backslash, double quote and newline, in that order, because doing them
# in any other order double-escapes. The first version of this function escaped
# newlines only and guarded the input with a grep for quotes — which meant a
# vault path containing one disabled the gate. Escaping properly is shorter than
# the guard was.
emit() {
  printf '{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"%s"}}\n' \
    "$(printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | awk '{ printf "%s\\n", $0 }')"
}

# TENET_LIB_QUIET keeps lib.sh's own warnings off stdout, which here is a JSON
# channel — but they are collected in TENET_LIB_NOTICE and travel with the gate
# instead of vanishing. A library warning that disappears because the caller
# needed a clean pipe is the failure mode this plugin is named for.
TENET_LIB_QUIET=1
. "$LIB" 2>/dev/null || exit 0

# vault_check writes to STDOUT by design — that is where hook messages survive,
# everywhere except here, where stdout is a JSON channel and a stray line makes
# the whole object unparseable. So it is captured, and the two states stay two
# states: a configured path that is missing says so through additionalContext,
# and a first run with no vault yet stays silent.
vc=$(vault_check --quiet-when-absent 2>&1) || {
  [ -z "$vc" ] || emit "$vc"
  exit 0
}
[ -z "$vc" ] || TENET_LIB_NOTICE="${TENET_LIB_NOTICE:+$TENET_LIB_NOTICE }$vc"

[ -d "$VAULT/inbox" ] || exit 0
[ -r "$PROMPT" ] || { emit "tenet: the Stop gate is wired up but $PROMPT is missing or unreadable, so no capture check ran this turn. Tell the user; the plugin install is incomplete."; exit 0; }

# Drop the editing comment: it is for whoever maintains the file, and it would be
# paid for in every response.
gate=$(sed '/^<!--/,/-->$/d' "$PROMPT" | sed '/./,$!d')
gate=${gate//@VAULT@/$VAULT}
gate=${gate//@DRAFT_RULES@/$RULES}
[ -z "${TENET_LIB_NOTICE:-}" ] || gate="$TENET_LIB_NOTICE"$'\n\n'"$gate"

emit "$gate"
exit 0
