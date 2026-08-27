#!/usr/bin/env bash
# Does every rule carry an enforcement row?
#
# One script, two targets — the same idea implemented once, not twice:
#
#   1. Full mode (default, no args): the global CLAUDE.md against the user's
#      own table at ~/.claude/enforcement.md. Prints three numbers: unmarked
#      rules (the defect), orphan rows (the table went stale), empty cells.
#   2. Table-only mode (--empty-only): any file with an enforcement table, e.g.
#      the ledger vault's conventions.md. Prints just the empty-cell count, or
#      MISSING when the section has no rows. promote.sh consumes this.
#
# Until 2026-08-15 the second target had its own copy of this logic inline in
# promote.sh — the exact duplication the fusion plan removes.
#
# Reports only — it never gates, and in full mode it never exits non-zero,
# because a broken checker must not be able to block a session.
#
# Options:
#   --table FILE     enforcement table (default: ~/.claude/enforcement.md)
#   --section NAME   heading the table sits under (default: "The table")
#   --header WORD    first-column header word to skip (default: "Rule")
#   --rules FILE     rules source for full mode (default: ~/.claude/CLAUDE.md)
#   --empty-only     table-only mode: print the empty-cell count or MISSING
set -uo pipefail

CLAUDE_MD="${CLAUDE_MD:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}/CLAUDE.md}"
# The table is DATA, and it lives beside the file it describes — the companion to
# CLAUDE_MD in the same layer, not inside the plugin. references/enforcement.md
# here documents the format and carries one worked example; it is not anybody's
# table. Override with ENFORCEMENT_TABLE when the instruction file is elsewhere.
TABLE="${ENFORCEMENT_TABLE:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}/enforcement.md}"
# Explicitly pointed-at (env var or --table) and default are different states
# when the file is missing: the first is a table someone HAD, the second may
# never have existed. The missing-table branch below keys off this.
TABLE_EXPLICIT="${ENFORCEMENT_TABLE:+yes}"
SECTION="The table"
HEADER="Rule"
MODE="full"

while [ $# -gt 0 ]; do
  case "$1" in
    --table)      TABLE="$2"; TABLE_EXPLICIT="yes"; shift 2 ;;
    --section)    SECTION="$2"; shift 2 ;;
    --header)     HEADER="$2"; shift 2 ;;
    --rules)      CLAUDE_MD="$2"; shift 2 ;;
    --empty-only) MODE="empty"; shift ;;
    *) shift ;;
  esac
done

if [ ! -r "$TABLE" ] && [ "$MODE" = "empty" ]; then
  echo "MISSING"; exit 0
fi

# Identical normalisation on both sides: drop markdown noise and the list bullet,
# collapse whitespace, lowercase, keep 40 characters. Long rules stay readable in
# the table while still matching their source line.
norm() {
  sed -e 's/[*`_]//g' \
      -e 's/^[[:space:]]*-[[:space:]]*//' \
      -e 's/[[:space:]][[:space:]]*/ /g' \
      -e 's/^ //' -e 's/ *$//' \
    | tr '[:upper:]' '[:lower:]' \
    | cut -c1-40 \
    | grep -v '^$'
}

# Only the rows under the requested section — prose and other tables are not rules.
table_rows() {
  awk -v s="^## $SECTION\$" '$0 ~ s {t=1; next} t && /^## / {t=0} t && /^\|/' "$TABLE"
}

# The alignment row may carry colons (`---`, `:--`, `--:`, `:-:`). The shipped
# examples use `---`, but this repo's README tables use `:--` — so a user copying
# that style got a permanent orphan-row alarm (GAPS 21, reproduced live).
count_empty() {
  table_rows | awk -F'|' -v h="$HEADER" '$2 !~ ("^[[:space:]]*(" h "|:?-+:?)[[:space:]]*$") {
    c = $3; gsub(/^[[:space:]]+|[[:space:]]+$/, "", c); if (c == "") n++
  } END {print n+0}'
}

if [ "$MODE" = "empty" ]; then
  if [ -z "$(table_rows)" ]; then echo "MISSING"; else count_empty; fi
  exit 0
fi

[ -r "$CLAUDE_MD" ] || { echo "enforcement-check: cannot read $CLAUDE_MD"; exit 0; }

rules=$(awk '/^```/ {f=!f; next} !f && /^- /' "$CLAUDE_MD" | norm | sort -u)

# A missing table is TWO states (the lib.sh vault check owns this pattern).
# An explicitly pointed-at table (env var or --table) that cannot be read is a
# table someone HAD — broken configuration, and the hook alarms on it. The
# default path never having held one is a first run, and it still reports the
# rule count, so "no table" never prints like "all covered". A table deleted
# from the default path is indistinguishable from first run without state —
# the same trade-off the vault check accepts for the default vault path.
# on-claude-md-edit.sh anchors on the "CLAUDE.md enforcement: no table yet at"
# line start — change them together.
if [ ! -r "$TABLE" ]; then
  n=$(printf '%s' "$rules" | grep -c . || true)
  if [ -n "$TABLE_EXPLICIT" ]; then
    printf 'enforcement-check: the table was pointed at %s and it cannot be read — moved or mistyped? %s rule(s) are uncovered until it is back.\n' "$TABLE" "$n"
  else
    printf 'CLAUDE.md enforcement: no table yet at %s — %s rule(s) with nothing recorded to catch them. Format and a worked example: %s/enforcement.md.\n' \
      "$TABLE" "$n" "$(cd "$(dirname "$0")/../references" && pwd)"
  fi
  exit 0
fi

rows=$(table_rows | awk -F'|' '{print $2}' \
       | grep -v '¶' \
       | grep -Ev "^[[:space:]]*($HEADER|:?-+:?)[[:space:]]*$" \
       | norm | sort -u)

empty=$(count_empty)

unmarked=$(comm -23 <(printf '%s\n' "$rules") <(printf '%s\n' "$rows"))
orphans=$(comm -13 <(printf '%s\n' "$rules") <(printf '%s\n' "$rows"))

nu=$(printf '%s' "$unmarked" | grep -c . || true)
no=$(printf '%s' "$orphans" | grep -c . || true)

printf 'CLAUDE.md enforcement: %s unmarked rule(s), %s orphan row(s), %s empty cell(s)\n' \
  "$nu" "$no" "$empty"
[ "$nu" -gt 0 ] && printf '%s\n' "$unmarked" | sed 's/^/  unmarked rule: /'
[ "$no" -gt 0 ] && printf '%s\n' "$orphans" | sed 's/^/  orphan row:    /'
exit 0
