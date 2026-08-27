#!/usr/bin/env bash
# rename-check.sh — the mechanism behind renames.
#
# The 2026-08-08 Brain→brain rename left nine hardcoded copies of the old path
# behind; the scheduled maintenance run then died silently on a case-sensitive
# filesystem, and a week later two more copies (~/.claude/CLAUDE.md, the
# Obsidian vault registry) were still live. Care did not work twice; this
# script is the mechanism instead: a rule that breaks twice gets something that
# fails when it is broken, or it gets deleted. Writing it down again is neither.
#
# What it checks, across the whole reference surface:
#   1. Path-shaped uses of every PREVIOUS name (Claude/<old>, skills/<old>).
#   2. The vault exists AND its on-disk name matches in case (via lib.sh —
#      [ -d ] lies on APFS, `find -name` does not).
#   3. SKILL.md ```! blocks carry no expansion the preprocessor has to perform —
#      one that does is rejected whole and silently truncates the skill (three
#      skills were mute for weeks this way, and nothing said so).
#      ${CLAUDE_PLUGIN_ROOT} is the one exception, verified 2026-08-16 by
#      running /tenet:tenet from the plugin cache: the loader substitutes it before
#      the permission check, so the shell never sees an expansion. $HOME and
#      $(...) still fail. Both skill trees are scanned — this repo's own and
#      ~/.claude/skills — because a check blind to its own tree is not a check.
#   4. SKILL.md frontmatter parses: a ": " inside an unquoted value reads as a
#      mapping, the block fails whole, and the skill loads with NO metadata —
#      same silent truncation as 3, different cause. 0.6.0 shipped one for a few
#      minutes; nothing here caught it, only `claude plugin validate`.
#   5. Active bindings in _meta/bindings.md point at directories that exist.
#   6. The vault's git remote still carries the current name (NOTE only —
#      GitHub redirects renamed repos, so this nags rather than fails).
#   8. hooks.json resolves no vault path of its own. It cannot source lib.sh,
#      so anything it names is a second copy of a fact lib.sh owns — the fix is
#      a script that sources lib.sh, not a comparison. Same class as 7.
#   7. The two manifests agree on name, version, license and keywords. Not a
#      rename check, but the same class and the same gate: two hand-kept copies
#      of one set of facts with nothing comparing them. The three DESCRIPTIONS
#      are deliberately different lengths for different surfaces, so they stay a
#      human release-checklist line rather than a check.
#
# Rename procedure: edit lib.sh (new VAULT_NAME, old name appended to
# VAULT_PREVIOUS_NAMES), edit the three SKILL.md literals, rename the directory
# and the GitHub repo, run this. Check 1 covers the literals; check 8 makes sure
# hooks.json never becomes one of them again.
# Exit 0 clean, 1 on any finding — loud by design; run it by hand, not from a
# hook.
#
# Usage: rename-check.sh [extra-stale-name ...]
set -uo pipefail

. "$(dirname "$0")/lib.sh" || { echo "rename-check: cannot source lib.sh next to me — that is itself a finding."; exit 1; }

findings=0
say() { findings=$((findings + 1)); printf '%s\n' "$*"; }

# --- the reference surface -------------------------------------------------
# Everything that names the store or the skills by path, plus this plugin's own
# tree. Two kinds of thing are deliberately NOT scanned for stale names, and both
# for the same reason — they are records rather than references:
#   * the store's knowledge notes: retro.md and log.md write down old spellings
#     as part of what happened.
#   * this repository's CHANGELOG.md, which is keyed by version and exists to say
#     what each release changed. The 2.1.0 entry documents the brain→ledger
#     rename and therefore has to spell the old name; on a fresh clone that made
#     the release gate fire on the paragraph explaining the release. Found by
#     running the gate against a simulated clone, which is also the only way it
#     could have been found — the working tree has other findings that masked it.
# README.md is NOT excluded. It carries live paths a reader will copy, so a stale
# one there is exactly what this check is for.
PLUGIN_ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
# $CLAUDE_DIR comes from lib.sh and honours CLAUDE_CONFIG_DIR. Six of these
# paths were pinned to ~/.claude until 2.1.0, so on a relocated config directory
# this script grepped six paths that did not exist and reported clean.
SURFACE=(
  "$CLAUDE_DIR/CLAUDE.md"
  "$CLAUDE_DIR/settings.json"
  "$CLAUDE_DIR/RESTORE.md"
  "$CLAUDE_DIR/surface-baseline.json"
  "$CLAUDE_DIR/skills"
  "$CLAUDE_DIR/scheduled-tasks"
  # Obsidian's vault registry: macOS first, then Linux. Both are listed rather
  # than detected, because grep skipping a path that does not exist is exactly
  # the silence this script exists to prevent — on Linux the macOS-only entry
  # used to drop one surface with no sign it had.
  "$HOME/Library/Application Support/obsidian/obsidian.json"
  "$HOME/.config/obsidian/obsidian.json"
  "$VAULT/_meta/bindings.md"
  "$PLUGIN_ROOT"
)

