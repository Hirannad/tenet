#!/usr/bin/env bash
# Inventory dump for the weekly maintenance run.
#
# This lives in a script rather than a ```! block in SKILL.md because that block
# is preprocessed by a shell that rejects expansions it would have to perform —
# ${VAR:-default} and $(...) both fail with "Contains expansion". The block
# therefore never ran, and the model improvised ~25 ad-hoc shell commands every
# run to replace it, each a fresh permission decision. One pre-approved script
# ends that.
#
# ${CLAUDE_PLUGIN_ROOT} is the exception, verified 2026-08-16: the plugin loader
# substitutes it before the check, so the shell never sees an expansion. That is
# what the SKILL.md invocation uses. $HOME and $(...) still fail — rename-check.sh
# check 3 knows the difference and scans both skill trees.

set -uo pipefail

# Vault location comes from the shared lib (one copy, not four); it also does
# the loud existence + case-exactness check. This script used to `exit 0` on a
# missing vault — that exact silence is how the 2026-08-10 scheduled run died
# with no trace after the Brain→brain rename. Plugin-relative only: the
# pre-plugin ~/.claude/skills copies are gone, and a fallback to a path that no
# longer exists hides which layout actually resolved.
_lib="$(dirname "$0")/../../tenet/scripts/lib.sh"
[ -r "$_lib" ] && . "$_lib"
if [ -z "${VAULT:-}" ]; then
  echo "TENET ERROR: cannot find tenet/scripts/lib.sh — was the tenet skill renamed? Run rename-check.sh."
  exit 1
fi
V="$VAULT"
vault_check || exit 1
cd "$V" || exit 1

echo "Vault: $V"
echo "Notes: $(find . -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"
echo "Drafts pending: $(find inbox -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
# Two numbers, not one. The ~15 threshold in check 6 measures the layer loaded
# into every session, and resolve.sh skips gotchas — so counting them here would
# raise the number without a byte more context being loaded, which is a false
# alarm on the check's own terms. The gotcha count is separate because it is the
# data check 1 needs: the gotcha type reverses itself below three in half a year,
# and until this line existed nothing could observe that.
universal=0
gotchas=0
for f in ./*.md; do
  [ -f "$f" ] || continue
  if grep -q '^type: gotcha' "$f" 2>/dev/null; then
    gotchas=$((gotchas + 1))
    continue
  fi
  grep -q '^scope: universal' "$f" 2>/dev/null && universal=$((universal + 1))
done
echo "Universal notes (excl. gotchas): $universal"
echo "Gotchas: $gotchas"
echo "Raw files: $(find raw -maxdepth 1 -type f ! -name '.gitkeep' 2>/dev/null | wc -l | tr -d ' ')"
echo

echo "--- decisions with a revisit condition ---"
grep -H '^revisit:' *.md 2>/dev/null | grep -v '^revisit:[[:space:]]*$' | sed 's|^|  |' | head -n 40
echo

echo "--- drafts older than 14 days ---"
find inbox -maxdepth 1 -name '*.md' -mtime +14 2>/dev/null | sed 's|^|  |'
echo

# Everything below replaces shell the model used to improvise each run.

# Date-prefixed, not year-pinned. These two loops globbed ./2026-*.md until
# 0.4.1, so every note created in another year was invisible to them and both
# sections reported nothing rather than failing — the silent zero this system
# bans. The count below is what makes that failure loud if the glob ever misses.
NOTE_GLOB='./[0-9][0-9][0-9][0-9]-*.md'

echo "--- type + status per root note ---"
seen=0
for f in $NOTE_GLOB; do
  [ -f "$f" ] || continue
  seen=$((seen + 1))
  printf '  %-52s type=%-9s status=%s\n' "$(basename "$f")" \
    "$(grep -m1 '^type:' "$f" | sed 's/type:[[:space:]]*//')" \
    "$(grep -m1 '^status:' "$f" | sed 's/status:[[:space:]]*//')"
done
# Notes: counts every root .md; this loop counts the date-prefixed ones. A gap
# means notes are misnamed, not that the vault is empty.
[ "$seen" -eq 0 ] && echo "  (no date-prefixed notes matched — check naming, not just emptiness)"
echo

