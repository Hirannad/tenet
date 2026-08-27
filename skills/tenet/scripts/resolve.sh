#!/usr/bin/env bash
# resolve.sh — the gate of the decision ledger.
#
# Prints the slice of the ledger that is in scope for the current working
# directory, and nothing else. Two things can be in scope:
#
#   1. Universal notes  — methodology / architecture / structure decisions.
#                         Always in scope, in every directory. This is the
#                         "how I work" layer and it deliberately crosses
#                         project boundaries.
#   2. Topic notes      — only when the current directory is bound to a topic
#                         in _meta/bindings.md.
#
# Producing no output is a normal, expected result: an unbound directory with
# an empty ledger is silent. The exit code is always 0 so that hooks never fail.

set -uo pipefail

# Vault location and the loud existence/case check live in lib.sh — one copy,
# not four. A missing or case-mismatched vault prints to stdout (which hooks
# surface; they swallow stderr) instead of vanishing silently.
. "$(dirname "$0")/lib.sh" || { printf 'TENET ERROR: cannot source %s/lib.sh\n' "$(dirname "$0")"; exit 0; }
# The SessionStart hooks call this bare and must stay quiet on a fresh install.
# The tenet skill's `!` block passes --interactive: there a missing vault has to
# print the bootstrap instructions, because that block is the stranger's first
# action and it used to be silent exactly when it had the most to say.
if [ "${1:-}" = "--interactive" ]; then
  vault_check || exit 0
else
  vault_check --quiet-when-absent || exit 0
fi

CWD="$PWD"
BINDINGS="$VAULT/_meta/bindings.md"
# Never flood the context. The cap counts LINES, and each line carries a whole
# revisit condition, so this is a rough brake rather than a byte budget. When it
# bites it says so: a `head` that quietly drops the tail is the silent-zero shape
# this system exists to catch, and the sweep's "over ~15 universal notes" advice
# fires long before the cap but is advice, not a mechanism.
MAX_LIST=40

# ---------------------------------------------------------------------------
# Read one frontmatter key. Empty if the file has no frontmatter or no key.
# ---------------------------------------------------------------------------
fm() {
  head -n 1 "$1" 2>/dev/null | grep -q '^---$' || return 0
  sed -n '2,/^---$/p' "$1" 2>/dev/null |
    sed -n "s/^$2:[[:space:]]*//p" |
    head -n 1 |
    sed 's/^["'\'']//; s/["'\'']$//'
}

# ---------------------------------------------------------------------------
# Resolve bound topics. Longest matching path prefix wins, so a binding for a
# specific package beats a binding for the repository root.
#
# The parsing lives in lib.sh's read_bindings, because until 2.1.0 this file and
# rename-check.sh each had their own reading of the same file and they disagreed:
# this one treated the shipped template's fenced and commented-out format
# examples as live bindings, so a fresh vault silently bound [[Acme]], [[Billing]]
# for anyone working under ~/code/acme-api.
# ---------------------------------------------------------------------------
topics=""
best=0
while IFS="$(printf '\t')" read -r bpath btopics; do
  [ -n "$bpath" ] || continue
  case "$bpath" in "~"*) bpath="$HOME${bpath#\~}" ;; esac
  case "$CWD" in
    "$bpath" | "$bpath"/*)
      if [ "${#bpath}" -gt "$best" ]; then
        best=${#bpath}
        topics="$btopics"
      fi
      ;;
  esac
done < <(read_bindings "$BINDINGS")

# Turn "[[Topic A]], [[Topic B]]" into a regex alternation: Topic A|Topic B
topic_re=""
if [ -n "$topics" ]; then
  topic_re=$(printf '%s\n' "$topics" |
    tr ',' '\n' |
    sed 's/^[[:space:]]*//; s/[[:space:]]*$//; s/^\[\[//; s/\]\]$//' |
    sed '/^$/d' |
    sed 's/[][\.^$*+?(){}|\\]/\\&/g' |
    paste -sd '|' -)
fi

