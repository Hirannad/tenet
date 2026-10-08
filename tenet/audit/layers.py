"""How many instructions load, and which ones load twice.

It answers three of the four diagnostics anthropics/claude-code#85477 names as missing: an
instruction budget, duplicate rules across layers, and cross-file conflicts narrowed to negation
pairs. The fourth, semantic conflict detection, is Claude Code's own `/doctor prompt-audit`; its
section here says so rather than quietly omitting it.

A directive is a content line that reads as an instruction: a list item, or a line carrying a
normative token (must, never, always, should, prefer, avoid, only, use, do not, ...).
Frontmatter, headings, fenced code, HTML comments and blank lines are excluded. It is a proxy with
two stated limits: the tokens are English, so an unbulleted Hungarian rule is missed, and a
paragraph holding three rules counts once. Both undercount, the safe direction for a budget.

It never writes and never gates. `--record` prints a baseline for the user to move into place,
because a baseline that updates itself erases the signal it exists to produce; the exit is always
0, because a checker that can fail a session is a checker people switch off.

Options: --baseline FILE, --record, --no-memory, then repo paths (none = the current directory).
"""
import fnmatch
import itertools
import os
import re
import stat
import string
import sys
from datetime import date

from tenet import paths

# Borrowed, not invented: #85477 cites HumanLayer's finding that frontier models reliably follow
# roughly 150-200 instructions, of which Claude Code's own system prompt already spends about 50.
BUDGET_TOTAL = 175
BUDGET_SYSTEM = 50
BUDGET_USER = BUDGET_TOTAL - BUDGET_SYSTEM

# Shorter normalized lines ("yes", "see below") collide for reasons that are not duplication, and a
# cluster report full of them teaches people to stop reading it.
MIN_COMPARE_LEN = 25

# Managed policy on macOS and Linux: the one layer no user setting can exclude.
MANAGED = ("/Library/Application Support/ClaudeCode", "/etc/claude-code")

_SP = r"[ \t\n\r\f\v]"  # POSIX [[:space:]]; \s would also match Unicode spaces
_LOWER = str.maketrans(string.ascii_uppercase, string.ascii_lowercase)
_LIST_ITEM = re.compile(rf"^{_SP}*([-*+]|[0-9]+\.){_SP}")
_LIST_MARKER = re.compile(rf"^{_SP}*([-*+]|[0-9]+\.){_SP}+")
_QUOTE = re.compile(rf"^{_SP}*>+{_SP}*")
_MARKUP = re.compile(r"[`*_~\[\]()]")
_OTHER = re.compile(r"[^a-z0-9 ]")
_FENCE = re.compile(rf"^{_SP}*(```|~~~)")
_BLANK = re.compile(rf"{_SP}*")
_HEADING = re.compile(rf"^{_SP}*#")
_NORMATIVE = re.compile(r"(^| )(must|never|always|should|shall|require|requires|required|ensure|"
                        r"prefer|avoid|only|do not|dont|use|forbidden|mandatory|no)( |$)")
_NEGATION = re.compile(r"(^| )(never|not|dont|no|avoid|forbidden|without)( |$)")

# claudeMdExcludes is matched as text rather than parsed as JSON, so a settings file that is not
# valid JSON still yields its patterns. The greedy lead takes the last occurrence.
_EXCLUDES = re.compile(rf'.*"claudeMdExcludes"{_SP}*:{_SP}*\[([^]]*)\]')
_LEAD = re.compile(rf'^{_SP}*"?')
_TRAIL = re.compile(rf'"?{_SP}*$')
_WAS = re.compile(rf'.*"total_directives"{_SP}*:{_SP}*([0-9]+)')
_WHEN = re.compile(rf'.*"recorded"{_SP}*:{_SP}*"([^"]*)"')


def _b(s):
    return s.encode("utf-8", "surrogateescape")


def _read(path):
    # Bytes that are not UTF-8 survive to the report; newline="" keeps a CRLF file's \r in place.
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as f:
        return f.read()


