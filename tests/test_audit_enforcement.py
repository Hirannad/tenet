import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tenet.audit import enforcement  # noqa: E402

RULES = """# Rules
- Never **commit** secrets or `tokens`
- Keep   *it* short
```
- fenced, not a rule
```
  - nested, not a rule
- Dangling rule nobody covers
"""
TABLE = """Prose above the table.
## The table
| Rule | Mechanism |
|:--|--:|
| never commit secrets or tokens | hook |
| - Keep it short |  |
| A stale row | lint |
| Note row ¶ | |
## Elsewhere
| Not in the table | x |
"""


class EnforcementCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = self.tmp / "cfg"
        self.cfg.mkdir()
        self._env = dict(os.environ)
        for var in ("CLAUDE_MD", "ENFORCEMENT_TABLE"):
            os.environ.pop(var, None)
        os.environ["CLAUDE_CONFIG_DIR"] = str(self.cfg)
        (self.cfg / "CLAUDE.md").write_text(RULES)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)
        shutil.rmtree(self.tmp)

    def run_main(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(enforcement.main(list(args)), 0)
        return out.getvalue()

    def test_unmarked_rule_orphan_row_and_empty_cell_are_counted(self):
        (self.cfg / "enforcement.md").write_text(TABLE)
        self.assertEqual(self.run_main(), "CLAUDE.md enforcement: 1 unmarked rule(s), 1 orphan row(s), 2 empty cell(s)\n"
                                          "  unmarked rule: dangling rule nobody covers\n"
                                          "  orphan row:    a stale row\n")

    def test_fully_covered_is_three_zeroes(self):
        (self.cfg / "enforcement.md").write_text(TABLE.replace("| A stale row | lint |", "| Dangling rule nobody covers | ci |"))
        self.assertIn("0 unmarked rule(s), 0 orphan row(s), 2 empty cell(s)", self.run_main())

    def test_matching_ignores_case_beyond_ascii(self):
        (self.cfg / "CLAUDE.md").write_text("- Árvíztűrő TÜKÖRFÚRÓGÉP szabály\n")
        (self.cfg / "enforcement.md").write_text("## The table\n| árvíztűrő tükörfúrógép szabály | x |\n")
        self.assertIn("0 unmarked rule(s), 0 orphan row(s), 0 empty cell(s)", self.run_main())

    def test_missing_default_table_still_counts_the_rules(self):
        out = self.run_main()
        self.assertTrue(out.startswith(f"CLAUDE.md enforcement: no table yet at {self.cfg}/enforcement.md — 3 rule(s)"), out)

    def test_missing_pointed_at_table_is_an_alarm(self):
        os.environ["ENFORCEMENT_TABLE"] = str(self.tmp / "moved.md")
        self.assertIn("the table was pointed at", self.run_main())
        del os.environ["ENFORCEMENT_TABLE"]
        self.assertIn("the table was pointed at", self.run_main("--table", str(self.tmp / "moved.md")))

    def test_unreadable_rules_say_so(self):
        self.assertEqual(self.run_main("--rules", str(self.tmp / "none.md")),
                         f"enforcement-check: cannot read {self.tmp}/none.md\n")

    def test_table_only_mode_is_gone(self):
        (self.tmp / "t.md").write_text("no table here\n")
        out = self.run_main("--empty-only", "--table", str(self.tmp / "t.md"))
        self.assertNotIn("MISSING", out)
        self.assertTrue(out.startswith("CLAUDE.md enforcement: 3 unmarked rule(s)"), out)


if __name__ == "__main__":
    unittest.main()
