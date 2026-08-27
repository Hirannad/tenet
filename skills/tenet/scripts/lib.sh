# lib.sh — single source of truth for the two names this system carries.
#
# Sourced, never executed. Every script that needs the vault reads it from here,
# so a rename is an edit to THIS file plus the entry points that cannot source it
# (SKILL.md `!` blocks and hooks.json, which need literal paths). Check 8 in
# rename-check.sh compares the hooks.json literal against this file, because two
# hand-kept copies of one default with nothing comparing them is the exact drift
# class this tool exists to catch — and until 2.1.0 that copy was unchecked.
#
# Why this exists: the 2026-08-08 Brain→brain rename left nine hardcoded copies
# of the old path behind, and the scheduled maintenance run died silently on a
# case-sensitive filesystem, and nothing reported it for a week. One default,
# checked loudly.
#
# The two names are deliberately separate. The VAULT is the content — notes you
# read in Obsidian, its own repository. The PLUGIN is the machinery that reads
# it. A tool and its store having different names is ordinary (git and .git),
# and conflating them means one rename has to move both.

# --- the vault: content ------------------------------------------------------
# Directory name under ~/Claude. rename-check.sh greps the whole surface for
# stale spellings; change it here first, then run that script.
VAULT_NAME="ledger"

# Every name the vault has EVER had, space-separated. On a rename: set
# VAULT_NAME to the new one, append the old one here, run rename-check.sh — it
# greps the reference surface for path-shaped uses and fails loudly on any hit.
# "Brain" is the 2026-08-08 spelling that killed the 08-10 scheduled run.
# "brain" is the 2.1.0 spelling, retired because the plugin is called tenet and
# the store was still advertising a different metaphor in three skill
# descriptions that load in every session.
VAULT_PREVIOUS_NAMES="Brain brain"

# --- the plugin: machinery ---------------------------------------------------
# Names the skill directories (tenet, tenet-capture, tenet-sweep, tenet-audit)
# and the repository. Same rename procedure, same check.
PLUGIN_NAME="tenet"

# "canon" was the working name this repository was built under, for one day.
# "brain" and "claude-md-auditor" are the pre-plugin skill directories; they were
# deleted from ~/.claude/skills on 2026-08-16, and until then they were excluded
# here on purpose — a check that fires on something legitimately present teaches
# you to ignore it. From 2.1.0 "brain" is retired on both axes, so the guard in
# rename-check.sh that used to except it no longer matches. It stays: it is a
# general guard for the next name that retires on one axis and not the other.
PLUGIN_PREVIOUS_NAMES="canon brain claude-md-auditor"

# Claude Code's own config directory. CLAUDE_CONFIG_DIR relocates it, and until
# 2.1.0 exactly one of the five scripts that read this tree honoured the
# variable — so on a relocated config dir the surface check reported every JSON
# surface as unmeasured rather than reading it.
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

# --- where the vault is ------------------------------------------------------
# Four sources, in precedence order. The first is the platform's own mechanism:
# `userConfig` in plugin.json declares the path as a typed `directory` option,
# Claude Code prompts for it when the plugin is enabled, and exports it to every
# hook process as CLAUDE_PLUGIN_OPTION_LEDGER. That is what a new install uses,
# and it is why "set the environment variable to match" left the Getting started
# list in 2.1.0.
#
# BRAIN_VAULT is kept because removing it is the one genuinely breaking change in
# the rename: a user who exported it and takes an update would otherwise be told
# "no vault yet" and offered a bootstrap, and accepting that offer would give
# them a second, empty vault beside the real one. So it still resolves, and
# vault_check says so on the paths where a person is present to read it.
VAULT_SOURCE="default"
if [ -n "${CLAUDE_PLUGIN_OPTION_LEDGER:-}" ]; then
  VAULT="$CLAUDE_PLUGIN_OPTION_LEDGER"
  VAULT_SOURCE="userConfig"
elif [ -n "${TENET_LEDGER:-}" ]; then
  VAULT="$TENET_LEDGER"
  VAULT_SOURCE="TENET_LEDGER"
