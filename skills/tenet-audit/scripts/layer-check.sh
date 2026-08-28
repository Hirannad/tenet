#!/usr/bin/env bash
# layer-check.sh — how many instructions load, and which ones load twice?
#
# The gap this closes is in this plugin, not in the platform. `references/rubric.md`
# scores Layer hygiene out of 15 and `references/layer-map.md` lists duplication and
# undeclared overrides as findings to flag — and until now nothing measured either.
# The cross-layer matrix was prose telling the model to build one by hand ("Build a
# matrix: for each rule…"), which is the same shape as the promise 0.6.0 found in the
# README: a 15-point dimension with no counter behind it. By this repository's own
# rule a claim that breaks twice gets a mechanism or gets deleted, so: a mechanism.
#
# It also answers three of the four diagnostics named in anthropics/claude-code#85477,
# where a Claude Code collaborator confirmed on 2026-08-17 that none of them exist
# natively: "There is no instruction-budget warning, duplicate-rule detection, or
# cross-file conflict detection yet." The fourth — semantic conflict detection — is
# NOT implemented here and says so in its own line rather than being quietly omitted.
#
# WHAT `directives` MEANS, because a number nobody can define is worse than none.
# A directive is a content line that reads as an instruction: a list item, or a line
# carrying a normative token (must, never, always, do not, should, prefer, avoid,
# only, require, ensure, use, don't). Frontmatter, headings, fenced code, HTML
# comments and blank lines are excluded. This is a PROXY, and two limits are stated
# rather than discovered later:
#   * the token list is English. A Hungarian or German instruction file undercounts
#     unless its rules are bulleted — which is why the bullet test comes first.
#   * one directive per line. A paragraph carrying three rules counts once.
# Both make the number an UNDER-estimate, which is the safe direction for a budget.
#
# The budget itself is borrowed, not invented: #85477 cites HumanLayer's finding that
# frontier models reliably follow roughly 150-200 instructions, of which Claude Code's
# own system prompt already spends about 50. So the user's share is ~100-150, and the
# thresholds below are that, named as someone else's measurement.
#
# It never writes, and it never gates. `--record` prints a baseline to stdout and
# leaves the redirect to the user, exactly as surface-check.sh does: a baseline that
# updates itself erases the signal it exists to produce. Exit is always 0 — a broken
# checker must not be able to block a session.
#
# Options:
#   --baseline FILE   baseline to compare against (default: $CLAUDE_CONFIG_DIR/instruction-baseline.json)
#   --record          print today's counts as a baseline to stdout, compare nothing
#   --no-memory       skip the auto-memory tree in the duplication scan
#
# Usage: layer-check.sh [options] [repo ...]     (no repo = current directory)
# Exit:  always 0.

set -uo pipefail

# CLAUDE_CONFIG_DIR relocates Claude Code's config tree, and every script in this
# plugin has honoured it since 2.1.0 — before that one of five did, and the one that
# ignored it was the one whose whole job was reading that tree.
CDIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
BASELINE="$CDIR/instruction-baseline.json"
MODE="compare"
SCAN_MEMORY=1

# Budget, from #85477's cited sources. Named as thresholds so a reader can disagree
# with the number without having to find it in the code.
BUDGET_TOTAL=175      # midpoint of the 150-200 range models reliably follow
BUDGET_SYSTEM=50      # what Claude Code's own system prompt already spends
BUDGET_USER=$(( BUDGET_TOTAL - BUDGET_SYSTEM ))

# A normalized line shorter than this is not compared. "yes", "and", "see below"
# collide across files for reasons that are not duplication, and a cluster report
# full of them is the false-alarm rate that teaches people to stop reading it.
MIN_COMPARE_LEN=25

REPOS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --baseline)  BASELINE="$2"; shift 2 ;;
    --record)    MODE="record"; shift ;;
    --no-memory) SCAN_MEMORY=0; shift ;;
    --) shift; while [ $# -gt 0 ]; do REPOS+=("$1"); shift; done ;;
    -*) shift ;;
    *) REPOS+=("$1"); shift ;;
  esac
done
[ "${#REPOS[@]}" -gt 0 ] || REPOS=("$PWD")

