#!/usr/bin/env bash
# promote.sh — the mechanical half of the ledger's review loop.
#
# The user reviews decisions and nothing else. Everything that follows from a
# status change is this script's job, so it can never be forgotten:
#
#   1. Promote  — a reviewed note (status not proposed/unclear) leaves inbox/
#                 for the vault root, where resolve.sh and tenet-sweep can
#                 actually see it. Until 2026-07-28 nothing did this, so the
#                 whole vault was invisible to its own machinery.
#   2. Validate — an unknown status means someone typed into the YAML by hand.
#                 Report it; never guess what was meant.
#   3. Nag      — a backlog in inbox/, or maintenance that has not run in a
#                 week. There is no scheduler; this line is the reminder.
#
# Silent when there is nothing to say. Always exits 0 so hooks never fail.

set -uo pipefail

# Vault location and the loud existence/case check live in lib.sh — one copy,
# not four. Errors go to stdout: the hook swallows stderr.
. "$(dirname "$0")/lib.sh" || { printf 'TENET ERROR: cannot source %s/lib.sh\n' "$(dirname "$0")"; exit 0; }
vault_check --quiet-when-absent || exit 0
INBOX="$VAULT/inbox"
[ -d "$INBOX" ] || { printf 'TENET ERROR: inbox/ missing under %s\n' "$VAULT"; exit 0; }

VALID="proposed accepted rejected unclear superseded reversed resolved"
KEEP_IN_INBOX="proposed unclear" # still awaiting the user

fm() {
  head -n 1 "$1" 2>/dev/null | grep -q '^---$' || return 0
  sed -n '2,/^---$/p' "$1" 2>/dev/null |
    sed -n "s/^$2:[[:space:]]*//p" |
    head -n 1 |
    sed 's/^["'\'']//; s/["'\'']$//'
}

has_word() { case " $1 " in *" $2 "*) return 0 ;; *) return 1 ;; esac; }

# Words in the note body, i.e. everything after the closing frontmatter fence.
body_words() { awk 'n==2{print} /^---$/{n++}' "$1" 2>/dev/null | wc -w | tr -d ' '; }

# Words under one heading, up to the next one.
section_words() { awk -v h="^## $2" '$0 ~ h {f=1;next} /^## /{f=0} f' "$1" 2>/dev/null | wc -w | tr -d ' '; }

promoted=""
invalid=""
toolong=""
unexpanded=""

