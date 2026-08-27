#!/usr/bin/env bash
# surface-check.sh — is the tool surface still the one you accepted?
#
# The failure mode this exists for: the surface grows quietly, one justified
# addition at a time. A count on its own cannot see that. One recorded case: an
# inventory three months after a full config reset found 25 enabled plugins
# where an earlier count had 18, and 15 of the 25 had never fired once.
#
# So the only number worth printing is a delta, and a delta needs a baseline the
# user accepted. Until 2026-08-21 that comparison was prose in
# references/config-hygiene.md telling the model to do it by hand — which meant
# the README promised a measurement nothing performed. This is the mechanism.
#
# It never writes. Re-baselining stays a human act: a baseline that updates
# itself erases the signal it exists to produce. `--record` prints a baseline to
# stdout and leaves the redirect to the user.
#
# It never gates either — always exit 0, like enforcement-check.sh. A broken
# checker must not be able to block a session.
#
# Options:
#   --baseline FILE   baseline to compare against (default: ~/.claude/surface-baseline.json)
#   --record          print a baseline for today's counts to stdout, compare nothing
set -uo pipefail

# CLAUDE_CONFIG_DIR relocates Claude Code's config tree. Until 2.1.0 this script
# — the one whose whole job is reading that tree — was pinned to ~/.claude, so on
# a relocated config dir it reported every JSON surface as unread rather than
# reading it. ~/.claude.json is deliberately not derived from this: it sits in the
# home directory rather than inside the config dir.
CDIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SETTINGS="$CDIR/settings.json"
BASELINE="$CDIR/surface-baseline.json"
MODE="compare"

while [ $# -gt 0 ]; do
  case "$1" in
    --baseline) BASELINE="$2"; shift 2 ;;
    --record)   MODE="record"; shift ;;
    *) shift ;;
  esac
done

# jq reads the JSON surfaces AND the baseline, so without it there is no diff at
# all. That is reported, not silently downgraded to zeroes: the whole point of
# this script is that "nothing grew" and "nothing was looked at" must not print
# the same way.
JQ=$(command -v jq 2>/dev/null || true)

# The surfaces, in report order. Every key here matches the hand-written
# baseline that predates this script, so the history recorded there stays
# comparable instead of needing a migration.
SURFACES="permissions_allow permissions_deny permissions_ask enabled_plugins
extraKnownMarketplaces global_hook_entries global_skills global_agents
enabled_plugin_skills skills_dir_plugins user_scope_mcp"
# Wrapped for reading, so the membership test below needs the newlines collapsed —
# unquoted word splitting does that. Matching against the wrapped form silently
# reported four measured surfaces as never-measured.
SURFACE_SET=" $(echo $SURFACES) "

# json_str VALUE — VALUE as a JSON string, quotes included.
#
# This script both reads JSON and writes it, and the writing half used to be two
# different things at once: `keys` went through `jq -R .` and `note` through a
# bare printf with no escaping at all. One of the note values embeds a plugin key
# read out of settings.json, so a plugin name containing a quote produced an
# invalid baseline — from the script whose entire job is that the baseline can be
# compared later. Same escaping for both now, and it needs no jq, so `--record`
# still works on a machine that has none.
json_str() {
  printf '"%s"' "$(printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')"
}

# jq_count PATH — the count at a JSON path, or the word `absent` when the key is
# not there (which is a real zero, not an unread surface), or empty when jq or
# the file is missing (which is an unread surface, not a zero).
jq_count() {
  [ -n "$JQ" ] && [ -r "$2" ] || return 0
  jq -r "($1) as \$v | if \$v == null then \"absent\" else (\$v | length) end" "$2" 2>/dev/null
}