elif [ -n "${BRAIN_VAULT:-}" ]; then
  VAULT="$BRAIN_VAULT"
  VAULT_SOURCE="BRAIN_VAULT"
else
  VAULT="$HOME/Claude/$VAULT_NAME"
fi

# --- section names: the one place the machinery reads the vault's language ----
# Notes are prose, and their headings are prose too. Only SECTION_DECISION is
# matched mechanically (the 60-word cap), but the whole set lives here so a
# locale carries it in one piece and the shipped templates cannot drift from
# what the checks look for.
SECTION_DECISION="Decision"
SECTION_REVISIT="When to reconsider"
SECTION_WHY="Why"
SECTION_BACKGROUND="Background"
SECTION_OPTIONS="Options weighed"
SECTION_DILEMMA="The dilemma"

# The locale is a property of the VAULT, not of the machine: a vault carries its
# own language to whatever machine clones it. `_meta/locale` holds one word
# naming a file in this plugin's locales/. TENET_LOCALE overrides it for a single
# run. Neither set means English.
#
# This is a parameterised template, a shape worth being suspicious of: one engine
# with a config header tends to become two systems sharing a directory. Kept to
# its smallest honest form — six strings, no second instance. If locales ever
# diverge past section names, that suspicion was right and this should go.
#
# The name is validated before it becomes a path. It comes from vault CONTENT,
# and this line SOURCES the file it names: without the guard, a `_meta/locale`
# holding `../../../../tmp/x` would execute /tmp/x.sh. Data must not be able to
# choose which code runs.
_locale="${TENET_LOCALE:-}"
if [ -z "$_locale" ] && [ -r "$VAULT/_meta/locale" ]; then
  _locale=$(head -n 1 "$VAULT/_meta/locale" 2>/dev/null | tr -d '[:space:]')
fi
# Anything this file has to say at source time goes into TENET_LIB_NOTICE as
# well as to stdout, and TENET_LIB_QUIET=1 suppresses the print. A caller whose
# stdout is a machine-readable channel — the Stop hook emits JSON — cannot let a
# library warning land in the middle of it, and cannot drop the warning either:
# that is the silence this whole system is built against. So the library reports
# and the caller picks the channel.
TENET_LIB_NOTICE=""
_notice() {
  TENET_LIB_NOTICE="${TENET_LIB_NOTICE:+$TENET_LIB_NOTICE }$1"
  [ "${TENET_LIB_QUIET:-0}" = "1" ] || printf '%s\n' "$1"
}

if [ -n "$_locale" ]; then
  case "$_locale" in
    *[!a-zA-Z0-9_-]*)
      _notice "tenet: locale '$_locale' is not a plain name (letters, digits, - and _ only). Ignoring it — a locale names a file in the plugin, and a path there would choose which code runs."
      _locale=""
      ;;
  esac
fi
if [ -n "$_locale" ]; then
  _locale_file="$(dirname "${BASH_SOURCE[0]:-$0}")/../../../locales/${_locale}.sh"
  if [ -r "$_locale_file" ]; then
    . "$_locale_file"
  else
    _notice "tenet: locale '$_locale' is set but $_locale_file does not exist — falling back to English section names, which will not match this vault."
  fi
fi