echo "--- word counts over the caps (400 body / 60 $SECTION_DECISION) ---"
for f in $NOTE_GLOB inbox/*.md; do
  [ -f "$f" ] || continue
  bw=$(awk 'n==2{print} /^---$/{n++}' "$f" | wc -w | tr -d ' ')
  # The body cap stays unguarded on purpose, unlike promote.sh's, which restricts
  # it to decision|gotcha. promote.sh only ever walks inbox/, so this loop is the
  # only thing that can catch an over-long note already sitting in the root —
  # narrowing it to match would silence live findings on other types.
  [ "${bw:-0}" -gt 400 ] && echo "  $(basename "$f"): body $bw"
  # The 60-word cap matches a heading, so it only means anything on a decision.
  # Run unguarded it scored every gotcha, source and open note at zero words —
  # a number that could never fail, which is not a passing check.
  if grep -q '^type: decision' "$f" 2>/dev/null; then
    dw=$(awk -v h="## $SECTION_DECISION" '$0==h{f=1;next} /^## /{f=0} f' "$f" | wc -w | tr -d ' ')
    if [ -z "$(grep -m1 "^## $SECTION_DECISION\$" "$f")" ]; then
      echo "  $(basename "$f"): no '## $SECTION_DECISION' section — check the locale, not the note"
    elif [ "${dw:-0}" -gt 60 ]; then
      echo "  $(basename "$f"): $SECTION_DECISION $dw"
    fi
  fi
done
echo

echo "--- categories tally ---"
# Stop at the closing --- as well as at the next key: a categories block that sits
# last in the frontmatter used to run the scan into the body, so every wikilink in
# the prose landed in the tally as if it were a category.
awk '/^categories:/{c=1;next} /^---$/{c=0} /^[a-z_]+:/{c=0} c' *.md 2>/dev/null \
  | grep -o '\[\[[^]]*\]\]' | tr -d '[]' | sort | uniq -c | sort -rn | sed 's|^|  |'
echo

echo "--- dead wikilinks ---"
grep -ohE '\[\[[^]]+\]\]' *.md _meta/*.md inbox/*.md 2>/dev/null | tr -d '[]' | sort -u \
  | while read -r t; do
      [ -f "$t.md" ] || [ -f "_meta/$t.md" ] || [ -f "inbox/$t.md" ] || echo "  $t"
    done
echo

echo "--- process deviations (native auto memory, type: feedback) ---"
# The plugin stopped collecting corrections itself in 2.0.0: Claude Code's auto memory
# already records them as `feedback` notes, and two records of the same thing is the
# redundancy this release removed. What is left here is the half the platform does not
# do — turning a repeat into a verdict (check 9).
#
# Every branch below prints a status line, because each way of finding nothing looks
# identical in the output and means something different. A disabled memory, a relocated
# directory read at the wrong path, and a genuinely clean record all yield zero entries;
# reporting "no deviations" for the first two is the silent zero this system bans.
#
# jq is deliberately not used: it is declared as exactly one script's dependency
# (surface-check.sh), and a second one would falsify the README. So the two settings are
# read with a sed capture, and a settings file that exists but yields nothing says so.
CDIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SETTINGS="$CDIR/settings.json"
mem_root=""
mem_note=""

if [ -n "${CLAUDE_CODE_DISABLE_AUTO_MEMORY:-}" ]; then
  echo "  status: auto memory is off (CLAUDE_CODE_DISABLE_AUTO_MEMORY is set). Nothing was read —"
  echo "          that is not the same as no deviations. Check 9 has no input this run."
elif [ ! -r "$SETTINGS" ]; then
  mem_root="$CDIR/projects"
  mem_note="no readable $SETTINGS, so a relocated directory could not be ruled out"
else
  if sed -n 's/.*"autoMemoryEnabled"[[:space:]]*:[[:space:]]*false.*/off/p' "$SETTINGS" | grep -q off; then
    echo "  status: auto memory is off (autoMemoryEnabled false in $SETTINGS). Nothing was read —"
    echo "          that is not the same as no deviations. Check 9 has no input this run."
  else
    custom=$(sed -n 's/.*"autoMemoryDirectory"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$SETTINGS" | head -n 1)
    case "$custom" in
      "~/"*) mem_root="$HOME/${custom#\~/}"; mem_note="relocated by autoMemoryDirectory" ;;
      "")    mem_root="$CDIR/projects" ;;
      *)     mem_root="$custom"; mem_note="relocated by autoMemoryDirectory" ;;
    esac
  fi
fi

if [ -n "$mem_root" ]; then
  if [ ! -d "$mem_root" ]; then
    echo "  status: nothing at $mem_root${mem_note:+ ($mem_note)} — no record to read, which is not"
    echo "          the same as a clean record. Check 9 has no input this run."
  else
    # Recursive on purpose: the per-project layout is <root>/<project>/memory/, but a
    # relocated root is documented only as "a different location" and may be flat. One
    # find covers both rather than guessing which, and a guess here reads as zero.
    fb=$(find "$mem_root" -name '*.md' -type f -exec grep -lE '^[[:space:]]*type:[[:space:]]*feedback' {} + 2>/dev/null | sort)
    count=$(printf '%s' "$fb" | grep -c . || true)
    if [ "${count:-0}" -eq 0 ]; then
      total=$(find "$mem_root" -name '*.md' -type f 2>/dev/null | wc -l | tr -d ' ')
      echo "  status: $mem_root holds $total memory note(s)${mem_note:+ ($mem_note)}, none of type feedback."
      echo "          A real zero: the record was read and holds no corrections."
    else
      echo "  status: $count feedback note(s) under $mem_root${mem_note:+ ($mem_note)}."
      echo "          Native auto memory is per-repository, so these span projects by design."
      printf '%s\n' "$fb" | while IFS= read -r f; do
        [ -n "$f" ] || continue
        proj=$(printf '%s' "$f" | sed "s|^$mem_root/||; s|/memory/.*||; s|/[^/]*\.md$||")
        desc=$(sed -n 's/^description:[[:space:]]*//p' "$f" | head -n 1)
        printf '  %-34s %-36s %s\n' "${proj:-.}" "$(basename "$f")" "${desc:-(no description)}"
      done
    fi
  fi
fi
echo

echo "--- git status ---"
git status --short 2>/dev/null | sed 's|^|  |'
