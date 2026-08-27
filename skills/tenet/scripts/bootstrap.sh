#!/usr/bin/env bash
# bootstrap.sh — create a vault where there is none.
#
# The plugin shipped for a day with no way to make the thing it reads. Every
# session start printed a repair procedure for a vault that had never existed,
# and the docs referenced templates/ and _meta/ files that were not in the
# repository at all. This is that gap closed.
#
# Refuses to touch a directory that already holds notes. Creating a vault is
# cheap; overwriting one is not.
#
# Usage: bootstrap.sh [target-directory]
#        Defaults to the configured ledger path, or ~/Claude/<VAULT_NAME>.
set -uo pipefail

. "$(dirname "$0")/lib.sh" || { echo "tenet: cannot source lib.sh next to me — the plugin install is broken."; exit 1; }

TARGET="${1:-$VAULT}"
TEMPLATE="$(cd "$(dirname "$0")/../../.." && pwd)/vault-template"

[ -d "$TEMPLATE" ] || { printf 'tenet: vault-template/ is missing from the plugin at %s — the install is incomplete.\n' "$TEMPLATE"; exit 1; }

# Three refusals, because one was not enough. The guard used to look only for
# root-level *.md — but this script goes on to `rm -rf "$TARGET/.obsidian"` (see
# below), and an Obsidian vault that keeps every note in subfolders has no
# root-level markdown at all. Pointed at one, the old guard passed and the next
# few lines deleted that vault's workspace, plugins and settings. `${TARGET:?}`
# guards the empty string, not the wrong directory.
if [ -d "$TARGET" ]; then
  refusal=""
  [ -d "$TARGET/.obsidian" ] && refusal="it is already an Obsidian vault (.obsidian/ is there)"
  if [ -z "$refusal" ] && [ -n "$(find "$TARGET" -name '*.md' -print -quit 2>/dev/null)" ]; then
    refusal="it already holds markdown files, at some depth"
  fi
  if [ -n "$refusal" ]; then
    printf 'tenet: refusing to write into %s — %s.\n' "$TARGET" "$refusal"
    printf 'This script creates a vault; it does not merge into one. If you meant to start a second vault, pass a different path: bootstrap.sh /path/to/new-vault\n'
    exit 1
  fi
fi

mkdir -p "$TARGET" || exit 1
# -R with a trailing /. copies contents rather than the directory itself, on both
# BSD and GNU cp.
cp -R "$TEMPLATE/." "$TARGET/" || exit 1
# Validating a release means opening vault-template/ in Obsidian, which leaves an
# .obsidian/ behind every time. It is gitignored, so it never ships — but cp does
# not read .gitignore, so without this line one person's window layout would seed
# every vault created on that machine.
rm -rf "${TARGET:?}/.obsidian"
mkdir -p "$TARGET/inbox" "$TARGET/raw"
# Git and most tooling drop empty directories; the vault needs both to exist.
: > "$TARGET/inbox/.gitkeep"
: > "$TARGET/raw/.gitkeep"

printf 'tenet: vault created at %s\n\n' "$TARGET"
# Counted, not asserted. This summary claimed three notes and no views while the
# template shipped seven views and could have shipped any number of notes; a
# hardcoded inventory is how a directory goes missing for a release without
# anything saying so.
notes=$(find "$TARGET" -maxdepth 1 -name '*.md' ! -name 'README.md' | wc -l | tr -d ' ')
views=$(find "$TARGET/bases" -name '*.base' 2>/dev/null | wc -l | tr -d ' ')
printf 'What is there:\n'
printf '  %s example notes in the root — read them once, then delete them\n' "$notes"
printf '  templates/ one per note type\n'
printf '  bases/     %s saved views — the catalogue, since there is no index file\n' "$views"
# Counted, not asserted, for the same reason as the two counts above: this line
# claimed "the three journals" for one release after hot.md was removed and left
# two, which is how a hardcoded manifest goes stale without anything saying so.
printf '  _meta/     %s bookkeeping file(s) — bindings, statuses, and the journals\n\n' \
  "$(find "$TARGET/_meta" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
printf 'Next:\n'
printf '  1. git init in it if you want the history — the notes are the database, git is the backup\n'
printf '  2. /tenet:tenet         see what is in scope in the current directory\n'
printf '  3. /tenet:tenet-capture turn a decision into a draft\n'
printf '  4. /tenet:tenet-sweep   the weekly pass over revisit conditions\n\n'
[ "$TARGET" = "$VAULT" ] || printf 'This is not the default path, so point the plugin at it: set the ledger path in the plugin config (/plugin), or export TENET_LEDGER=%s.\n' "$TARGET"