# measure KEY — sets M_COUNT (number, or empty when unread), M_NOTE (why a zero
# or an empty is what it is), M_KEYS (newline-separated item names, where the
# surface is a list; growth is far more useful with the added items named).
measure() {
  M_COUNT=""; M_NOTE=""; M_KEYS=""; M_SRC=""
  case "$1" in
    permissions_allow)      M_COUNT=$(jq_count '.permissions.allow' "$SETTINGS")
                            M_KEYS=$([ -n "$JQ" ] && jq -r '.permissions.allow[]?' "$SETTINGS" 2>/dev/null) ;;
    permissions_deny)       M_COUNT=$(jq_count '.permissions.deny' "$SETTINGS")
                            M_KEYS=$([ -n "$JQ" ] && jq -r '.permissions.deny[]?' "$SETTINGS" 2>/dev/null) ;;
    permissions_ask)        M_COUNT=$(jq_count '.permissions.ask' "$SETTINGS")
                            M_KEYS=$([ -n "$JQ" ] && jq -r '.permissions.ask[]?' "$SETTINGS" 2>/dev/null) ;;
    enabled_plugins)        M_COUNT=$(jq_count '.enabledPlugins' "$SETTINGS")
                            M_KEYS=$([ -n "$JQ" ] && jq -r '.enabledPlugins | keys[]?' "$SETTINGS" 2>/dev/null) ;;
    extraKnownMarketplaces) M_COUNT=$(jq_count '.extraKnownMarketplaces' "$SETTINGS")
                            M_KEYS=$([ -n "$JQ" ] && jq -r '.extraKnownMarketplaces | keys[]?' "$SETTINGS" 2>/dev/null) ;;
    global_hook_entries)    # `.hooks` is keyed by EVENT, and there are only about nine events
                            # — counting those keys saturates almost immediately, and five hooks
                            # added under an existing event registered as no growth at all. Count
                            # the leaf commands; keep the event names for the naming line.
                            M_COUNT=$(jq_count '[.hooks | to_entries[] | .value[] | (.hooks // [])[]]' "$SETTINGS")
                            M_KEYS=$([ -n "$JQ" ] && jq -r '.hooks | keys[]?' "$SETTINGS" 2>/dev/null) ;;
    global_skills)          if [ -d "$CDIR/skills" ]; then
                              M_KEYS=$(cd "$CDIR/skills" && ls -d */ 2>/dev/null | sed 's|/$||')
                              M_COUNT=$(printf '%s' "$M_KEYS" | grep -c . || true)
                            else M_COUNT=0; M_NOTE="no skills/ directory"; fi ;;
    global_agents)          if [ -d "$CDIR/agents" ]; then
                              M_KEYS=$(cd "$CDIR/agents" && ls *.md 2>/dev/null | sed 's|\.md$||')
                              M_COUNT=$(printf '%s' "$M_KEYS" | grep -c . || true)
                            else M_COUNT=0; M_NOTE="no agents/ directory"; fi ;;
    enabled_plugin_skills)  # Where growth actually happens: one plugin ships any number of
                            # skills, each an always-loaded description. Which cached copy is
                            # live cannot be guessed — cache/<marketplace>/<plugin>/ keeps every
                            # version ever installed (eight of this plugin's own), and some are
                            # named by commit SHA rather than semver, so sorting the directory
                            # names is not an ordering. installed_plugins.json carries the
                            # installPath; ask it. Counting the whole cache tree counted history
                            # instead: 111 files where 15 descriptions load.
                            _inst="$CDIR/plugins/installed_plugins.json"
                            if [ -z "$JQ" ] || [ ! -r "$SETTINGS" ] || [ ! -r "$_inst" ]; then
                              M_NOTE="needs settings.json and plugins/installed_plugins.json"
                            else
                              _n=0
                              while IFS= read -r _ep; do
                                [ -n "$_ep" ] || continue
                                _p=$(jq -r --arg k "$_ep" '.plugins[$k][0].installPath // empty' "$_inst" 2>/dev/null)
                                if [ -z "$_p" ] || [ ! -d "$_p" ]; then
                                  M_NOTE="${M_NOTE:+$M_NOTE; }$_ep enabled, nothing installed"
                                  continue
                                fi
                                _n=$((_n + $(find "$_p" -name SKILL.md 2>/dev/null | grep -c . || true)))
                              done <<EOF
$(jq -r '.enabledPlugins | to_entries[]? | select(.value) | .key' "$SETTINGS" 2>/dev/null)
EOF
                              M_COUNT=$_n
                            fi ;;
    skills_dir_plugins)     if [ -d "$CDIR/plugins/data" ]; then
                              M_KEYS=$(cd "$CDIR/plugins/data" && ls 2>/dev/null)
                              M_COUNT=$(printf '%s' "$M_KEYS" | grep -c . || true)
                            else M_COUNT=0; M_NOTE="no plugins/data directory"; fi ;;
    user_scope_mcp)         # `claude mcp add -s user` writes ~/.claude.json, not
                            # ~/.claude/.mcp.json — the path this check watched until 0.6.0,
                            # which made the one surface the README calls "MCP servers" a zero
                            # that could never become anything else, reported as `unchanged`.
                            M_SRC="~/.claude.json"
                            if [ -r "$HOME/.claude.json" ]; then
                              M_COUNT=$(jq_count '.mcpServers' "$HOME/.claude.json")
                              M_KEYS=$([ -n "$JQ" ] && jq -r '.mcpServers | keys[]?' "$HOME/.claude.json" 2>/dev/null)
                            else M_COUNT=0; M_NOTE="no ~/.claude.json"; fi ;;
  esac
  if [ "$M_COUNT" = "absent" ]; then M_COUNT=0; M_NOTE="key absent from ${M_SRC:-settings.json}"; fi
}