WORK=$(mktemp -d) || { printf 'layer-check: could not create a work directory; measured nothing.\n'; exit 0; }
trap 'rm -rf "$WORK"' EXIT

# --- claudeMdExcludes --------------------------------------------------------
# A file can exist, sit in the load path, and still never load. Reporting it as
# `measured` would inflate every number below it. This is a sed capture rather than
# jq, because jq is declared as exactly one script's dependency and a second user of
# it would make that claim false. The capture handles a flat array on one or more
# lines; anything it cannot parse yields nothing and the layer reads `unmeasured`,
# never a silent pass.
EXCLUDES=""
EXCLUDES_READ=0
for sf in "/Library/Application Support/ClaudeCode/managed-settings.json" \
          "/etc/claude-code/managed-settings.json" \
          "$CDIR/settings.json" "$CDIR/settings.local.json"; do
  [ -r "$sf" ] || continue
  EXCLUDES_READ=1
  got=$(tr -d '\n' < "$sf" \
        | sed -n 's/.*"claudeMdExcludes"[[:space:]]*:[[:space:]]*\[\([^]]*\)\].*/\1/p' \
        | tr ',' '\n' | sed 's/[[:space:]]*"\{0,1\}//; s/"\{0,1\}[[:space:]]*$//' | grep -v '^$' || true)
  [ -n "$got" ] && EXCLUDES="$EXCLUDES
$got"
done

is_excluded() {
  local path="$1" pat
  [ -n "$EXCLUDES" ] || return 1
  while IFS= read -r pat; do
    [ -n "$pat" ] || continue
    # shellcheck disable=SC2254
    case "$path" in $pat) return 0 ;; esac
    case "$path" in *"$pat") return 0 ;; esac
  done <<EOF
$EXCLUDES
EOF
  return 1
}

