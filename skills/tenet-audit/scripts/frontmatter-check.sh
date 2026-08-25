#!/usr/bin/env bash
# Frontmatter mechanism for the "every .md carries title/type/status/updated" rule.
#
# The rule lived as prose in three project CLAUDE.md files and was violated 13 times
# without anything noticing (2026-08-14 audit). Per the rule that a repeatedly broken rule gets a mechanism or gets deleted,
# a rule that breaks repeatedly gets a mechanism that can fail, or it goes.
#
# Exemptions are declared per repo in <repo>/.claude/frontmatter-exempt — one shell
# glob per line, '#' comments allowed, paths relative to the repo root. A '*' in a
# pattern crosses directory separators. Declaring an exemption is how you say
# "this genre deliberately carries no frontmatter"; an undeclared miss is a defect.
#
# Usage: frontmatter-check.sh [repo ...]     (no args = current directory)
# Exit:  0 = clean, 1 = undeclared violations found.

set -uo pipefail

REQUIRED=(title type status updated)
total_bad=0

check_repo() {
  local repo="$1" exempt_file="$1/.claude/frontmatter-exempt"
  local -a patterns=()
  local bad=0 checked=0 exempted=0

  [[ -d "$repo" ]] || { printf '%s — no such directory\n' "$repo"; return; }

  if [[ -f "$exempt_file" ]]; then
    while IFS= read -r line; do
      line="${line%%#*}"; line="${line#"${line%%[![:space:]]*}"}"; line="${line%"${line##*[![:space:]]}"}"
      [[ -n "$line" ]] && patterns+=("$line")
    done < "$exempt_file"
  fi

  printf '\n== %s ==\n' "${repo##*/}"

  while IFS= read -r file; do
    local rel="${file#"$repo"/}" skip=0
    for pat in "${patterns[@]+"${patterns[@]}"}"; do
      # shellcheck disable=SC2254
      case "$rel" in $pat) skip=1; break ;; esac
    done
    if (( skip )); then exempted=$(( exempted + 1 )); continue; fi

    checked=$(( checked + 1 ))
    if [[ "$(head -n1 "$file")" != "---" ]]; then
      printf '  NO FRONTMATTER  %s\n' "$rel"; bad=$(( bad + 1 )); continue
    fi
    local block missing=""
    block="$(awk 'NR>1{ if ($0=="---") exit; print }' "$file")"
    for key in "${REQUIRED[@]}"; do
      grep -qE "^${key}:[[:space:]]*[^[:space:]]" <<<"$block" || missing+="$key "
    done
    [[ -n "$missing" ]] && { printf '  INCOMPLETE      %s → %s\n' "$rel" "${missing% }"; bad=$(( bad + 1 )); }
  done < <(find "$repo" -name '*.md' -type f \
      -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/.next/*' \
      -not -path '*/dist/*' -not -path '*/build/*' -not -path '*/vendor/*' \
      -not -path '*/.claude/skills/*' | sort)

  printf '  %d checked, %d exempted, %d bad\n' "$checked" "$exempted" "$bad"
  (( ${#patterns[@]} == 0 )) && printf '  (no .claude/frontmatter-exempt — every .md is required to carry it)\n'
  total_bad=$(( total_bad + bad ))
}

if (( $# == 0 )); then check_repo "$PWD"; else for r in "$@"; do check_repo "$r"; done; fi

printf '\nfrontmatter: %d undeclared violation(s)\n' "$total_bad"
(( total_bad == 0 )) || exit 1