# --- record mode: today's counts as a baseline, on stdout only ---------------
if [ "$MODE" = "record" ]; then
  if [ -z "$JQ" ]; then
    # stderr, not stdout: the documented invocation redirects stdout into the baseline,
    # so a message printed there replaces the accepted file with prose. The redirect
    # still truncates whatever it points at, which is why the documented target is a
    # .new file the user moves over the real one themselves.
    printf 'surface-check: jq is not installed, so the JSON surfaces cannot be read and a baseline\nrecorded now would understate the surface. Install jq first.\n' >&2
    exit 0
  fi
  printf '{\n  "recorded": "%s",\n  "recorded_by": "surface-check.sh — counts only. Add a note per surface by hand; the reasoning is the part a diff cannot reconstruct.",\n  "surfaces": {\n' "$(date +%Y-%m-%d)"
  first=1
  for k in $SURFACES; do
    measure "$k"
    # stdout is the baseline itself and usually redirected, so a hole in it has to
    # announce itself on stderr or it gets written silently and read back as absent.
    [ -n "$M_COUNT" ] || printf 'surface-check: %s could not be read; recording null, which will read as unbaselined next time.\n' "$k" >&2
    [ "$first" -eq 1 ] || printf ',\n'
    first=0
    printf '    "%s": { "count": %s' "$k" "${M_COUNT:-null}"
    if [ -n "$M_KEYS" ]; then
      printf ', "keys": ['
      sep=""
      while IFS= read -r item; do
        [ -n "$item" ] || continue
        printf '%s%s' "$sep" "$(json_str "$item")"
        sep=", "
      done <<EOF
$M_KEYS
EOF
      printf ']'
    fi
    [ -n "$M_NOTE" ] && printf ', "note": %s' "$(json_str "$M_NOTE")"
    printf ' }'
  done
  printf '\n  }\n}\n'
  exit 0
fi

# --- compare mode ------------------------------------------------------------
if [ -z "$JQ" ]; then
  printf 'Claude surface: NOT MEASURED — jq is not installed, and it is what reads both settings.json\nand the baseline. This is unmeasured, not unchanged: no surface was compared. Install jq, or\ndrop the surface-growth check rather than letting it report silence.\n'
  exit 0
fi

# Three states, not two. A file that exists but does not parse (a truncated redirect
# leaves exactly that behind) used to read as a baseline with a blank date, and the
# summary line then said "0 grown" about surfaces it had never compared.
BASE_OK=""
if [ -r "$BASELINE" ]; then
  jq -e '.surfaces | type == "object"' "$BASELINE" >/dev/null 2>&1 && BASE_OK=yes
fi

# One pre-flight read, so every JSON surface can name the same cause instead of
# eleven lines each saying only that something went wrong.
SETTINGS_WHY=""
if [ ! -r "$SETTINGS" ]; then SETTINGS_WHY="no settings.json"
elif ! jq -e . "$SETTINGS" >/dev/null 2>&1; then SETTINGS_WHY="settings.json does not parse"
fi