# ---------------------------------------------------------------------------
# Classify notes.
#
# Knowledge notes live flat in the vault root. _meta, templates, inbox and raw
# are excluded on purpose: inbox holds unapproved drafts, and a draft must
# never behave as if it were canonical.
#
# gotcha is excluded by type, before the scope test so it drops out of the topic
# branch too. This list says what has already been DECIDED; a gotcha is a fact
# about a tool, and it reaches you the way every other finding does — cited from
# a decision's Why section, with that decision already in the list. Including
# them would spend context in every session on reference material you only need
# on the way into the surprise, and they default to universal, so the cost would
# be permanent and would grow.
# ---------------------------------------------------------------------------
universal_files=""
topic_files=""

while IFS= read -r f; do
  [ -n "$f" ] || continue
  [ "$(fm "$f" type)" = "gotcha" ] && continue
  if [ "$(fm "$f" scope)" = "universal" ]; then
    universal_files="$universal_files$f"$'\n'
    continue
  fi
  [ -n "$topic_re" ] || continue
  frontmatter=$(sed -n '2,/^---$/p' "$f" 2>/dev/null | tr -d '\n')
  if printf '%s' "$frontmatter" | grep -qE "$topic_re"; then
    topic_files="$topic_files$f"$'\n'
  fi
done <<EOF
$(find "$VAULT" -maxdepth 1 -type f -name '*.md' 2>/dev/null | sort)
EOF

universal_files=$(printf '%s' "$universal_files" | sed '/^$/d')
topic_files=$(printf '%s' "$topic_files" | sed '/^$/d')

# Nothing in scope and nothing bound: stay completely silent.
if [ -z "$universal_files" ] && [ -z "$topic_files" ] && [ -z "$topics" ]; then
  exit 0
fi

# ---------------------------------------------------------------------------
# One compact line per note. Title, what it is, and — for decisions — the
# condition that would make it worth revisiting.
# ---------------------------------------------------------------------------
describe() {
  local f title type status revisit
  f="$1"
  title=$(basename "$f" .md)
  type=$(fm "$f" type)
  status=$(fm "$f" status)
  revisit=$(fm "$f" revisit)
  printf -- '- [[%s]]' "$title"
  [ -n "$type" ] && printf ' (%s%s)' "$type" "${status:+, $status}"
  [ -n "$revisit" ] && printf ' — revisit when: %s' "$revisit"
  printf '\n'
}

printf 'LEDGER: %s\n' "$VAULT"
if [ -n "$topics" ]; then
  printf 'BOUND TOPICS: %s\n' "$topics"
else
  printf 'BOUND TOPICS: none (this directory is not bound; topic notes are out of scope)\n'
fi

# withheld LIST_NAME — one loud line when the cap dropped anything, so a note
# missing from the session's context is visible rather than absent.
withheld() {
  n=$(printf '%s\n' "$1" | grep -c . || true)
  [ "${n:-0}" -gt "$MAX_LIST" ] || return 0
  printf '(%s further %s note(s) withheld — MAX_LIST=%s in resolve.sh. Ask for them by name, or thin the layer: /tenet:tenet-sweep reports an over-grown universal layer.)\n' \
    "$((n - MAX_LIST))" "$2" "$MAX_LIST"
}

if [ -n "$universal_files" ]; then
  printf '\n## Always in scope — methodology, architecture, structure\n'
  printf '%s\n' "$universal_files" | head -n "$MAX_LIST" | while IFS= read -r f; do describe "$f"; done
  withheld "$universal_files" "universal"
fi

if [ -n "$topic_files" ]; then
  printf '\n## Topic notes in scope\n'
  printf '%s\n' "$topic_files" | head -n "$MAX_LIST" | while IFS= read -r f; do describe "$f"; done
  withheld "$topic_files" "topic"
fi

pending=$(find "$VAULT/inbox" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
if [ "${pending:-0}" -gt 0 ]; then
  printf '\n%s draft(s) awaiting review in inbox/. Run /tenet:tenet-capture to review them.\n' "$pending"
fi

exit 0
