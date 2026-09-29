import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tenet.audit import frontmatter  # noqa: E402

GOOD = "---\ntitle: T\ntype: guide\nstatus: active\nupdated: 2026-09-01\n---\nbody\n"


class FrontmatterCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        self.repo.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, rel, text, root=None):
        path = (root or self.repo) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def run_main(self, *paths):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = frontmatter.main([str(p) for p in paths])
        return code, out.getvalue()

    def test_missing_and_incomplete_are_counted_and_exempted_is_not(self):
        self.write("good.md", GOOD)
        self.write("none.md", "# no frontmatter\n")
        self.write("part.md", "---\ntitle: T\ntype:\n---\nstatus: after the block\n")
        self.write("docs/deep/x.md", "# exempt\n")
        self.write("node_modules/pkg/n.md", "# vendored\n")
        self.write(".claude/skills/s/SKILL.md", "# tool-owned\n")
        self.write(".claude/frontmatter-exempt", "# comment\n  docs/*   # '*' crosses '/'\n")
        code, out = self.run_main(self.repo)
        self.assertEqual(code, 1)
        self.assertIn("\n== repo ==\n  NO FRONTMATTER  none.md\n  INCOMPLETE      part.md → type status updated\n"
                      "  3 checked, 1 exempted, 2 bad\n", out)
        self.assertIn("frontmatter: 2 undeclared violation(s)", out)

    def test_clean_repo_exits_zero_and_names_the_missing_exempt_file(self):
        self.write("good.md", GOOD)
        code, out = self.run_main(self.repo)
        self.assertEqual(code, 0)
        self.assertIn("(no .claude/frontmatter-exempt — every .md is required to carry it)", out)

    @unittest.skipUnless(shutil.which("git"), "git not installed")
    def test_gitignored_file_is_not_scored(self):
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.write(".gitignore", "local.md\n")
        self.write("local.md", "# machine-local, never shipped\n")
        self.write("tracked.md", GOOD)
        self.write("untracked.md", "# new, not yet added\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "tracked.md"], check=True)
        code, out = self.run_main(self.repo)
        self.assertEqual(code, 1)
        self.assertIn("  NO FRONTMATTER  untracked.md\n  2 checked, 0 exempted, 1 bad", out)
        self.assertNotIn("local.md", out)

    def test_missing_directory_is_not_examined_and_fails(self):
        self.write("good.md", GOOD)
        code, out = self.run_main(self.repo, self.tmp / "nope")
        self.assertEqual(code, 1)
        self.assertIn(f"{self.tmp}/nope — no such directory, not examined", out)
        self.assertIn("frontmatter: 0 undeclared violation(s); 1 path(s) not examined", out)

    def test_last_exemption_without_a_newline_applies(self):
        self.write("b.md", "# x\n")
        self.write("docs/a.md", "# x\n")
        self.write(".claude/frontmatter-exempt", "b.md\ndocs/*")
        self.assertEqual(self.run_main(self.repo), (0, "\n== repo ==\n  0 checked, 2 exempted, 0 bad\n\n"
                                                       "frontmatter: 0 undeclared violation(s)\n"))

    def test_repo_inside_a_build_directory_is_still_examined(self):
        repo = self.tmp / "build" / "inner"
        self.write("none.md", "# x\n", root=repo)
        self.write("dist/generated.md", "# x\n", root=repo)
        code, out = self.run_main(repo)
        self.assertIn("  1 checked, 0 exempted, 1 bad", out)

    def test_trailing_slash_keeps_exemptions_relative(self):
        self.write("docs/a.md", "# x\n")
        self.write(".claude/frontmatter-exempt", "docs/*\n")
        code, out = self.run_main(f"{self.repo}/")
        self.assertEqual(code, 0)
        self.assertIn("== repo ==\n  0 checked, 1 exempted, 0 bad", out)

    def test_glob_follows_case_semantics(self):
        g = frontmatter.glob
        self.assertTrue(g("skills/*/SKILL.md").fullmatch("skills/a/b/SKILL.md"))
        self.assertTrue(g("docs/?.md").fullmatch("docs/a.md"))
        self.assertFalse(g("docs/?.md").fullmatch("docs/ab.md"))
        self.assertTrue(g("docs/[!a].md").fullmatch("docs/b.md"))
        self.assertFalse(g("docs/[^a].md").fullmatch("docs/a.md"))
        self.assertTrue(g("docs/[a-c].md").fullmatch("docs/b.md"))
        self.assertTrue(g(r"docs/\*.md").fullmatch("docs/*.md"))
        self.assertFalse(g(r"docs/\*.md").fullmatch("docs/x.md"))
        self.assertTrue(g("docs/[").fullmatch("docs/["))
        self.assertFalse(g("README.md").fullmatch("x/README.md"))


if __name__ == "__main__":
    unittest.main()
