import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tenet import bootstrap, ledger, paths, promote, sweep  # noqa: E402
from tests.helpers import VaultCase, note  # noqa: E402

CLI = Path(__file__).resolve().parent.parent / "tenet" / "cli.py"


class Paths(VaultCase):
    def test_precedence(self):
        os.environ.pop("CLAUDE_PLUGIN_OPTION_LEDGER", None)
        os.environ["TENET_LEDGER"] = "/x/env"
        self.assertEqual(paths.ledger(), (Path("/x/env"), "TENET_LEDGER"))
        os.environ["CLAUDE_PLUGIN_OPTION_LEDGER"] = "/x/opt"
        self.assertEqual(paths.ledger(), (Path("/x/opt"), "userConfig"))
        del os.environ["CLAUDE_PLUGIN_OPTION_LEDGER"], os.environ["TENET_LEDGER"]
        os.environ["BRAIN_VAULT"] = "/x/old"  # retired spelling: no longer consulted
        self.assertEqual(paths.ledger()[1], "default")

    def test_missing_configured_path_is_loud_even_when_quiet(self):
        ok, msg = paths.check_ledger(self.tmp / "nope", "TENET_LEDGER", quiet_when_absent=True)
        self.assertFalse(ok)
        self.assertIn("TENET ERROR", msg)

    def test_missing_default_is_quiet_only_when_asked(self):
        self.assertEqual(paths.check_ledger(self.tmp / "nope", "default", True), (False, None))
        self.assertIn("bootstrap", paths.check_ledger(self.tmp / "nope", "default", False)[1])

    def test_case_mismatch(self):
        wrong = self.vault.parent / "LEDGER"
        if wrong.is_dir():  # case-insensitive filesystem: the listing must catch it
            ok, msg = paths.check_ledger(wrong, "TENET_LEDGER")
            self.assertFalse(ok)
            self.assertIn("case", msg)
        self.assertEqual(paths.check_ledger(self.vault, "TENET_LEDGER"), (True, None))


class Ledger(VaultCase):
    def test_frontmatter_scalars_lists_and_quotes(self):
        fm = ledger.frontmatter('type: decision\nrevisit: "ha X"\ncategories:\n  - "[[Methods]]"\n  - "[[Tools]]"\nsupersedes:\n')
        self.assertEqual(fm["revisit"], "ha X")
        self.assertEqual(fm["categories"], ["[[Methods]]", "[[Tools]]"])
        self.assertEqual(fm["supersedes"], "")

    def test_raw_items_keep_quotes(self):
        block = 'categories:\n  - "[[Methods]]"\n  - frontend\nrelated:\n  - "[[x]]"\n'
        self.assertEqual(ledger.raw_items(block, "categories"), ['"[[Methods]]"', "frontend"])

    def test_heading_comes_from_the_vault_template(self):
        self.assertEqual(ledger.section_heading(self.vault), ("Döntés", None))
        (self.vault / "templates" / "Decision Template.md").unlink()
        heading, notice = ledger.section_heading(self.vault)
        self.assertEqual(heading, "Decision")
        self.assertIn("no '## ' heading", notice)

    def test_conventions_are_complete(self):
        conv = ledger.conventions()
        self.assertIn("accepted", conv["statuses"])
        self.assertEqual((conv["cap_decision_words"], conv["cap_note_words"]), (60, 400))