# --- 1. stale names ----------------------------------------------------------
# Vault names appear as `Claude/<name>`; plugin names as `skills/<name>` and as
# the repository directory. Checked separately because the two renamed apart, on
# their own schedules: the machinery became `tenet` in 0.1.0 and the vault became
# `ledger` in 2.1.0, and for the eighteen releases in between they carried
# different names on purpose.
for name in $VAULT_PREVIOUS_NAMES "$@"; do
  [ -n "$name" ] || continue
  for pat in "Claude/$name"; do
    # Exclude this script BY FILE, not by line content. The previous form piped
    # through `grep -v rename-check.sh`, which also swallowed every legitimate
    # line elsewhere that happened to name the script — RESTORE.md's own restore
    # command among them, so the runbook kept a dead path invisibly.
    hits=$(grep -rn --exclude-dir=.git --exclude='rename-check.sh' --exclude='CHANGELOG.md' -F "$pat" "${SURFACE[@]}" 2>/dev/null || true)
    if [ -n "$hits" ]; then
      say "STALE VAULT NAME '$pat' still referenced:"
      printf '%s\n' "$hits" | sed 's/^/  /'
    fi
  done
done

for name in $PLUGIN_PREVIOUS_NAMES; do
  [ -n "$name" ] || continue
  pats=("skills/$name/" "skills/$name\"")
  # `Claude/<name>` catches a plugin repository that used to live under ~/Claude,
  # but only when the vault loop is not already checking that same pattern —
  # otherwise every hit prints twice and a reader learns to skim the section.
  #
  # Two ways that happens, and both have been live. A name still current on the
  # vault axis: until 2.1.0 "brain" was the plugin's retired skill directory AND
  # the vault's live name, and without the first test every correct vault
  # reference read as a stale plugin name. A name retired on BOTH axes: after
  # 2.1.0 "brain" is exactly that, and without the second test the vault loop and
  # this one report the same twenty lines each. One pattern, one owner.
  _skip=0
  [ "$name" = "$VAULT_NAME" ] && _skip=1
  for _vn in $VAULT_PREVIOUS_NAMES; do [ "$name" = "$_vn" ] && _skip=1; done
  [ "$_skip" -eq 1 ] || pats+=("Claude/$name")
  for pat in "${pats[@]}"; do
    hits=$(grep -rn --exclude-dir=.git --exclude='rename-check.sh' --exclude='CHANGELOG.md' -F "$pat" "${SURFACE[@]}" 2>/dev/null || true)
    if [ -n "$hits" ]; then
      say "STALE PLUGIN NAME '$pat' still referenced:"
      printf '%s\n' "$hits" | sed 's/^/  /'
    fi
  done
done

# --- 2. vault exists, case-exactly ------------------------------------------
vault_check || findings=$((findings + 1))