grown=0; shrunk=0; same=0; unread=0; counted=0; body=""
add_line() { body="${body}$1
"; }

for k in $SURFACES; do
  measure "$k"
  if [ -z "$M_COUNT" ]; then
    unread=$((unread + 1))
    add_line "$(printf '  %-12s%-23s %s' "unread" "$k" "not measured${SETTINGS_WHY:+ — $SETTINGS_WHY}${M_NOTE:+ ($M_NOTE)}")"
    continue
  fi
  if [ -n "$BASE_OK" ]; then
    was=$(jq -r --arg k "$k" '.surfaces[$k].count // "none"' "$BASELINE" 2>/dev/null)
  else
    was="none"
  fi
  if [ "$was" = "none" ] || [ -z "$was" ]; then
    unread=$((unread + 1))
    counted=$((counted + 1))
    add_line "$(printf '  %-12s%-23s %s now%s' "unbaselined" "$k" "$M_COUNT" "${M_NOTE:+ ($M_NOTE)}")"
    continue
  fi
  case "$was" in
    ''|*[!0-9]*)
      unread=$((unread + 1))
      add_line "$(printf '  %-12s%-23s baseline holds %s, which is not a count' "unusable" "$k" "$was")"
      continue ;;
  esac
  d=$((M_COUNT - was))
  if [ "$d" -eq 0 ]; then
    same=$((same + 1))
    add_line "$(printf '  %-12s%-23s %s%s' "unchanged" "$k" "$M_COUNT" "${M_NOTE:+ ($M_NOTE)}")"
    continue
  fi
  [ "$d" -gt 0 ] && { grown=$((grown + 1)); word="grown"; sign="+"; } || { shrunk=$((shrunk + 1)); word="shrunk"; sign=""; }
  add_line "$(printf '  %-12s%-23s %s -> %s (%s%s)' "$word" "$k" "$was" "$M_COUNT" "$sign" "$d")"
  # Name the items where the surface is a list. A bare "+12" tells you to look;
  # the twelve names tell you whether to keep them.
  old=$(jq -r --arg k "$k" '.surfaces[$k].keys // [] | .[]' "$BASELINE" 2>/dev/null | sort)
  # Either side may be empty — a surface that emptied to zero still has items that
  # left, and gating the whole block on today's list hid exactly that case.
  if [ -n "$M_KEYS" ] || [ -n "$old" ]; then
    added=$(comm -23 <(printf '%s\n' "$M_KEYS" | sort | grep -v '^$' || true) <(printf '%s\n' "$old" | grep -v '^$' || true))
    gone=$(comm -13 <(printf '%s\n' "$M_KEYS" | sort | grep -v '^$' || true) <(printf '%s\n' "$old" | grep -v '^$' || true))
    if [ -z "$old" ]; then
      add_line "               (the baseline recorded a count but no item list, so the change cannot be named)"
    else
      [ -n "$added" ] && add_line "$(printf '%s\n' "$added" | grep . | sed 's/^/               added:   /')"
      [ -n "$gone" ] && add_line "$(printf '%s\n' "$gone" | grep . | sed 's/^/               removed: /')"
    fi
  fi
done

# A surface the baseline tracks and this script does not measure would otherwise
# just disappear from the report — the quiet kind of gap this check exists to
# prevent, arriving from the inside.
if [ -n "$BASE_OK" ]; then
  while IFS= read -r bk; do
    [ -n "$bk" ] || continue
    case "$SURFACE_SET" in
      *" $bk "*) ;;
      *) unread=$((unread + 1))
         add_line "$(printf '  %-12s%-23s in the baseline, never measured here — it will never be diffed' "untracked" "$bk")" ;;
    esac
  done <<EOF
$(jq -r '.surfaces | keys[]?' "$BASELINE" 2>/dev/null)
EOF
fi

if [ -n "$BASE_OK" ]; then
  when=$(jq -r '.recorded // "undated"' "$BASELINE" 2>/dev/null)
  printf 'Claude surface: %s grown, %s shrunk, %s unchanged, %s unmeasured (baseline %s)\n' \
    "$grown" "$shrunk" "$same" "$unread" "$when"
elif [ -r "$BASELINE" ]; then
  printf 'Claude surface: %s exists but is not a surface baseline this can read (no .surfaces object).\nNothing was compared — the counts below are today only. Re-record it, or point --baseline at\nthe real one:\n\n  bash "%s/surface-check.sh" --record > "%s.new"\n\n' \
    "$BASELINE" "$(cd "$(dirname "$0")" && pwd)" "$BASELINE"
else
  printf 'Claude surface: no baseline yet at %s — %s of 11 surfaces counted below, nothing to\ncompare them against. Record them once you have accepted this surface as intentional:\n\n  bash "%s/surface-check.sh" --record > "%s.new"\n\nThen read it and move it into place yourself. The redirect truncates its target, so a\nrecord that goes wrong must not be pointed at the file you would lose.\n\n' \
    "$BASELINE" "$counted" "$(cd "$(dirname "$0")" && pwd)" "$BASELINE"
fi
printf '%s' "$body"
exit 0