def _files_under(top, keep):
    """Sorted regular files below top whose path passes keep. Symlinks are followed, as Claude
    Code follows them for shared rules; a directory reached twice is walked once."""
    found, seen = [], set()
    for root, dirs, names in os.walk(top, followlinks=True):
        real = os.path.realpath(root)
        if real in seen:
            dirs[:] = []
            continue
        seen.add(real)
        for path in (os.path.join(root, name) for name in names):
            try:
                if keep(path) and stat.S_ISREG(os.stat(path).st_mode):
                    found.append(path)
            except OSError:
                pass
    return sorted(found, key=_b)  # byte order, so the report is the same under any locale


def _is_md(path):
    return path.endswith(".md")


def normalize(line):
    s = _LIST_MARKER.sub("", line.translate(_LOWER), count=1)
    s = _MARKUP.sub("", _QUOTE.sub("", s, count=1))
    return " ".join(_OTHER.sub(" ", s).split())


def scan(text):
    """(content lines, [(normalized, line)] for the directives among them)."""
    records = text.split("\n")
    if records[-1] == "":
        records.pop()  # a final newline ends the last line; it does not start another
    count, found = 0, []
    fm = fence = htm = False
    for i, line in enumerate(records):
        if i == 0 and line == "---":
            fm = True
            continue
        if fm:
            fm = line != "---"
            continue
        if _FENCE.match(line):
            fence = not fence
            continue
        if fence:
            continue
        if "<!--" in line:
            htm = True
        if htm:
            htm = "-->" not in line
            continue
        if _BLANK.fullmatch(line) or _HEADING.match(line):
            continue
        n = normalize(line)
        if not n:
            continue
        count += 1
        if _LIST_ITEM.match(line) or _NORMATIVE.search(n):
            found.append((n, line))
    return count, found


def _shown(line):
    # A reported rule stays on one line of its own: outer tabs dropped, cut at the first inner one.
    return line.strip("\t").split("\t")[0]


def _excludes(text):
    m = _EXCLUDES.match(text.replace("\n", ""))
    if not m:
        return []
    pats = (_TRAIL.sub("", _LEAD.sub("", p, count=1), count=1) for p in m.group(1).split(","))
    return [p for p in pats if p]


def _pwd():
    # The shell's logical directory, so a repo reached through a symlink keeps the name it was given.
    pwd = os.environ.get("PWD", "")
    try:
        if os.path.isabs(pwd) and os.path.samefile(pwd, "."):
            return pwd
    except OSError:
        pass
    return os.getcwd()


def _parse(argv, cdir):
    baseline, record, memory, repos = cdir + "/instruction-baseline.json", False, True, []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--baseline" and i + 1 < len(argv):
            baseline = argv[i + 1]
            i += 1
        elif arg == "--record":
            record = True
        elif arg == "--no-memory":
            memory = False
        elif arg == "--":
            repos += argv[i + 1:]
            break
        elif not arg.startswith("-"):
            repos.append(arg)
        i += 1
    return baseline, record, memory, repos or [_pwd()]


