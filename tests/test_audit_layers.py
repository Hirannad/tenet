import contextlib
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tenet.audit import layers  # noqa: E402

RULE = "- Always run the unit tests before committing anything\n"


class LayerCheck(unittest.TestCase):
    """A throwaway config dir and repo; the machine's managed policy is pointed at nothing."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.cfg = self.root / "cfg"
        self.repo = self.root / "repo"
        self.cfg.mkdir()
        self.repo.mkdir()
        for patch in (mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.cfg)}),
                      mock.patch.object(layers, "MANAGED", (str(self.root / "managed"),))):
            patch.start()
            self.addCleanup(patch.stop)

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def check(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(layers.main([*args, str(self.repo)]), 0)
        self.stderr = err.getvalue()
        return out.getvalue()

    def snapshot(self):
        return {p: (p.stat().st_size, p.stat().st_mtime_ns) for p in self.root.rglob("*")}

    def test_absent_user_layer_is_absent_not_zero(self):
        self.write(self.repo / "CLAUDE.md", RULE)
        out = self.check()
        self.assertRegex(out, re.compile(r"^  absent +user CLAUDE\.md +- +- +-\n +no such layer on this machine — not a zero", re.M))
        self.assertRegex(out, re.compile(r"^  measured +project repo/CLAUDE\.md +1 +1 +1$", re.M))
        self.assertNotRegex(out, re.compile(r"^  measured +user CLAUDE\.md", re.M))

    def test_agents_md_is_the_project_layer_only_without_claude_md(self):
        self.write(self.repo / "AGENTS.md", RULE)
        self.assertRegex(self.check("--no-memory"), re.compile(r"^  measured +project repo/AGENTS\.md +1 +1 +1$", re.M))
        self.write(self.repo / ".claude" / "CLAUDE.md", RULE)
        out = self.check("--no-memory")
        self.assertRegex(out, re.compile(r"^  measured +project repo/CLAUDE\.md +1 +1 +1$", re.M))
        self.assertNotIn("AGENTS.md", out)

    def test_memory_follows_the_settings_that_move_or_disable_it(self):
        mem = self.write(self.root / "elsewhere" / "MEMORY.md", RULE)
        self.write(self.cfg / "CLAUDE.md", RULE)
        self.write(self.cfg / "settings.json", '{"autoMemoryDirectory": "%s"}' % mem.parent)
        self.assertIn("  2 layers: auto memory, user CLAUDE.md\n", self.check())
        self.write(self.cfg / "settings.json", '{"autoMemoryEnabled": false}')
        out = self.check()
        self.assertIn("auto memory not read: auto memory is off (autoMemoryEnabled false", out)
        self.assertNotIn("auto memory,", out)

    def test_symlinked_rule_files_and_directories_are_followed(self):
        shared = self.write(self.root / "shared" / "style.md", RULE)
        self.write(self.root / "shared" / "sub" / "api.md", "- Never call the API without a timeout set\n")
        rules = self.repo / ".claude" / "rules"
        rules.mkdir(parents=True)
        os.symlink(shared, rules / "style.md")
        os.symlink(shared.parent / "sub", rules / "sub")
        out = self.check("--no-memory")
        self.assertRegex(out, re.compile(r"^  measured +project .*rules +2 +2", re.M))

    def test_summary_does_not_count_what_it_did_not_compare(self):
        out = self.check("--no-memory")
        self.assertIn("duplication cluster unmeasured", out)
        self.assertNotIn("0 duplication cluster(s)", out)

    def test_empty_stack_prints_no_budget_number(self):
        out = self.check("--no-memory")
        self.assertIn("  unmeasured — no layer was opened. This is not a budget of zero.\n", out)
        self.assertNotIn("directive(s) across", out)
        self.assertNotIn("% of the", out)
        self.assertIn("  unmeasured — no directive reached the comparison", out)
        self.assertIn("  unmeasured — nothing reached the comparison", out)
        self.assertIn("claudeMdExcludes could not be consulted", out)

    def test_record_writes_nothing_and_prints_a_baseline(self):
        self.write(self.cfg / "CLAUDE.md", RULE)
        self.write(self.cfg / "projects" / "p" / "memory" / "MEMORY.md", RULE)
        before = self.snapshot()
        baseline = json.loads(self.check("--record"))
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(baseline["total_directives"], 1)
        self.assertEqual(baseline["layers"], {"user CLAUDE.md": {"files": 1, "lines": 1, "directives": 1}})
        self.assertEqual(self.stderr, "")

    def test_record_of_nothing_warns_and_writes_nothing(self):
        before = self.snapshot()
        self.assertEqual(json.loads(self.check("--record", "--no-memory"))["layers"], {})
        self.assertEqual(self.snapshot(), before)
        self.assertIn("no layer could be measured", self.stderr)

    def test_rule_in_two_layers_is_a_cluster(self):
        self.write(self.cfg / "CLAUDE.md", RULE)
        self.write(self.repo / "CLAUDE.md", "* always run the **unit tests** before committing anything\n")
        out = self.check("--no-memory")
        self.assertIn("  2 layers: project repo/CLAUDE.md, user CLAUDE.md\n", out)
        self.assertIn("1 duplication cluster(s)", out)

    def test_rule_twice_in_one_layer_is_not_a_cluster(self):
        self.write(self.cfg / "CLAUDE.md", RULE + RULE)
        out = self.check("--no-memory")
        self.assertIn("  none — 1 comparable directive(s) checked across the layers above\n", out)
        self.assertIn("0 duplication cluster(s)", out)

    def test_negation_pair_across_layers_is_a_candidate(self):
        self.write(self.cfg / "CLAUDE.md", "- Never commit directly to the main branch of this repository\n")
        self.write(self.repo / "CLAUDE.md", "- Commit directly to the main branch of this repository\n")
        out = self.check("--no-memory")
        self.assertIn("  2 line(s) form a negation pair across layers. Candidates, not verdicts:\n"
                      "    [project repo/CLAUDE.md] - Commit directly to the main branch of this repository\n"
                      "    [user CLAUDE.md] - Never commit directly to the main branch of this repository\n", out)

    def test_negation_pair_inside_one_layer_is_not_a_candidate(self):
        self.write(self.cfg / "CLAUDE.md", "- Never commit directly to the main branch of this repository\n"
                                           "- Commit directly to the main branch of this repository\n")
        out = self.check("--no-memory")
        self.assertIn("  none — no directive pair across layers differed only by a negation\n", out)

    def test_no_memory_skips_the_memory_tree(self):
        self.write(self.cfg / "CLAUDE.md", RULE)
        self.write(self.cfg / "projects" / "p" / "memory" / "MEMORY.md", RULE)
        scanned = self.check()
        self.assertIn("  2 layers: auto memory, user CLAUDE.md\n", scanned)
        self.assertIn("auto memory scanned (1 file(s), duplication only)", scanned)
        self.assertIn("  1 directive(s) across 1 measured layer(s)", scanned)  # memory stays out of the budget
        skipped = self.check("--no-memory")
        self.assertNotIn("auto memory,", skipped)
        self.assertIn("auto memory skipped by --no-memory", skipped)

    def test_missing_projects_dir_is_absent_not_empty(self):
        self.assertIn("auto memory absent (not zero — no memory directory)", self.check())

    def test_unopenable_file_is_unreadable_not_a_zero(self):
        (self.repo / "CLAUDE.md").mkdir()
        out = self.check("--no-memory")
        self.assertRegex(out, re.compile(r"^  unreadable +project repo/CLAUDE\.md +1 +- +-\n +present but could not be read", re.M))
        self.assertIn("This is not a budget of zero", out)

    def test_claude_md_excludes_is_honoured(self):
        self.write(self.cfg / "settings.json", '{"claudeMdExcludes": [\n  "*/repo/CLAUDE.md"\n]}')
        self.write(self.repo / "CLAUDE.md", RULE)
        out = self.check("--no-memory")
        self.assertRegex(out, re.compile(r"^  excluded +project repo/CLAUDE\.md +1", re.M))
        self.assertNotIn("could not be consulted", out)

    def test_scan_counts_content_and_directives_only(self):
        text = ("---\ntitle: x\n- not a rule\n---\n# Heading must go\n- a list item\nplain prose\n"
                "you should do this\n```\n- fenced\n```\n<!--\n- commented\n-->\n\n> - quoted rule\n")
        count, found = layers.scan(text)
        self.assertEqual(count, 4)
        self.assertEqual([n for n, _ in found], ["a list item", "you should do this"])
        self.assertEqual(layers.normalize("* **Don't** use `rm -rf` [here](x)"), "don t use rm rf herex")

    def test_trend_against_a_baseline(self):
        self.write(self.cfg / "CLAUDE.md", RULE + "- Never push to main without a reviewed pull request\n")
        base = self.write(self.root / "base.json", '{"recorded": "2026-01-01", "total_directives": 1}')
        self.assertIn("  grown    1 → 2 directives (+1) since 2026-01-01\n", self.check("--baseline", str(base)))
        base.write_text('{"recorded": "2026-01-01"}')
        self.assertIn("unusable — " + str(base), self.check("--baseline", str(base)))
        self.assertIn("  unbaselined — no baseline at " + str(self.cfg / "instruction-baseline.json"), self.check())

    def test_a_crash_still_exits_zero_and_says_so(self):
        with mock.patch.object(layers, "run", side_effect=RuntimeError("boom")):
            out = self.check()
        self.assertIn("audit layers: RuntimeError: boom; measured nothing.", out)


if __name__ == "__main__":
    unittest.main()