for f in "$INBOX"/*.md; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  status=$(fm "$f" status)

  # The length caps are the one convention that broke twice on 2026-07-28, and
  # unlike "one decision per note" they are not a judgement call — so they get a
  # check instead of a paragraph. Drafts only: flagging the pre-convention notes
  # in the vault root forever would just train the reader to ignore this.
  #
  # The two caps have different reach on purpose. The body cap is a note-format
  # rule, so it covers gotchas too. The 60-word cap matches a heading, and a
  # gotcha has no Decision section — running it there would report 0 words
  # forever — the silent-zero shape this system bans: a zero that cannot fail
  # is indistinguishable from a check that never looked.
  type=$(fm "$f" type)
  if [ "$type" = "decision" ]; then
    dw=$(section_words "$f" "$SECTION_DECISION")
    [ "${dw:-0}" -gt 60 ] && toolong="$toolong  - $base — ## $SECTION_DECISION: $dw words (max 60)"$'\n'
  fi
  if [ "$type" = "decision" ] || [ "$type" = "gotcha" ]; then
    bw=$(body_words "$f")
    hint=""
    [ "$type" = "decision" ] && hint=" — probably two decisions"
    [ "${bw:-0}" -gt 400 ] && toolong="$toolong  - $base — whole note: $bw words (max 400)$hint"$'\n'
  fi

  # Obsidian expands the templates' {{date:…}} placeholder for a human; nothing
  # expands it on the agent path, and bases/Inbox.base sorts drafts by `created`,
  # so a literal one leaves the "Oldest first" view ordering by a shared non-date.
  # Both capture paths are told to write a real date — this is the part that fails
  # when they do not, instead of a third copy of the instruction.
  if grep -q '{{' "$f" 2>/dev/null; then
    unexpanded="$unexpanded  - $base — $(grep -o '{{[^}]*}}' "$f" | head -n 1 | sed 's/$/ left literal/')"$'\n'
  fi

  if [ -z "$status" ] || ! has_word "$VALID" "$status"; then
    invalid="$invalid  - $base — status: ${status:-(missing)}"$'\n'
    continue
  fi

  has_word "$KEEP_IN_INBOX" "$status" && continue

  if [ -e "$VAULT/$base" ]; then
    invalid="$invalid  - $base — cannot promote, a note of that name already exists in the vault root"$'\n'
    continue
  fi

  if git -C "$VAULT" rev-parse --git-dir >/dev/null 2>&1; then
    git -C "$VAULT" mv "inbox/$base" "$base" 2>/dev/null || mv "$f" "$VAULT/$base"
  else
    mv "$f" "$VAULT/$base"
  fi
  promoted="$promoted  - $base ($status)"$'\n'
done

pending=$(find "$INBOX" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')

# A hyphen in a property name parses as subtraction inside a .base filter, so the
# view goes silently wrong rather than erroring. The enforcement table carried
# `none` for this rule on the argument that "the four property names are fixed" —
# which was already untrue when it was written: raw/ had been holding `kept-under`
# and `source-note` since 2026-07-27, and nobody noticed for weeks. Whole vault,
# not just drafts: that is where the two hid. Silent when clean.
hyphenated=""
bad_categories=""
for f in "$VAULT"/*.md "$VAULT"/inbox/*.md "$VAULT"/raw/*.md "$VAULT"/_meta/*.md "$VAULT"/templates/*.md; do
  [ -f "$f" ] || continue
  head -n 1 "$f" 2>/dev/null | grep -q '^---$' || continue
  keys=$(sed -n '2,/^---$/p' "$f" 2>/dev/null |
    grep -oE '^[a-zA-Z][a-zA-Z0-9_-]*:' | tr -d ':' | grep -E '\-' || true)
  for k in $keys; do
    hyphenated="$hyphenated  - ${f#"$VAULT"/} — $k"$'\n'
  done

  # Same loop, second rule: a categories value must be a quoted wikilink, because
  # [[Methods]] resolves only against ./Methods.md, _meta/Methods.md or
  # inbox/Methods.md — a bare string resolves against nothing and lands in the
  # tally as its own one-note category. The enforcement table carried a bare
  # `none` for this with no reason, which its own preamble calls worth almost
  # nothing, and on 2026-08-28 a draft arrived with two lowercase Hungarian
  # strings here and was one review away from the vault root.
  #
  # The block scan stops at the closing fence AND at the next top-level key. Both
  # guards are load-bearing: a categories block that sits last in the frontmatter
  # ran the scan into the body in inventory.sh until 0.5.0, and every prose
  # wikilink in the note landed in the result.
  # templates/ is excluded from THIS rule but not from the one above, and the
  # split is deliberate. A hyphenated property *name* in a template propagates to
  # every note made from it, so it belongs in the check. A category *value* in a
  # template is a placeholder — all five ship `- ""` — and flagging them fired on
  # five of five on the first run: the false-alarm rate that teaches a reader to
  # skip the digest. Same reason every .base view excludes templates by filename.
  case "$f" in "$VAULT"/templates/*) continue ;; esac

  cats=$(sed -n '2,/^---$/p' "$f" 2>/dev/null |
    awk '/^categories:/{c=1;next} /^---$/{c=0} /^[a-z_]+:/{c=0} c' |
    grep -E '^[[:space:]]*-' |
    grep -vE '^[[:space:]]*-[[:space:]]*"\[\[[^]]+\]\]"[[:space:]]*$' || true)
  while IFS= read -r c; do
    [ -n "$c" ] || continue
    bad_categories="$bad_categories  - ${f#"$VAULT"/} — $(printf '%s' "$c" | sed 's/^[[:space:]]*-[[:space:]]*//')"$'\n'
  done <<<"$cats"
done