# vault_check [--quiet-when-absent] — loud when the vault is missing or its
# on-disk name differs in case from the configured one. Errors go to STDOUT on
# purpose: the hooks pipe stderr to /dev/null (`2>/dev/null || true`), so stderr
# is exactly where a message goes to disappear. Return 1 so callers can decide to
# stop; callers in hooks still exit 0 so a broken checker never blocks a session
# — a failure that reports nothing is worse than one that shouts.
#
# "Missing" is TWO states, and conflating them is a bug this plugin shipped with.
# A configured path that does not exist is broken configuration and has to be
# loud. The default path simply not existing yet is a fresh install, and shouting
# a repair procedure at someone who has nothing to repair is noise in every
# session forever. The model is the clean install: a vault renamed out from under
# a live config is covered by the documented rename procedure (edit this file,
# run rename-check.sh) and by the case check below, not by guessing from the
# neighbours — until 0.5.0 a heuristic here treated any vault-shaped sibling as
# rename evidence, which made every fresh install with one such neighbour loud in
# every session, twice, forever (owner verdict, 2026-08-20).
#
# --quiet-when-absent belongs to the callers that fire unattended on every
# SessionStart, including the post-compaction one. The user-invoked entry points
# leave it off, so the bootstrap instructions appear the moment someone reaches
# for tenet — and so does the BRAIN_VAULT migration notice, which is advice
# rather than a failure and therefore has no business in an unattended run.
vault_check() {
  _quiet_absent=0
  [ "${1:-}" = "--quiet-when-absent" ] && _quiet_absent=1

  if [ "$VAULT_SOURCE" = "BRAIN_VAULT" ] && [ "$_quiet_absent" -eq 0 ]; then
    printf 'tenet: BRAIN_VAULT still works and still points at %s. It is the pre-2.1.0 name; the current one is TENET_LEDGER, and a fresh install is asked for the path at enable time instead. Nothing to do unless you want the new spelling.\n' "$VAULT"
  fi

  if [ ! -d "$VAULT" ]; then
    if [ "$VAULT_SOURCE" != "default" ]; then
      # Loud even in quiet mode — but this state is ambiguous: a vault that
      # moved, OR a configured path exported before its vault exists (dotfiles
      # outlive machines). Both fixes are named, so neither reader dead-ends in a
      # message loop.
      printf 'TENET ERROR: the vault path came from %s and points at %s, where nothing is. If the vault moved, fix that setting (or scripts/lib.sh) and run rename-check.sh. If it does not exist yet, create it:\n\n  bash "%s/bootstrap.sh" "%s"\n' \
        "$VAULT_SOURCE" "$VAULT" "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)" "$VAULT"
      return 1
    fi
    [ "$_quiet_absent" -eq 1 ] && return 1
    printf 'tenet: no vault yet. It is an ordinary directory of markdown files — create one with templates and three worked examples:\n\n  bash "%s/bootstrap.sh"\n\nIt will not touch an existing vault. Pass a path to put it somewhere other than %s.\n' \
      "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)" "$VAULT"
    return 1
  fi
  # `find -name` compares against the directory entry as stored on disk, so this
  # catches a case mismatch even on APFS, where [ -d ] happily lies.
  if [ -z "$(find "$(dirname "$VAULT")" -mindepth 1 -maxdepth 1 -name "$(basename "$VAULT")" 2>/dev/null)" ]; then
    printf 'TENET ERROR: vault path %s does not match the on-disk name in case. This works on APFS and dies silently on case-sensitive filesystems — the exact 2026-08-10 failure. Fix the path, then run rename-check.sh.\n' "$VAULT"
    return 1
  fi
  return 0
}

# read_bindings FILE — emit one `path<TAB>topics` line per LIVE binding.
#
# One parser, because there were two and they disagreed. resolve.sh read every
# line matching the shape; rename-check.sh skipped code fences and HTML comments,
# with the comment that those hold the format examples rather than live bindings.
# The shipped vault-template/_meta/bindings.md carries one example in a fence and
# one in an HTML comment — `~/code/acme-api` — so on every fresh vault the
# looser parser loaded phantom topics for anyone whose work happened to live
# there, and the stricter one could not report it because by its own reading
# there was no binding. Two readings of one file is the drift class, in the file
# that decides what the model sees.
read_bindings() {
  [ -f "$1" ] || return 0
  awk '
    /^[[:space:]]*```/ { infence = !infence; next }
    infence { next }
    /<!--/ { incomment = 1 }
    incomment { if (/-->/) incomment = 0; next }
    # The shape: a backquoted path, an arrow, then the topics.
    /`[^`]+`[^`]*→/ {
      line = $0
      sub(/^[^`]*`/, "", line)
      path = line
      sub(/`.*$/, "", path)
      topics = $0
      sub(/^.*→[[:space:]]*/, "", topics)
      if (path != "" && topics != "") printf "%s\t%s\n", path, topics
    }
  ' "$1"
}