# --- 3. expansion-free ```! blocks -------------------------------------------
# The SKILL.md preprocessor rejects a ```! block that needs a shell expansion
# ("Contains expansion") and the whole skill body then fails to load, silently.
# ${CLAUDE_PLUGIN_ROOT} is exempt: the plugin loader substitutes it first, so it
# never reaches the check. Everything else — $HOME, $(...) — still fails.
for sk in "$PLUGIN_ROOT/skills"/*/SKILL.md "$CLAUDE_DIR/skills"/*/SKILL.md; do
  [ -f "$sk" ] || continue
  bad=$(awk '/^```!/{f=1;next} /^```/{f=0}
             f { l=$0; gsub(/\$\{CLAUDE_PLUGIN_ROOT\}/, "", l); if (l ~ /\$/) print }' "$sk")
  if [ -n "$bad" ]; then
    say "EXPANSION in \`\`\`! block of $sk — the preprocessor will reject it and the skill will silently truncate:"
    printf '%s\n' "$bad" | sed 's/^/  /'
  fi
done

# --- 4. frontmatter that parses ----------------------------------------------
# The failure this catches is invisible at runtime: no error, no warning, the
# skill simply arrives with every frontmatter field dropped — no name, no
# description, so the model never sees it exists. One ": " in a plain YAML
# scalar is enough, and a description is exactly the kind of prose that grows a
# colon. Quoted values are skipped: those are legal.
for sk in "$PLUGIN_ROOT/skills"/*/SKILL.md "$CLAUDE_DIR/skills"/*/SKILL.md; do
  [ -f "$sk" ] || continue
  bad=$(awk 'NR==1 { if ($0 != "---") exit; next }
             /^---[ \t]*$/ { exit }
             /^[A-Za-z][A-Za-z0-9_-]*:[ \t]/ {
               v = $0; sub(/^[^:]*:[ \t]+/, "", v)
               c = substr(v, 1, 1)
               if (c == "\042" || c == "\047") next
               if (v ~ /: /) printf "%d: %s\n", NR, substr($0, 1, 90)
             }' "$sk")
  if [ -n "$bad" ]; then
    say "UNQUOTED \": \" in the frontmatter of $sk — YAML reads it as a mapping, the block fails to parse, and the skill loads with no metadata at all:"
    printf '%s\n' "$bad" | sed 's/^/  /'
  fi
done

# --- 5. active bindings resolve ----------------------------------------------
# A renamed project directory silently unbinds its topics; nothing else notices.
# The parsing is lib.sh's read_bindings, shared with resolve.sh since 2.1.0. It
# used to be a second, stricter implementation here: this one skipped code fences
# and HTML comments (they hold the format examples, not live bindings) and
# resolve.sh did not, so the shipped template bound two phantom topics on every
# fresh vault and this check could not report them — by its own reading there was
# nothing there.
while IFS="$(printf '\t')" read -r bpath _btopics; do
  case "$bpath" in "~"*) bpath="$HOME${bpath#\~}" ;; esac
  [ -d "$bpath" ] || say "DEAD BINDING: $bpath"
done < <(read_bindings "$VAULT/_meta/bindings.md")

# --- 6. git remote carries the current name (NOTE only) ----------------------
remote=$(git -C "$VAULT" remote get-url origin 2>/dev/null || true)
if [ -n "$remote" ]; then
  case "$remote" in
    *"$VAULT_NAME"*) : ;;
    *) printf 'NOTE: vault git remote (%s) does not carry the current name "%s". GitHub redirects, but update it after a repo rename.\n' "$remote" "$VAULT_NAME" ;;
  esac
fi