class Promote(VaultCase):
    def test_accepted_moves_and_proposed_stays(self):
        self.write("inbox/2026-09-01-a.md", note(status="accepted"))
        self.write("inbox/2026-09-01-b.md", note(status="proposed"))
        out = promote.run(self.vault)
        self.assertTrue((self.vault / "2026-09-01-a.md").exists())
        self.assertTrue((self.vault / "inbox" / "2026-09-01-b.md").exists())
        self.assertIn("  - 2026-09-01-a.md (accepted)", out)

    def test_hungarian_decision_over_the_cap_fails(self):
        self.write("inbox/long.md", note(status="proposed", decision_words=61))
        self.write("inbox/short.md", note(status="proposed", decision_words=60))
        out = "\n".join(promote.run(self.vault))
        self.assertIn("long.md — ## Döntés: 61 words (max 60)", out)
        self.assertNotIn("short.md", out)

    def test_missing_section_is_reported_not_passed(self):
        self.write("inbox/english.md", note(status="proposed", heading="Decision", decision_words=80))
        out = "\n".join(promote.run(self.vault))
        self.assertIn("english.md — no '## Döntés' section", out)

    def test_english_template_checks_english_heading(self):
        (self.vault / "templates" / "Decision Template.md").write_text("## Decision\n")
        self.write("inbox/en.md", note(status="proposed", heading="Decision", decision_words=61))
        self.assertIn("en.md — ## Decision: 61 words (max 60)", "\n".join(promote.run(self.vault)))

    def test_invalid_status_placeholder_and_collision(self):
        self.write("inbox/bad.md", note(status="done"))
        self.write("inbox/ph.md", note(status="proposed").replace("2026-09-01", "{{date:YYYY-MM-DD}}"))
        self.write("dup.md", note())
        self.write("inbox/dup.md", note())
        out = "\n".join(promote.run(self.vault))
        self.assertIn("bad.md — status: done", out)
        self.assertIn("ph.md — {{date:YYYY-MM-DD}} left literal", out)
        self.assertIn("dup.md — a note of that name already exists", out)
        self.assertTrue((self.vault / "inbox" / "bad.md").exists())

    def test_unquoted_category_is_flagged_but_templates_are_not(self):
        self.write("2026-09-01-x.md", note(categories=("frontend",)))
        self.write("templates/Gotcha Template.md", note(categories=('""',)))
        out = "\n".join(promote.run(self.vault))
        self.assertIn("2026-09-01-x.md — frontend (not a quoted wikilink)", out)
        self.assertNotIn("Gotcha Template", out)

    def test_silent_when_clean_and_nags_when_maintenance_is_stale(self):
        digest = self.vault / "_meta" / "maintenance-2026-01-01.md"
        os.utime(digest, (time.time(), time.time()))
        self.assertEqual(promote.run(self.vault), [])
        os.utime(digest, (time.time() - 8 * 86400,) * 2)
        self.assertIn("Maintenance is due (last run 2026-01-01). Run /tenet:tenet-sweep.", promote.run(self.vault))


class Bootstrap(VaultCase):
    def test_refuses_existing_notes_and_obsidian(self):
        self.assertIn("markdown", bootstrap.refusal(self.vault))
        target = self.tmp / "obs"
        (target / ".obsidian").mkdir(parents=True)
        self.assertIn("Obsidian", bootstrap.refusal(target))
        self.assertEqual(bootstrap.run(target)[0], 1)

    def test_creates_a_ledger(self):
        target = self.tmp / "new"
        code, _ = bootstrap.run(target)
        self.assertEqual(code, 0)
        self.assertTrue((target / "inbox" / ".gitkeep").exists())
        self.assertTrue((target / "templates" / "Decision Template.md").exists())
        self.assertFalse((target / ".obsidian").exists())


