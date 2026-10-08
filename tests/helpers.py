import os
import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path

HU_TEMPLATE = "---\ntype: decision\n---\n\n## Döntés\n\n## Mikor kell újragondolni\n"


def note(kind="decision", status="accepted", decision_words=10, heading="Döntés",
         categories=('"[[Methods]]"',), revisit="ha X", extra=""):
    cats = "".join(f"\n  - {c}" for c in categories)
    body = f"## {heading}\n\n" + " ".join(["szó"] * decision_words) + "\n" if heading else "## Más\n\nszöveg\n"
    return (f"---\ntype: {kind}\ncreated: 2026-09-01\nstatus: {status}\n"
            f"categories:{cats}\nrevisit: {revisit}\n{extra}---\n\n{body}")


class VaultCase(unittest.TestCase):
    """A throwaway ledger with the Hungarian Decision template the live one uses."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.vault = self.tmp / "ledger"
        for sub in ("inbox", "_meta", "templates", "raw"):
            (self.vault / sub).mkdir(parents=True)
        (self.vault / "templates" / "Decision Template.md").write_text(HU_TEMPLATE)
        (self.vault / "_meta" / "maintenance-2026-01-01.md").write_text("---\ntype: meta\n---\n")
        (self.vault / "Methods.md").write_text("# Methods\n")
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)
        shutil.rmtree(self.tmp)

    def write(self, rel, text):
        path = self.vault / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text) if text.startswith("\n") else text)
        return path
