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
#   7. The two manifests agree on name, version, license and keywords. Not a
#      rename check, but the same class and the same gate: two hand-kept copies
#      of one set of facts with nothing comparing them. The three DESCRIPTIONS
#      are deliberately different lengths for different surfaces, so they stay a
#      human release-checklist line rather than a check.
#
# Rename procedure: edit lib.sh (new BRAIN_NAME, old name appended to
# BRAIN_PREVIOUS_NAMES), rename the directory and the GitHub repo, run this.
# Exit 0 clean, 1 on any finding — loud by design; run it by hand, not from a
# hook.
#
# Usage: rename-check.sh [extra-stale-name ...]
set -uo pipefail

. "$(dirname "$0")/lib.sh" || { echo "rename-check: cannot source lib.sh next to me — that is itself a finding."; exit 1; }

findings=0
say() { findings=$((findings + 1)); printf '%s\n' "$*"; }

# --- the reference surface -------------------------------------------------
# Everything that names the vault or the skills by path, plus this plugin's own
# tree. The vault's knowledge notes are deliberately NOT scanned: retro.md and
# log.md record old spellings as history, and history is not a live reference.
PLUGIN_ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
SURFACE=(
  "$HOME/.claude/CLAUDE.md"
  "$HOME/.claude/settings.json"
  "$HOME/.claude/RESTORE.md"
  "$HOME/.claude/surface-baseline.json"
  "$HOME/.claude/skills"
  "$HOME/.claude/scheduled-tasks"
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
# the repository directory. Checked separately because the two renamed apart:
# the vault is still `brain` while the machinery became `tenet`.
for name in $BRAIN_PREVIOUS_NAMES "$@"; do
  [ -n "$name" ] || continue
  for pat in "Claude/$name"; do
    # Exclude this script BY FILE, not by line content. The previous form piped
    # through `grep -v rename-check.sh`, which also swallowed every legitimate
    # line elsewhere that happened to name the script — RESTORE.md's own restore
    # command among them, so the runbook kept a dead path invisibly.
    hits=$(grep -rn --exclude-dir=.git --exclude='rename-check.sh' -F "$pat" "${SURFACE[@]}" 2>/dev/null || true)
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
  # but only when that name is not what the vault is called TODAY. "brain" is
  # both — the plugin's old name and the vault's live directory — and without
  # this guard every correct `~/Claude/brain` reference reads as a stale plugin
  # name. That is the same conflation lib.sh split apart, arriving from the other
  # side: one name retired on one axis while still current on the other.
  [ "$name" = "$BRAIN_NAME" ] || pats+=("Claude/$name")
  for pat in "${pats[@]}"; do
    hits=$(grep -rn --exclude-dir=.git --exclude='rename-check.sh' -F "$pat" "${SURFACE[@]}" 2>/dev/null || true)
    if [ -n "$hits" ]; then
      say "STALE PLUGIN NAME '$pat' still referenced:"
      printf '%s\n' "$hits" | sed 's/^/  /'
    fi
  done
done

# --- 2. vault exists, case-exactly ------------------------------------------
brain_vault_check || findings=$((findings + 1))

# --- 3. expansion-free ```! blocks -------------------------------------------
# The SKILL.md preprocessor rejects a ```! block that needs a shell expansion
# ("Contains expansion") and the whole skill body then fails to load, silently.
# ${CLAUDE_PLUGIN_ROOT} is exempt: the plugin loader substitutes it first, so it
# never reaches the check. Everything else — $HOME, $(...) — still fails.
for sk in "$PLUGIN_ROOT/skills"/*/SKILL.md "$HOME/.claude/skills"/*/SKILL.md; do
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
for sk in "$PLUGIN_ROOT/skills"/*/SKILL.md "$HOME/.claude/skills"/*/SKILL.md; do
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
# HTML comments and code fences hold the format examples — not live bindings.
if [ -f "$VAULT/_meta/bindings.md" ]; then
  incomment=0; infence=0
  while IFS= read -r line; do
    case "$line" in '```'*) [ "$infence" -eq 0 ] && infence=1 || infence=0; continue ;; esac
    case "$line" in *'<!--'*) incomment=1 ;; esac
    if [ "$incomment" -eq 1 ]; then
      case "$line" in *'-->'*) incomment=0 ;; esac
      continue
    fi
    [ "$infence" -eq 1 ] && continue
    case "$line" in *'`'*'`'*'→'*) ;; *) continue ;; esac
    p=$(printf '%s\n' "$line" | sed -n 's/.*`\([^`]*\)`.*/\1/p')
    case "$p" in "~"*) p="$HOME${p#\~}" ;; esac
    [ -d "$p" ] || say "DEAD BINDING: $p (from: $line)"
  done < "$VAULT/_meta/bindings.md"
fi

# --- 6. git remote carries the current name (NOTE only) ----------------------
remote=$(git -C "$VAULT" remote get-url origin 2>/dev/null || true)
if [ -n "$remote" ]; then
  case "$remote" in
    *"$BRAIN_NAME"*) : ;;
    *) printf 'NOTE: vault git remote (%s) does not carry the current name "%s". GitHub redirects, but update it after a repo rename.\n' "$remote" "$BRAIN_NAME" ;;
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

# --- verdict ------------------------------------------------------------------
if [ "$findings" -eq 0 ]; then
  printf 'rename-check: clean — no stale name, vault case-exact, !-blocks expansion-free, frontmatter parses, bindings resolve, manifests agree.\n'
  exit 0
fi
printf 'rename-check: %s finding(s). A stale reference works on APFS and dies silently elsewhere — fix before trusting any scheduled run.\n' "$findings"
exit 1