# --- the counter -------------------------------------------------------------
# Emits, per content line: "D<TAB>normalized<TAB>original" for a directive and
# "C<TAB><TAB>original" for a non-directive content line. Frontmatter, fenced code,
# HTML comments, headings and blanks never reach the output.
count_file() {
  awk '
    function norm(s) {
      s = tolower(s)
      gsub(/^[[:space:]]*([-*+]|[0-9]+\.)[[:space:]]+/, "", s)   # list marker
      gsub(/^[[:space:]]*>+[[:space:]]*/, "", s)                 # blockquote
      gsub(/[`*_~\[\]()]/, "", s)                                # emphasis, code, links
      gsub(/[^a-z0-9 ]/, " ", s)                                 # everything else
      gsub(/[[:space:]]+/, " ", s)
      gsub(/^ | $/, "", s)
      return s
    }
    NR == 1 && $0 == "---" { fm = 1; next }
    fm == 1 { if ($0 == "---") fm = 0; next }
    /^[[:space:]]*(```|~~~)/ { fence = !fence; next }
    fence { next }
    /<!--/ { htm = 1 }
    htm { if ($0 ~ /-->/) htm = 0; next }
    /^[[:space:]]*$/ { next }
    /^[[:space:]]*#/ { next }
    {
      n = norm($0)
      if (n == "") next
      isdir = ($0 ~ /^[[:space:]]*([-*+]|[0-9]+\.)[[:space:]]/) ||
              (n ~ /(^| )(must|never|always|should|shall|require|requires|required|ensure|prefer|avoid|only|do not|dont|use|forbidden|mandatory|no)( |$)/)
      printf "%s\t%s\t%s\n", (isdir ? "D" : "C"), (isdir ? n : ""), $0
    }
  ' "$1" 2>/dev/null
}

# --- layer registration ------------------------------------------------------
# One row per layer, in load order. The layer SET comes from references/layer-map.md's
# "Load order" block and nowhere else — a second hand-written list is the drift this
# whole plugin is about, and it is how an audit comes to report a clean bill on a
# layer it never opened.
: > "$WORK/rows"        # state \t label \t files \t lines \t directives \t note
: > "$WORK/dirs"        # layer-label \t normalized \t original
LAYERS_MEASURED=0

add_row() { printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "${3:-}" "${4:-}" "${5:-}" "${6:-}" >> "$WORK/rows"; }

# Measure a layer from a list of candidate files. Five states, and only one of them
# means "counted": a layer nobody opened is never clean.
measure_layer() {
  local label="$1"; shift
  local files=0 lines=0 dirs=0 excluded=0 unreadable=0 present=0

  for f in "$@"; do
    [ -e "$f" ] || continue
    present=1
    if is_excluded "$f"; then excluded=$(( excluded + 1 )); continue; fi
    if [ ! -r "$f" ]; then unreadable=$(( unreadable + 1 )); continue; fi
    files=$(( files + 1 ))
    while IFS=$'\t' read -r kind n orig; do
      lines=$(( lines + 1 ))
      [ "$kind" = "D" ] || continue
      dirs=$(( dirs + 1 ))
      [ "${#n}" -ge "$MIN_COMPARE_LEN" ] && printf '%s\t%s\t%s\n' "$label" "$n" "$orig" >> "$WORK/dirs"
    done < <(count_file "$f")
  done

  if [ "$present" -eq 0 ]; then
    add_row absent "$label" - - - "no such layer on this machine — not a zero"
  elif [ "$files" -eq 0 ] && [ "$excluded" -gt 0 ]; then
    add_row excluded "$label" "$excluded" - - "claudeMdExcludes matched every file — it exists and does not load"
  elif [ "$files" -eq 0 ] && [ "$unreadable" -gt 0 ]; then
    add_row unreadable "$label" "$unreadable" - - "present but could not be read"
  else
    local note=""
    [ "$excluded" -gt 0 ] && note="${excluded} file(s) excluded by claudeMdExcludes"
    [ "$unreadable" -gt 0 ] && note="${note:+$note; }${unreadable} file(s) unreadable"
    add_row measured "$label" "$files" "$lines" "$dirs" "$note"
    LAYERS_MEASURED=$(( LAYERS_MEASURED + 1 ))
  fi
}

# 1. Managed policy — the one layer no user setting can exclude.
measure_layer "managed policy" \
  "/Library/Application Support/ClaudeCode/CLAUDE.md" \
  "/etc/claude-code/CLAUDE.md" \
  "C:/Program Files/ClaudeCode/CLAUDE.md"

# 2. User layer.
measure_layer "user CLAUDE.md" "$CDIR/CLAUDE.md"
user_rules=()
[ -d "$CDIR/rules" ] && while IFS= read -r f; do user_rules+=("$f"); done < <(find "$CDIR/rules" -name '*.md' -type f 2>/dev/null | sort)
measure_layer "user rules" "${user_rules[@]+"${user_rules[@]}"}"

# 3-4. Project layers, per repo argument.
for repo in "${REPOS[@]}"; do
  if [ ! -d "$repo" ]; then
    add_row absent "project ${repo##*/}" - - - "no such directory"
    continue
  fi
  short="${repo##*/}"
  measure_layer "project $short/CLAUDE.md" "$repo/CLAUDE.md" "$repo/.claude/CLAUDE.md"
  proj_rules=()
  [ -d "$repo/.claude/rules" ] && while IFS= read -r f; do proj_rules+=("$f"); done < <(find "$repo/.claude/rules" -name '*.md' -type f 2>/dev/null | sort)
  measure_layer "project $short/rules" "${proj_rules[@]+"${proj_rules[@]}"}"
  measure_layer "project $short/local" "$repo/CLAUDE.local.md"
done

# 5. Auto memory — duplication scan only, and it is NOT in the budget.
# layer-map.md's sixth cross-layer finding is "Instructions duplicating auto memory":
# auto memory skips what CLAUDE.md already says, so a CLAUDE.md restating accumulated
# preferences pays for the same content twice. inventory.sh already reads this tree
# for the sweep; this connects the two rather than adding a surface. It stays out of
# the budget because the harness meters MEMORY.md separately and double-counting it
# would make the one number this script exists to produce wrong.
MEM_STATE="skipped"
MEM_FILES=0
if [ "$SCAN_MEMORY" -eq 1 ]; then
  if [ ! -d "$CDIR/projects" ]; then
    MEM_STATE="absent"
  else
    mem=()
    while IFS= read -r f; do mem+=("$f"); done < <(find "$CDIR/projects" -path '*/memory/*.md' -type f 2>/dev/null | sort)
    if [ "${#mem[@]}" -eq 0 ]; then
      MEM_STATE="empty"
    else
      MEM_STATE="measured"
      for f in "${mem[@]}"; do
        [ -r "$f" ] || continue
        MEM_FILES=$(( MEM_FILES + 1 ))
        while IFS=$'\t' read -r kind n orig; do
          [ "$kind" = "D" ] || continue
          [ "${#n}" -ge "$MIN_COMPARE_LEN" ] && printf '%s\t%s\t%s\n' "auto memory" "$n" "$orig" >> "$WORK/dirs"
        done < <(count_file "$f")
      done
    fi
  fi
fi

TOTAL_DIRS=$(awk -F'\t' '$1=="measured"{s+=$5} END{print s+0}' "$WORK/rows")

# --- record mode: today's counts as a baseline, on stdout only ---------------
if [ "$MODE" = "record" ]; then
  printf '{\n  "recorded": "%s",\n' "$(date +%Y-%m-%d)"
  printf '  "recorded_by": "layer-check.sh — counts only. The reasoning for an accepted count is the part a diff cannot reconstruct; add it by hand.",\n'
  printf '  "budget": { "total": %s, "system": %s, "user": %s },\n' "$BUDGET_TOTAL" "$BUDGET_SYSTEM" "$BUDGET_USER"
  printf '  "total_directives": %s,\n  "layers": {\n' "$TOTAL_DIRS"
  first=1
  while IFS=$'\t' read -r state label files lines dirs _note; do
    [ "$state" = "measured" ] || continue
    [ "$first" -eq 1 ] || printf ',\n'; first=0
    esc=$(printf '%s' "$label" | sed 's/\\/\\\\/g; s/"/\\"/g')
    printf '    "%s": { "files": %s, "lines": %s, "directives": %s }' "$esc" "$files" "$lines" "$dirs"
  done < "$WORK/rows"
  [ "$first" -eq 1 ] && printf '    ' || printf '\n'
  printf '  }\n}\n'
  if [ "$LAYERS_MEASURED" -eq 0 ]; then
    printf 'layer-check: no layer could be measured, so this baseline records nothing and will read as\nunbaselined next time. Recording it now would freeze a measurement that never happened.\n' >&2
  fi
  exit 0
fi

# --- 1. the layer table ------------------------------------------------------
printf '\n== instruction layers ==\n'
printf '  %-12s %-30s %6s %6s %6s\n' state layer files lines direc
while IFS=$'\t' read -r state label files lines dirs note; do
  printf '  %-12s %-30s %6s %6s %6s' "$state" "$label" "$files" "$lines" "$dirs"
  [ -n "$note" ] && printf '\n               %s' "$note"
  printf '\n'
done < "$WORK/rows"

if [ "$EXCLUDES_READ" -eq 0 ]; then
  printf '  (no settings file was readable, so claudeMdExcludes could not be consulted — an\n   excluded file would have been counted as loading)\n'
fi

# --- 2. the budget -----------------------------------------------------------
printf '\n== instruction budget ==\n'
if [ "$LAYERS_MEASURED" -eq 0 ]; then
  printf '  unmeasured — no layer was opened. This is not a budget of zero.\n'
else
  pct=$(( TOTAL_DIRS * 100 / BUDGET_USER ))
  printf '  %s directive(s) across %s measured layer(s) — %s%% of the ~%s available to you\n' \
    "$TOTAL_DIRS" "$LAYERS_MEASURED" "$pct" "$BUDGET_USER"
  printf '  (~%s total is what models reliably follow; Claude Code'"'"'s system prompt already spends ~%s)\n' \
    "$BUDGET_TOTAL" "$BUDGET_SYSTEM"
  if [ "$TOTAL_DIRS" -gt "$BUDGET_USER" ]; then
    printf '  OVER BUDGET by %s. Past the budget, adherence degrades across ALL instructions rather\n  than only the newest — so trimming is not cosmetic. Path-scoped rules (`paths:` frontmatter)\n  are what actually defers cost; an @-import does not.\n' \
      "$(( TOTAL_DIRS - BUDGET_USER ))"
  elif [ "$pct" -ge 80 ]; then
    printf '  Approaching the budget.\n'
  fi
fi

# --- 3. duplication across layers -------------------------------------------
# Normalized exact match, not semantic similarity, and the report says so. A cluster
# is a normalized directive carried by two or more DISTINCT layers; the same line
# twice inside one layer is that layer's own problem and not a cross-layer finding.
printf '\n== duplication across layers ==\n'
dup_clusters=0
if [ -s "$WORK/dirs" ]; then
  sort -t$'\t' -k2,2 -k1,1 -u "$WORK/dirs" > "$WORK/dirs_u"
  awk -F'\t' '{ c[$2]++; l[$2] = l[$2] ", " $1; t[$2] = $3 }
              END { for (k in c) if (c[k] > 1) printf "%s\t%s\t%s\n", c[k], substr(l[k], 3), t[k] }' \
      "$WORK/dirs_u" | sort -rn > "$WORK/dups"
  dup_clusters=$(wc -l < "$WORK/dups" | tr -d ' ')
  if [ "$dup_clusters" -eq 0 ]; then
    printf '  none — %s comparable directive(s) checked across the layers above%s\n' \
      "$(wc -l < "$WORK/dirs_u" | tr -d ' ')" \
      "$([ "$MEM_STATE" = measured ] && printf ' and the auto-memory tree')"
  else
    while IFS=$'\t' read -r n layers orig; do
      printf '  %s layers: %s\n    %s\n' "$n" "$layers" "$orig"
    done < "$WORK/dups"
    printf '\n  Keep each in the most general layer that is still correct and delete the copy. An\n  @-import deduplicates; it does not reduce context.\n'
  fi
else
  printf '  unmeasured — no directive reached the comparison (nothing readable, or every line\n  shorter than the %s-character floor)\n' "$MIN_COMPARE_LEN"
fi

# --- 4. undeclared-override candidates --------------------------------------
# Two directives in different layers whose normalized forms differ ONLY by a negation
# token. Layers are concatenated rather than replaced, so an unflagged contradiction
# leaves two live rules and the model picks one.
#
# These are CANDIDATES. The script does not judge whether the pair is a real
# contradiction, and it must not: that is the propose-don't-decide line this whole
# plugin holds. A verdict from a string comparison would be a claim with nothing
# behind it — the exact defect this script was written to close.
printf '\n== undeclared-override candidates ==\n'
ovr=0
if [ -s "${WORK}/dirs_u" ]; then
  awk -F'\t' '{
    core = $2
    neg = (core ~ /(^| )(never|not|dont|no|avoid|forbidden|without)( |$)/) ? 1 : 0
    gsub(/(^| )(never|not|dont|no|avoid|forbidden|without)( |$)/, " ", core)
    gsub(/[[:space:]]+/, " ", core); gsub(/^ | $/, "", core)
    if (length(core) < 20) next
    print core "\t" neg "\t" $1 "\t" $3
  }' "$WORK/dirs_u" | sort -t$'\t' -k1,1 > "$WORK/cores"

  # Two distinct LAYERS are required, not merely two lines. A negation pair inside one
  # file is that file contradicting itself — a real finding, but a per-file one, and
  # reporting it here would put it under a heading that says "across layers".
  awk -F'\t' '
    function flush() {
      if (k != "" && pos && negc && nlayer > 1) printf "%s", buf
    }
    { if ($1 != k) { flush(); k = $1; pos = 0; negc = 0; buf = ""; nlayer = 0; delete seen }
      if ($2 == 1) negc = 1; else pos = 1
      if (!($3 in seen)) { seen[$3] = 1; nlayer++ }
      buf = buf sprintf("    [%s] %s\n", $3, $4)
    }
    END { flush() }
  ' "$WORK/cores" > "$WORK/ovr"
  # `grep -c` exits 1 on zero matches, so `grep -c ... || echo 0` printed BOTH its own
  # 0 and the fallback 0 — a two-line "0\n0" that then failed an integer test. Caught
  # by running it, which is the only way this class shows up.
  ovr=$(wc -l < "$WORK/ovr" | tr -d ' ')
  if [ "$ovr" -eq 0 ]; then
    printf '  none — no directive pair across layers differed only by a negation\n'
  else
    printf '  %s line(s) form a negation pair across layers. Candidates, not verdicts:\n' "$ovr"
    cat "$WORK/ovr"
    printf '\n  If the later layer is meant to override the earlier one, say so in the text. An\n  unflagged contradiction leaves both rules live.\n'
  fi
else
  printf '  unmeasured — nothing reached the comparison\n'
fi

# --- 5. what this does NOT do ------------------------------------------------
# enforcement.md's convention: a cell reading `none` alone is worth almost nothing;
# `none` plus the reason is the whole point. This is that cell, for the one diagnostic
# #85477 asks for that a string comparison cannot honestly provide.
printf '\n== semantic conflict detection ==\n'
printf '  none — mechanisable only by a model, not by this script. Two rules can contradict\n'
printf '  each other with no shared wording ("commit early and often" against "one reviewed\n'
printf '  change per PR"), and a string comparison cannot see it. The negation pairs above are\n'
printf '  the mechanical subset; the rest is the audit skill'"'"'s judgement call, and stating that\n'
printf '  is the difference between a gap and a check that quietly passes.\n'

# --- 6. trend against an accepted baseline ----------------------------------
printf '\n== trend ==\n'
if [ ! -r "$BASELINE" ]; then
  printf '  unbaselined — no baseline at %s. Today'"'"'s count is above; there is nothing to compare\n' "$BASELINE"
  printf '  it against. Record it once you have accepted this instruction load as intentional:\n\n'
  printf '    bash "%s" --record %s > "%s.new"\n\n' "$0" "${REPOS[0]}" "$BASELINE"
  printf '  Then read it and move it into place yourself. The redirect truncates its target, so a\n  record that goes wrong must not be pointed at the file you would lose.\n'
else
  was=$(tr -d '\n' < "$BASELINE" | sed -n 's/.*"total_directives"[[:space:]]*:[[:space:]]*\([0-9]\{1,\}\).*/\1/p')
  when=$(tr -d '\n' < "$BASELINE" | sed -n 's/.*"recorded"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
  if [ -z "$was" ]; then
    printf '  unusable — %s exists but carries no readable total_directives. Nothing was compared.\n' "$BASELINE"
  elif [ "$LAYERS_MEASURED" -eq 0 ]; then
    printf '  unmeasured — a baseline of %s exists (recorded %s) but nothing was measured today.\n' "$was" "${when:-undated}"
  elif [ "$TOTAL_DIRS" -gt "$was" ]; then
    printf '  grown    %s → %s directives (+%s) since %s\n' "$was" "$TOTAL_DIRS" "$(( TOTAL_DIRS - was ))" "${when:-undated}"
  elif [ "$TOTAL_DIRS" -lt "$was" ]; then
    printf '  shrunk   %s → %s directives (%s) since %s\n' "$was" "$TOTAL_DIRS" "$(( TOTAL_DIRS - was ))" "${when:-undated}"
  else
    printf '  unchanged at %s directives since %s\n' "$TOTAL_DIRS" "${when:-undated}"
  fi
fi

# --- summary -----------------------------------------------------------------
printf '\nlayer-check: %s directive(s), %s layer(s) measured, %s duplication cluster(s), %s override candidate(s)' \
  "$TOTAL_DIRS" "$LAYERS_MEASURED" "$dup_clusters" "$ovr"
case "$MEM_STATE" in
  measured) printf ', auto memory scanned (%s file(s), duplication only)' "$MEM_FILES" ;;
  absent)   printf ', auto memory absent (not zero — no projects directory)' ;;
  empty)    printf ', auto memory read and held no directives' ;;
  skipped)  printf ', auto memory skipped by --no-memory' ;;
esac
printf '\n'

# Always 0. This reports; enforcement-check.sh and surface-check.sh do the same, and
# a checker that can fail a session is a checker people switch off.
exit 0
