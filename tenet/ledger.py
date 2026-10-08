"""Reading notes: frontmatter, sections, and the conventions the machinery enforces."""
import re
from pathlib import Path

from tenet import paths

CONVENTIONS = paths.PLUGIN_ROOT / "skills" / "tenet-capture" / "references" / "conventions.md"
_KEY = re.compile(r"^([A-Za-z_][\w-]*):[ \t]*(.*)$")
_ITEM = re.compile(r"^\s*-[ \t]*(.*)$")


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def split(text):
    """Return (frontmatter block, body). No leading --- fence means no frontmatter."""
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---", 3)
    if end < 0:
        return "", text
    rest = text[end + 4:]
    return text[4:end + 1], rest.split("\n", 1)[1] if "\n" in rest else ""


def frontmatter(block):
    """Scalars and block lists: the YAML subset notes use."""
    data, key = {}, None
    for line in block.splitlines():
        m = _KEY.match(line)
        if m:
            # A repeated key keeps its first value, as the bash tools did.
            key = None if m.group(1) in data else m.group(1)
            if key:
                data[key] = unquote(m.group(2))
            continue
        m = _ITEM.match(line)
        if m and key:
            if not isinstance(data[key], list):
                data[key] = []
            data[key].append(unquote(m.group(1)))
    return data


def raw_items(block, key):
    """The list items under `key`, exactly as written (quotes matter to YAML)."""
    items, inside = [], False
    for line in block.splitlines():
        if _KEY.match(line):
            inside = line.startswith(key + ":")
            continue
        m = _ITEM.match(line)
        if inside and m:
            items.append(m.group(1).strip())
    return items


def read(path):
    """Return (frontmatter dict, raw block, body) for a note."""
    block, body = split(Path(path).read_text(encoding="utf-8", errors="replace"))
    return frontmatter(block), block, body


def sections(body):
    """Map each `## ` heading to the text under it."""
    out, current = {}, None
    for line in body.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def words(text):
    return len(text.split())


def section_heading(vault):
    """The Decision heading in the vault's own language: the first `##` of its Decision
    template. Returns (heading, notice); the notice is set when it fell back to English."""
    template = Path(vault) / "templates" / "Decision Template.md"
    try:
        for line in template.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("## "):
                return line[3:].strip(), None
    except OSError:
        pass
    return "Decision", (
        f"tenet: no '## ' heading found in {template}; checking decisions against '## Decision'. "
        "A vault in another language will report every decision as missing that section."
    )


def template_headings(vault, kind):
    """The `## ` headings of the vault's own template for a note type, in order. Empty when the
    template is missing or has none."""
    template = Path(vault) / "templates" / f"{kind} Template.md"
    try:
        lines = template.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return [line[3:].strip() for line in lines if line.startswith("## ")]


def conventions():
    """The machine-read values of the note model, from the one file that states them."""
    data = frontmatter(split(CONVENTIONS.read_text(encoding="utf-8"))[0])
    missing = [k for k in ("statuses", "keep_in_inbox", "cap_decision_words", "cap_note_words") if not data.get(k)]
    if missing:
        raise ValueError(f"{CONVENTIONS} lacks {', '.join(missing)} in its frontmatter")
    return {
        "statuses": data["statuses"].split(),
        "keep_in_inbox": data["keep_in_inbox"].split(),
        "cap_decision_words": int(data["cap_decision_words"]),
        "cap_note_words": int(data["cap_note_words"]),
    }


def md_files(directory):
    """Regular, non-hidden *.md files: no directories, dangling links, lock or AppleDouble files."""
    return sorted(p for p in Path(directory).glob("*.md") if p.is_file() and not p.name.startswith("."))


def notes(vault):
    """Knowledge notes in the ledger root, sorted by filename."""
    return md_files(vault)