def run(argv):
    """(stdout, stderr) of one run. Reads only; nothing is written anywhere."""
    cdir = str(paths.config_dir())
    baseline, record, memory, repos = _parse(argv, cdir)

    # A file can sit in the load path and still never load; counting it would inflate every number.
    excludes, excludes_read = [], False
    for sf in [m + "/managed-settings.json" for m in MANAGED] + [cdir + "/settings.json", cdir + "/settings.local.json"]:
        try:
            text = _read(sf)
        except OSError:
            continue
        excludes_read = True
        excludes += _excludes(text)

    def excluded(path):
        return any(fnmatch.fnmatchcase(path, p) or path.endswith(p) for p in excludes)

    rows, directives = [], []  # (state, label, files, lines, directives, note); (label, normalized, shown)

    # Five states, one of which means counted: a layer nobody opened is never clean.
    def measure(label, candidates):
        files = lines = dirs = n_excluded = n_unreadable = 0
        present = False
        for f in candidates:
            if not os.path.exists(f):
                continue
            present = True
            if excluded(f):
                n_excluded += 1
                continue
            try:
                text = _read(f)
            except OSError:  # a directory named CLAUDE.md too: present, and not a zero
                n_unreadable += 1
                continue
            files += 1
            count, found = scan(text)
            lines += count
            dirs += len(found)
            directives.extend((label, n, _shown(line)) for n, line in found if len(n) >= MIN_COMPARE_LEN)
        if not present:
            rows.append(("absent", label, "-", "-", "-", "no such layer on this machine — not a zero"))
        elif files == 0 and n_excluded:
            rows.append(("excluded", label, n_excluded, "-", "-",
                         "claudeMdExcludes matched every file — it exists and does not load"))
        elif files == 0 and n_unreadable:
            rows.append(("unreadable", label, n_unreadable, "-", "-", "present but could not be read"))
        else:
            note = "; ".join(s for s in (n_excluded and f"{n_excluded} file(s) excluded by claudeMdExcludes",
                                         n_unreadable and f"{n_unreadable} file(s) unreadable") if s)
            rows.append(("measured", label, files, lines, dirs, note))

    # The layer set follows references/layer-map.md's load order; a second list is how an audit
    # comes to report a clean bill on a layer it never opened.
    measure("managed policy", [m + "/CLAUDE.md" for m in MANAGED])
    measure("user CLAUDE.md", [cdir + "/CLAUDE.md"])
    measure("user rules", _files_under(cdir + "/rules", _is_md))
    for repo in repos:
        short = repo[repo.rfind("/") + 1:]
        if not os.path.isdir(repo):
            rows.append(("absent", f"project {short}", "-", "-", "-", "no such directory"))
            continue
        claude_md = [repo + "/CLAUDE.md", repo + "/.claude/CLAUDE.md"]
        # Claude Code (2.1.277+) reads AGENTS.md instead in a project that has no CLAUDE.md.
        if not any(os.path.exists(f) for f in claude_md) and os.path.exists(repo + "/AGENTS.md"):
            measure(f"project {short}/AGENTS.md", [repo + "/AGENTS.md"])
        else:
            measure(f"project {short}/CLAUDE.md", claude_md)
        measure(f"project {short}/rules", _files_under(repo + "/.claude/rules", _is_md))
        measure(f"project {short}/local", [repo + "/CLAUDE.local.md"])

    # Auto memory joins the duplication scan only: the harness meters MEMORY.md separately, so
    # counting it in the budget would make the one number this exists to produce wrong.
    mem_state, mem_files, mem_note = "skipped", 0, ""
    if memory:
        root, mem_note = paths.memory_root()
        if root is None:
            mem_state = "off"
        elif not root.is_dir():
            mem_state = "absent"
        else:
            relocated = root != paths.config_dir() / "projects"
            mem = _files_under(str(root), _is_md if relocated else lambda f: fnmatch.fnmatchcase(f, "*/memory/*.md"))
            mem_state = "measured" if mem else "empty"
            for f in mem:
                try:
                    text = _read(f)
                except OSError:
                    continue
                mem_files += 1
                directives.extend(("auto memory", n, _shown(line)) for n, line in scan(text)[1]
                                  if len(n) >= MIN_COMPARE_LEN)

    measured = [r for r in rows if r[0] == "measured"]
    total = sum(r[4] for r in measured)

    if record:
        def esc(s):
            return s.replace("\\", "\\\\").replace('"', '\\"')
        layers = ",\n".join('    "{}": {{ "files": {}, "lines": {}, "directives": {} }}'.format(esc(r[1]), *r[2:5])
                            for r in measured)
        out = ('{\n'
               f'  "recorded": "{date.today().isoformat()}",\n'
               '  "recorded_by": "tenet audit layers — counts only. The reasoning for an accepted count is the part '
               'a diff cannot reconstruct; add it by hand.",\n'
               f'  "budget": {{ "total": {BUDGET_TOTAL}, "system": {BUDGET_SYSTEM}, "user": {BUDGET_USER} }},\n'
               f'  "total_directives": {total},\n  "layers": {{\n'
               + (layers + "\n" if layers else "    ") + "  }\n}\n")
        err = "" if measured else (
            "layer-check: no layer could be measured, so this baseline records nothing and will read as\n"
            "unbaselined next time. Recording it now would freeze a measurement that never happened.\n")
        return out, err

    out = []
    p = out.append

    p("\n== instruction layers ==\n")
    p("  %-12s %-30s %6s %6s %6s\n" % ("state", "layer", "files", "lines", "direc"))
    for state, label, files, lines, dirs, note in rows:
        p("  %-12s %-30s %6s %6s %6s" % (state, label, files, lines, dirs))
        if note:
            p("\n               %s" % note)
        p("\n")
    if not excludes_read:
        p("  (no settings file was readable, so claudeMdExcludes could not be consulted — an\n"
          "   excluded file would have been counted as loading)\n")

    p("\n== instruction budget ==\n")
    if not measured:
        p("  unmeasured — no layer was opened. This is not a budget of zero.\n")
    else:
        pct = total * 100 // BUDGET_USER
        p("  %d directive(s) across %d measured layer(s) — %d%% of the ~%d available to you\n"
          % (total, len(measured), pct, BUDGET_USER))
        p("  (~%d total is what models reliably follow; Claude Code's system prompt already spends ~%d)\n"
          % (BUDGET_TOTAL, BUDGET_SYSTEM))
        if total > BUDGET_USER:
            p("  OVER BUDGET by %d. Past the budget, adherence degrades across ALL instructions rather\n"
              "  than only the newest — so trimming is not cosmetic. Path-scoped rules (`paths:` frontmatter)\n"
              "  are what actually defers cost; an @-import does not.\n" % (total - BUDGET_USER))
        elif pct >= 80:
            p("  Approaching the budget.\n")

    # Normalized exact match, not similarity. A cluster is a directive carried by two or more
    # distinct layers; the same line twice in one layer is that layer's problem, not a cross-layer one.
    p("\n== duplication across layers ==\n")
    clusters, candidates = [], []
    if directives:
        unique = {}
        for label, n, shown in directives:
            unique.setdefault((n, label), shown)
        ordered = sorted(unique.items(), key=lambda kv: (_b(kv[0][0]), _b(kv[0][1])))
        by_rule = {}
        for (n, label), shown in ordered:
            entry = by_rule.setdefault(n, [[], None])
            entry[0].append(label)
            entry[1] = shown
        clusters = [(len(labels), ", ".join(labels), shown) for labels, shown in by_rule.values() if len(labels) > 1]
        # Most layers first; ties in a fixed order, so two runs over the same files diff clean.
        clusters.sort(key=lambda c: (c[0], _b("%d\t%s\t%s" % c)), reverse=True)
        if not clusters:
            p("  none — %d comparable directive(s) checked across the layers above%s\n"
              % (len(ordered), " and the auto-memory tree" if mem_state == "measured" else ""))
        else:
            for c in clusters:
                p("  %d layers: %s\n    %s\n" % c)
            p("\n  Keep each in the most general layer that is still correct and delete the copy. An\n"
              "  @-import deduplicates; it does not reduce context.\n")
    else:
        p("  unmeasured — no directive reached the comparison (nothing readable, or every line\n"
          "  shorter than the %d-character floor)\n" % MIN_COMPARE_LEN)

    # Two directives in different layers whose normalized forms differ only by a negation token.
    # Layers are concatenated, so an unflagged contradiction leaves two live rules. These are
    # candidates: judging them is the audit skill's call, and a verdict from a string comparison
    # would be a claim with nothing behind it.
    p("\n== undeclared-override candidates ==\n")
    if directives:
        cores = []
        for (n, label), shown in ordered:
            core = " ".join(_NEGATION.sub(" ", n).split())
            if len(core) >= 20:
                cores.append((core, "1" if _NEGATION.search(n) else "0", label, shown))
        cores.sort(key=lambda r: (_b(r[0]), _b("\t".join(r))))
        for _core, group in itertools.groupby(cores, key=lambda r: r[0]):
            group = list(group)
            # Two distinct layers, not merely two lines: a file contradicting itself is a per-file finding.
            if len({r[1] for r in group}) == 2 and len({r[2] for r in group}) > 1:
                candidates += ["    [%s] %s\n" % (r[2], r[3]) for r in group]
        if not candidates:
            p("  none — no directive pair across layers differed only by a negation\n")
        else:
            p("  %d line(s) form a negation pair across layers. Candidates, not verdicts:\n" % len(candidates))
            out += candidates
            p("\n  If the later layer is meant to override the earlier one, say so in the text. An\n"
              "  unflagged contradiction leaves both rules live.\n")
    else:
        p("  unmeasured — nothing reached the comparison\n")

    # A cell reading `none` alone is worth almost nothing; `none` plus the reason is the point.
    p("\n== semantic conflict detection ==\n"
      "  none — mechanisable only by a model, not by this script. Two rules can contradict\n"
      "  each other with no shared wording (\"commit early and often\" against \"one reviewed\n"
      "  change per PR\"), and a string comparison cannot see it. The negation pairs above are\n"
      "  the mechanical subset; for the rest, Claude Code's own `/doctor prompt-audit` reports\n"
      "  instruction files that contradict each other.\n")

    p("\n== trend ==\n")
    if not os.access(baseline, os.R_OK):
        p("  unbaselined — no baseline at %s. Today's count is above; there is nothing to compare\n" % baseline)
        p("  it against. Record it once you have accepted this instruction load as intentional:\n\n")
        p('    python3 "%s" audit layers --record %s > "%s.new"\n\n' % (paths.CLI, repos[0], baseline))
        p("  Then read it and move it into place yourself. The redirect truncates its target, so a\n"
          "  record that goes wrong must not be pointed at the file you would lose.\n")
    else:
        try:
            text = _read(baseline).replace("\n", "")
        except OSError:
            text = ""
        was, when = _WAS.match(text), _WHEN.match(text)
        when = when.group(1) if when and when.group(1) else "undated"
        if not was:
            p("  unusable — %s exists but carries no readable total_directives. Nothing was compared.\n" % baseline)
        elif not measured:
            p("  unmeasured — a baseline of %s exists (recorded %s) but nothing was measured today.\n"
              % (was.group(1), when))
        else:
            before = int(was.group(1))
            if total > before:
                p("  grown    %s → %d directives (+%d) since %s\n" % (was.group(1), total, total - before, when))
            elif total < before:
                p("  shrunk   %s → %d directives (%d) since %s\n" % (was.group(1), total, total - before, when))
            else:
                p("  unchanged at %d directives since %s\n" % (total, when))

    # An unmeasured comparison is not zero clusters.
    count = lambda n, what: ("%d %s" % (n, what)) if directives else ("%s unmeasured" % what.split("(")[0].rstrip())
    p("\nlayer-check: %d directive(s), %d layer(s) measured, %s, %s"
      % (total, len(measured), count(len(clusters), "duplication cluster(s)"), count(len(candidates), "override candidate(s)")))
    p({"measured": ", auto memory scanned (%d file(s), duplication only)" % mem_files,
       "absent": ", auto memory absent (not zero — no memory directory)",
       "empty": ", auto memory read and held no directives",
       "off": ", auto memory not read: %s" % mem_note,
       "skipped": ", auto memory skipped by --no-memory"}[mem_state])
    p("\n")
    return "".join(out), ""


def _emit(text, stream):
    buf = getattr(stream, "buffer", None)
    if buf is None:
        stream.write(text)
    else:  # write the bytes back as read, so a file that is not UTF-8 cannot crash the report
        stream.flush()
        buf.write(_b(text))
        buf.flush()


def main(argv):
    try:
        out, err = run(argv)
    except Exception as exc:  # noqa: BLE001 — a broken checker must not be able to block a session
        out, err = f"layer-check: {type(exc).__name__}: {exc}; measured nothing.\n", ""
    _emit(out, sys.stdout)
    if err:
        _emit(err, sys.stderr)
    return 0