class Sweep(VaultCase):
    def test_memory_off_is_not_a_clean_record(self):
        os.environ["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
        self.write("2026-09-01-u.md", note(decision_words=70))
        out = "\n".join(sweep.render(self.vault))
        self.assertIn("auto memory is off", out)
        self.assertIn("2026-09-01-u.md: ## Döntés: 70 words (max 60)", out)

    def test_nested_feedback_type_is_found(self):
        cfg = self.tmp / "cfg"
        mem = cfg / "projects" / "-repo" / "memory"
        mem.mkdir(parents=True)
        (mem / "f.md").write_text("---\nname: f\ndescription: say it once\nmetadata:\n  type: feedback\n---\nbody\n")
        os.environ["CLAUDE_CONFIG_DIR"] = str(cfg)
        os.environ.pop("CLAUDE_CODE_DISABLE_AUTO_MEMORY", None)
        out = "\n".join(sweep.render(self.vault))
        self.assertIn("1 feedback note(s)", out)
        self.assertIn("say it once", out)


class Cli(VaultCase):
    def run_cli(self, *args, **env):
        full = {k: v for k, v in os.environ.items() if k not in ("TENET_LEDGER", "CLAUDE_PLUGIN_OPTION_LEDGER")}
        full.update(env)
        return subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True, env=full, cwd=self.tmp)

    def test_hook_is_silent_without_a_default_ledger(self):
        r = self.run_cli("hook", "session-start", HOME=str(self.tmp / "home"))
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_hook_is_loud_about_a_configured_missing_ledger(self):
        r = self.run_cli("hook", "session-start", TENET_LEDGER=str(self.tmp / "gone"))
        self.assertEqual(r.returncode, 0)
        self.assertIn("TENET ERROR", r.stdout)

    def test_hook_reports_a_broken_inbox(self):
        (self.vault / "inbox").rmdir()
        (self.vault / "inbox").write_text("not a directory")
        r = self.run_cli("hook", "session-start", TENET_LEDGER=str(self.vault))
        self.assertEqual(r.returncode, 0)
        self.assertIn("inbox/ missing", r.stdout)

    def test_session_start_hook_covers_clear(self):
        # /clear empties the context, so the brief has to come back with it.
        hooks = json.loads((paths.PLUGIN_ROOT / "hooks" / "hooks.json").read_text())["hooks"]["SessionStart"]
        self.assertIn("clear", "|".join(h["matcher"] for h in hooks).split("|"))

    def test_compact_lists_without_promoting(self):
        self.write("inbox/a.md", note(status="accepted"))
        self.write("2026-09-01-u.md", note())
        r = self.run_cli("hook", "session-start", "--compact", TENET_LEDGER=str(self.vault))
        self.assertIn("LEDGER:", r.stdout)
        self.assertTrue((self.vault / "inbox" / "a.md").exists())


class ReviewFindings(VaultCase):
    """Regressions found by the port review, each with the input that broke it."""

    def test_directory_and_dangling_link_named_md_are_skipped(self):
        self.write("inbox/a.md", note(status="accepted"))
        (self.vault / "inbox" / "folder.md").mkdir()
        os.symlink(self.tmp / "missing", self.vault / "inbox" / ".#draft.md")
        out = promote.run(self.vault)
        self.assertIn("  - a.md (accepted)", out)
        self.assertFalse(any("folder.md" in l or ".#draft" in l for l in out))

    def test_hidden_drafts_are_neither_promoted_nor_reported(self):
        self.write("inbox/.hidden.md", note(status="accepted"))
        self.write("inbox/._x.md", "\x00binary")
        self.assertEqual(promote.run(self.vault), [])
        self.assertTrue((self.vault / "inbox" / ".hidden.md").exists())

    def test_non_utf8_template_does_not_crash(self):
        (self.vault / "templates" / "Decision Template.md").write_bytes(b"## D\xf6nt\xe9s\n")
        promote.run(self.vault)

    def test_column_zero_list_items_are_read(self):
        fm = ledger.frontmatter('categories:\n- "[[Methods]]"\n- módszerek\n')
        self.assertEqual(fm["categories"], ["[[Methods]]", "módszerek"])
        self.write("2026-09-01-c.md", note(categories=()).replace("categories:", 'categories:\n- módszerek'))
        self.assertIn("2026-09-01-c.md — módszerek (not a quoted", "\n".join(promote.run(self.vault)))

    def test_repeated_key_keeps_the_first_value(self):
        self.assertEqual(ledger.frontmatter("status: accepted\nstatus: proposed\n")["status"], "accepted")

    def test_a_crashing_step_does_not_hide_the_other(self):
        import contextlib, io
        from tenet import cli
        self.write("2026-09-01-u.md", note())
        os.environ["TENET_LEDGER"] = str(self.vault)
        original, buf = promote.run, io.StringIO()
        promote.run = lambda vault: 1 / 0
        try:
            with contextlib.redirect_stdout(buf):
                self.assertEqual(cli.session_start(compact=False), 0)
        finally:
            promote.run = original
        self.assertIn("TENET ERROR: promote failed: ZeroDivisionError", buf.getvalue())
        self.assertIn("LEDGER:", buf.getvalue())

if __name__ == "__main__":
    unittest.main()