# A convention may enter without a
# mechanism, but never without being marked. The enforcement table in
# conventions.md carries one row per rule; an empty "what catches it" cell means
# nobody ever asked the question, and that gap is what this counts. A cell
# reading "none" is a valid answer and deliberately not reported — the point is
# to kill the silent third state, not to nag about judgement calls.
#
# The counting itself lives in the auditor's enforcement-check.sh — one script,
# two targets (this table and the global CLAUDE.md's). Until 2026-08-15 this
# block carried its own copy of that logic.
# Plugin-relative, both of them. The pre-plugin ~/.claude/skills fallbacks are
# gone with that directory — and one of them never resolved anyway: it read
# skills/tenet-audit, while the pre-plugin directory was named claude-md-auditor.
# A fallback nobody could reach is indistinguishable from no fallback, except
# that it reads like cover.
CONVENTIONS="$(dirname "$0")/../references/conventions.md"
CELLCHECK="$(dirname "$0")/../../tenet-audit/scripts/enforcement-check.sh"
unmarked=0
missing_table=""
missing_checker=""
if [ -f "$CONVENTIONS" ]; then
  if [ -r "$CELLCHECK" ]; then
    out=$(bash "$CELLCHECK" --empty-only --table "$CONVENTIONS" --section "Enforcement" --header "Convention" 2>/dev/null)
    case "$out" in
      MISSING) missing_table="yes" ;;
      ''|*[!0-9]*) missing_checker="yes" ;; # garbage output is as loud as absence
      *) unmarked="$out" ;;
    esac
  else
    missing_checker="yes"
  fi
fi

# Maintenance has no scheduler behind it, so its age has to be surfaced here.
last_digest=$(find "$VAULT/_meta" -maxdepth 1 -name 'maintenance-*.md' 2>/dev/null | sort | tail -1)
stale_maintenance=""
if [ -z "$last_digest" ]; then
  stale_maintenance="never run"
elif [ -n "$(find "$last_digest" -mtime +7 2>/dev/null)" ]; then
  stale_maintenance="last run $(basename "$last_digest" .md | sed 's/^maintenance-//')"
fi

[ -z "$promoted" ] && [ -z "$invalid" ] && [ -z "$toolong" ] && [ -z "$unexpanded" ] && [ -z "$hyphenated" ] && [ -z "$bad_categories" ] && [ "${pending:-0}" -lt 3 ] && [ -z "$stale_maintenance" ] && [ "${unmarked:-0}" -eq 0 ] && [ -z "$missing_table" ] && [ -z "$missing_checker" ] && exit 0

printf 'TENET INBOX\n'
[ -n "$promoted" ] && printf 'Promoted to the vault root:\n%s' "$promoted"
[ -n "$invalid" ] && printf 'Needs attention — off-vocabulary status, left in inbox/ (valid: %s):\n%s' "$VALID" "$invalid"
[ -n "$toolong" ] && printf 'Over the length caps — rewrite or split before asking for a verdict:\n%s' "$toolong"
[ -n "$unexpanded" ] && printf 'Template placeholder left literal — Obsidian expands these, the agent path does not:\n%s' "$unexpanded"
[ -n "$hyphenated" ] && printf 'Hyphenated property name(s) — a hyphen parses as subtraction in a .base filter:\n%s' "$hyphenated"
[ -n "$bad_categories" ] && printf 'Category value(s) that are not a quoted wikilink — these resolve to no hub:\n%s' "$bad_categories"
[ "${pending:-0}" -ge 3 ] && printf '%s drafts are waiting for review. Run /tenet:tenet-capture review.\n' "$pending"
[ -n "$stale_maintenance" ] && printf 'Maintenance is due (%s). Run /tenet:tenet-sweep.\n' "$stale_maintenance"
[ "${unmarked:-0}" -gt 0 ] && printf '%s convention(s) in conventions.md have no enforcement cell. Fill them or write "none" with a reason.\n' "$unmarked"
[ -n "$missing_table" ] && printf 'The Enforcement table is gone from conventions.md — no convention is marked any more.\n'
[ -n "$missing_checker" ] && printf 'enforcement-check.sh is missing or broke (%s) — the conventions table went unchecked this session.\n' "$CELLCHECK"

exit 0
