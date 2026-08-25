# lib.sh — single source of truth for the two names this system carries.
#
# Sourced, never executed. Every script that needs the vault reads it from here,
# so a rename is an edit to THIS file plus the entry points that cannot source it
# (SKILL.md `!` blocks and hooks.json, which need literal paths).
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
BRAIN_NAME="brain"

# Every name the vault has EVER had, space-separated. On a rename: set
# BRAIN_NAME to the new one, append the old one here, run rename-check.sh — it
# greps the reference surface for path-shaped uses and fails loudly on any hit.
# "Brain" is the 2026-08-08 spelling that killed the 08-10 scheduled run.
BRAIN_PREVIOUS_NAMES="Brain"

# --- the plugin: machinery ---------------------------------------------------
# Names the skill directories (tenet, tenet-capture, tenet-sweep, tenet-audit)
# and the repository. Same rename procedure, same check.
PLUGIN_NAME="tenet"

# "canon" was the working name this repository was built under, for one day.
# "brain" and "claude-md-auditor" are the pre-plugin skill directories; they were
# deleted from ~/.claude/skills on 2026-08-16, and until then they were excluded
# here on purpose — a check that fires on something legitimately present teaches
# you to ignore it.
PLUGIN_PREVIOUS_NAMES="canon brain claude-md-auditor"

VAULT="${BRAIN_VAULT:-$HOME/Claude/$BRAIN_NAME}"

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
_locale="${TENET_LOCALE:-}"
if [ -z "$_locale" ] && [ -r "$VAULT/_meta/locale" ]; then
  _locale=$(head -n 1 "$VAULT/_meta/locale" 2>/dev/null | tr -d '[:space:]')
fi
if [ -n "$_locale" ]; then
  _locale_file="$(dirname "${BASH_SOURCE[0]:-$0}")/../../../locales/${_locale}.sh"
  if [ -r "$_locale_file" ]; then
    . "$_locale_file"
  else
    printf 'tenet: locale "%s" is set but %s does not exist — falling back to English section names, which will not match this vault.\n' "$_locale" "$_locale_file"
  fi
fi

# brain_vault_check [--quiet-when-absent] — loud when the vault is missing or its
# on-disk name differs in case from the configured one. Errors go to STDOUT on
# purpose: the hooks pipe stderr to /dev/null (`2>/dev/null || true`), so stderr
# is exactly where a message goes to disappear. Return 1 so callers can decide to
# stop; callers in hooks still exit 0 so a broken checker never blocks a session
# — a failure that reports nothing is worse than one that shouts.
#
# "Missing" is TWO states, and conflating them is a bug this plugin shipped with.
# BRAIN_VAULT pointing at a path that does not exist is broken configuration and
# has to be loud. The default path simply not existing yet is a fresh install,
# and shouting a repair procedure at someone who has nothing to repair is noise
# in every session forever. The model is the clean install: a vault renamed out
# from under a live config is covered by the documented rename procedure (edit
# this file, run rename-check.sh) and by the case check below, not by guessing
# from the neighbours — until 0.5.0 a heuristic here treated any vault-shaped
# sibling as rename evidence, which made every fresh install with one such
# neighbour loud in every session, twice, forever (owner verdict, 2026-08-20).
#
# --quiet-when-absent belongs to the callers that fire unattended on every
# SessionStart, including the post-compaction one. The user-invoked entry points
# leave it off, so the bootstrap instructions appear the moment someone reaches
# for tenet.
brain_vault_check() {
  _quiet_absent=0
  [ "${1:-}" = "--quiet-when-absent" ] && _quiet_absent=1

  if [ ! -d "$VAULT" ]; then
    if [ -n "${BRAIN_VAULT:-}" ]; then
      # Loud even in quiet mode — but this state is ambiguous: a vault that
      # moved, OR a custom path exported before its vault exists (the README
      # says "set BRAIN_VAULT to match", and dotfiles outlive machines). Both
      # fixes are named, so neither reader dead-ends in a message loop.
      printf 'BRAIN ERROR: BRAIN_VAULT points at %s and nothing is there. If the vault moved, fix BRAIN_VAULT (or scripts/lib.sh) and run rename-check.sh. If it does not exist yet, create it:\n\n  bash "%s/bootstrap.sh" "%s"\n' \
        "$VAULT" "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)" "$VAULT"
      return 1
    fi
    [ "$_quiet_absent" -eq 1 ] && return 1
    printf 'tenet: no vault yet. It is an ordinary directory of markdown files — create one with templates and three worked examples:\n\n  bash "%s/bootstrap.sh"\n\nIt will not touch an existing vault. Pass a path to put it somewhere other than %s, and set BRAIN_VAULT to match.\n' \
      "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)" "$VAULT"
    return 1
  fi
  # `find -name` compares against the directory entry as stored on disk, so this
  # catches a case mismatch even on APFS, where [ -d ] happily lies.
  if [ -z "$(find "$(dirname "$VAULT")" -mindepth 1 -maxdepth 1 -name "$(basename "$VAULT")" 2>/dev/null)" ]; then
    printf 'BRAIN ERROR: vault path %s does not match the on-disk name in case. This works on APFS and dies silently on case-sensitive filesystems — the exact 2026-08-10 failure. Fix the path, then run rename-check.sh.\n' "$VAULT"
    return 1
  fi
  return 0
}
