"""The mechanism behind "every .md carries title/type/status/updated".

Exemptions are declared per repo in <repo>/.claude/frontmatter-exempt: one shell glob per line,
'#' comments allowed, paths relative to the repo root, and a '*' crosses directory separators.
Declaring one is how a repo says "this genre carries no frontmatter"; an undeclared miss is a defect.

Usage: frontmatter [repo ...] (none = the current directory).
Exit: 0 = clean, 1 = undeclared violations, or a path that could not be examined.
"""
import os
import re
import stat
import subprocess
import sys

REQUIRED = ("title", "type", "status", "updated")
# Vendored, generated and tool-owned trees, matched only inside the repo: a repo that itself
# sits under a directory named build/ or vendor/ is still examined.
EXCLUDED = re.compile(r"/(\.git|node_modules|\.next|dist|build|vendor|\.claude/skills)/")
SPACE = " \t\n\r\f\v"


def glob(pattern):
    """A bash `case` pattern as a regex: * and ? cross '/', [...] negates with ! or ^, \\ escapes."""
    out, i = [], 0
    while i < len(pattern):
        c, i = pattern[i], i + 1
        if c == "*":
            out.append(".*")
        elif c == "?":
            out.append(".")
        elif c == "\\" and i < len(pattern):
            out.append(re.escape(pattern[i]))
            i += 1
        elif c == "[":
            j = i + (pattern[i:i + 1] in ("!", "^"))
            j += pattern[j:j + 1] == "]"  # a leading ] is a member, not the end
            while j < len(pattern) and pattern[j] != "]":
                j += 2 if pattern[j] == "\\" else 1
            if j >= len(pattern):  # unterminated: a literal [
                out.append(r"\[")
                continue
            body, i = pattern[i:j], j + 1
            neg = body[:1] in ("!", "^")
            body = body[neg:]
            members, k = [], 0
            while k < len(body):
                if body[k] == "\\" and k + 1 < len(body):
                    members.append(re.escape(body[k + 1]))
                    k += 2
                    continue
                # a dash between two members is a range; first or last, it is a dash
                members.append("-" if body[k] == "-" and members and k + 1 < len(body) else re.escape(body[k]))
                k += 1
            out.append("[" + ("^" if neg else "") + "".join(members) + "]")
        else:
            out.append(re.escape(c))
    return re.compile("".join(out), re.S)


def _patterns(repo):
    try:
        with open(os.path.join(repo, ".claude", "frontmatter-exempt"), encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
    except OSError:
        return []
    return [glob(p) for p in (line.split("#", 1)[0].strip(SPACE) for line in lines) if p]


def _regular(path):
    try:
        return stat.S_ISREG(os.lstat(path).st_mode)
    except OSError:
        return False


def files(repo):
    """Relative .md paths. Inside a git work tree, git's view (tracked plus untracked-not-ignored)
    so a gitignored file is not scored; otherwise every regular file, as find would list them."""
    try:
        run = subprocess.run(["git", "-C", repo, "ls-files", "-z", "-co", "--exclude-standard", "--", "*.md"],
                             capture_output=True)
    except OSError:
        run = None
    if run is not None and run.returncode == 0:
        found = [os.fsdecode(p) for p in run.stdout.split(b"\0") if p]
    else:
        found = []
        for root, dirs, names in os.walk(repo, onerror=lambda e: print(f"frontmatter: {e}", file=sys.stderr)):
            prefix = os.path.relpath(root, repo)
            prefix = "" if prefix == "." else prefix + "/"
            dirs[:] = [d for d in dirs if not EXCLUDED.search(f"/{prefix}{d}/")]
            found += [prefix + n for n in names]
    return sorted({f for f in found if f.endswith(".md") and not EXCLUDED.search("/" + f)
                   and _regular(os.path.join(repo, f))})


def problem(path):
    """None when the frontmatter is complete, else (label, detail) for the report line."""
    try:
        with open(path, "rb") as fh:
            lines = fh.read().decode("utf-8", "replace").split("\n")
    except OSError:
        lines = [""]
    if lines[0] != "---":
        return "NO FRONTMATTER", ""
    block = []
    for line in lines[1:]:
        if line == "---":
            break
        block.append(line)
    missing = [k for k in REQUIRED if not any(re.match(f"{k}:[{SPACE}]*[^{SPACE}]", line) for line in block)]
    return ("INCOMPLETE", " → " + " ".join(missing)) if missing else None


def check(repo):
    """Print one repo's report; return its violation count, or None when it could not be examined."""
    if not os.path.isdir(repo):
        print(f"{repo} — no such directory, not examined")
        return None
    patterns = _patterns(repo)
    print(f"\n== {repo.rstrip('/').rsplit('/', 1)[-1] or repo} ==")
    bad = checked = exempted = 0
    for rel in files(repo):
        if any(p.fullmatch(rel) for p in patterns):
            exempted += 1
            continue
        checked += 1
        found = problem(os.path.join(repo, rel))
        if found:
            bad += 1
            print(f"  {found[0]:<16}{rel}{found[1]}")
    print(f"  {checked} checked, {exempted} exempted, {bad} bad")
    if not patterns:
        print("  (no .claude/frontmatter-exempt — every .md is required to carry it)")
    return bad


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    results = [check(repo) for repo in (argv or [os.getcwd()])]
    bad, unexamined = sum(r for r in results if r), results.count(None)
    tail = f"; {unexamined} path(s) not examined" if unexamined else ""
    print(f"\nfrontmatter: {bad} undeclared violation(s){tail}")
    return 1 if bad or unexamined else 0