# --- 7. the two manifests agree ----------------------------------------------
# `claude plugin update` gates on plugin.json's version while the marketplace
# entry advertises its own copy, and until now nothing compared the two. Kept
# jq-free on purpose: jq is declared as exactly one script's dependency, and a
# second user of it would make the README's own claim false. Extraction is pinned
# to the indentation jq emits per nesting level — two spaces for plugin.json's
# top level, six for the marketplace's plugin entry — which is also what keeps
# author.name and the marketplace's own top-level name out of the comparison. A
# reformat therefore yields an EMPTY value rather than quietly matching the wrong
# key, and an empty value is a finding here, not a pass.
manifest_scalar() { # file, indent, key
  # Bound worth naming: the capture stops at the first `"`, so a value carrying an
  # escaped quote would be compared on its prefix. Nothing this reads can hold one —
  # plugin names are kebab-case, versions semver, licenses SPDX ids.
  sed -n "s/^$2\"$3\": *\"\([^\"]*\)\".*/\1/p" "$1" | head -1
}
manifest_keywords() { # file, indent — one keyword per line, in order
  # The closing bracket is matched with OR WITHOUT a trailing comma. Matching the
  # bare `]` alone worked only because keywords happens to be the last key in both
  # manifests today; the day it stops being last, that version would run on through
  # the rest of the file and report a confidently wrong list. One keyword per line
  # rather than space-joined, so a keyword containing a space cannot mask a real
  # difference, and a line holding no quoted value is named instead of dropped.
  awk -v ind="$2" '
    $0 == ind "\"keywords\": [" { inlist = 1; next }
    inlist && index($0, ind "]") == 1 { exit }
    inlist {
      if (match($0, /"[^"]*"/)) print substr($0, RSTART + 1, RLENGTH - 2)
      else print "<unparsed: " $0 ">"
    }
  ' "$1"
}
PLUGIN_MANIFEST="$PLUGIN_ROOT/.claude-plugin/plugin.json"
MARKET_MANIFEST="$PLUGIN_ROOT/.claude-plugin/marketplace.json"
if [ ! -f "$PLUGIN_MANIFEST" ] || [ ! -f "$MARKET_MANIFEST" ]; then
  say "MANIFEST MISSING: expected both $PLUGIN_MANIFEST and $MARKET_MANIFEST. A comparison that could not run is not a comparison that passed."
else
  for key in name version license; do
    a=$(manifest_scalar "$PLUGIN_MANIFEST" '  ' "$key")
    b=$(manifest_scalar "$MARKET_MANIFEST" '      ' "$key")
    if [ -z "$a" ] || [ -z "$b" ]; then
      say "MANIFEST FIELD UNREADABLE \"$key\": plugin.json gave '$a', marketplace.json gave '$b'. The extraction is pinned to jq's indentation — check that first."
    elif [ "$a" != "$b" ]; then
      say "MANIFEST DRIFT \"$key\": plugin.json says '$a', marketplace.json says '$b'."
    fi
  done
  ka=$(manifest_keywords "$PLUGIN_MANIFEST" '  ')
  kb=$(manifest_keywords "$MARKET_MANIFEST" '      ')
  if [ -z "$ka" ] || [ -z "$kb" ]; then
    say "MANIFEST KEYWORDS UNREADABLE: plugin.json gave '$(printf '%s' "$ka" | tr '\n' '|')', marketplace.json gave '$(printf '%s' "$kb" | tr '\n' '|')'."
  elif [ "$ka" != "$kb" ]; then
    # Pipe-separated, not space-separated: with spaces, ["a b","c"] and ["a","b c"]
    # print identically and the message reads as if the two agreed.
    say "MANIFEST DRIFT keywords: plugin.json has [$(printf '%s' "$ka" | tr '\n' '|')], marketplace.json has [$(printf '%s' "$kb" | tr '\n' '|')]."
  fi
fi

# --- 8. hooks.json resolves no vault path of its own -------------------------
# Until 2.1.0 the Stop hook was written inline in hooks.json and carried its own
# literal copy of the default vault path, because hooks.json cannot source
# lib.sh. One fact, two hand-kept copies, nothing comparing them — the exact
# drift class this plugin exists to catch, sitting in its own hook config.
#
# The fix was not to compare the copies but to delete the second one: the guard
# moved into hooks/on-stop.sh, which sources lib.sh like every other script. So
# this check enforces the invariant rather than a comparison. Any vault-path
# resolution reappearing in hooks.json is a finding, whichever spelling it wears.
#
# Same rule as check 7: a check that could not run has not passed. A missing
# hooks.json is a finding, not a clean line.
HOOKS_JSON="$PLUGIN_ROOT/hooks/hooks.json"
if [ ! -f "$HOOKS_JSON" ]; then
  say "HOOKS CONFIG MISSING: expected $HOOKS_JSON. A check that could not run is not a check that passed."
else
  # Every shape that would mean hooks.json decided where the vault is: a literal
  # path, or any of the variables lib.sh consults. Listed rather than inferred,
  # because a pattern that matches nothing and a config that names nothing print
  # the same way otherwise.
  for pat in 'Claude/' 'TENET_LEDGER' 'BRAIN_VAULT' 'CLAUDE_PLUGIN_OPTION_'; do
    hits=$(grep -n -F "$pat" "$HOOKS_JSON" 2>/dev/null || true)
    if [ -n "$hits" ]; then
      say "HOOKS CONFIG RESOLVES THE VAULT ITSELF ('$pat' in $HOOKS_JSON). hooks.json cannot source lib.sh, so a path written here is a second copy of a fact lib.sh owns, and nothing would compare them. Move the guard into a script that sources lib.sh — hooks/on-stop.sh is the worked example:"
      printf '%s\n' "$hits" | sed 's/^/  /'
    fi
  done
fi

# --- verdict ------------------------------------------------------------------
if [ "$findings" -eq 0 ]; then
  printf 'rename-check: clean — no stale name, vault case-exact, !-blocks expansion-free, frontmatter parses, bindings resolve, manifests agree, hooks config resolves no path of its own.\n'
  exit 0
fi
printf 'rename-check: %s finding(s). A stale reference works on APFS and dies silently elsewhere — fix before trusting any scheduled run.\n' "$findings"
exit 1
