import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tenet.audit import surface  # noqa: E402


class SurfaceCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = self.tmp / "cfg"
        self.cfg.mkdir()
        (self.tmp / "home").mkdir()
        self._env = dict(os.environ)
        os.environ["CLAUDE_CONFIG_DIR"] = str(self.cfg)
        os.environ["HOME"] = str(self.tmp / "home")

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)
        shutil.rmtree(self.tmp)

    def put(self, rel, data):
        path = self.cfg / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data if isinstance(data, str) else json.dumps(data))
        return path

    def baseline(self, **surfaces):
        self.put("surface-baseline.json", {"recorded": "2026-09-01", "surfaces": surfaces})

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = surface.main(list(args))
        self.assertEqual(code, 0)
        return out.getvalue(), err.getvalue()


class Compare(SurfaceCase):
    def test_unparseable_settings_is_unread_not_zero(self):
        self.put("settings.json", "{oops")
        self.put("plugins/installed_plugins.json", {"plugins": {}})
        self.baseline(permissions_allow={"count": 3}, enabled_plugin_skills={"count": 5})
        out, _ = self.run_main()
        self.assertIn("  unread      permissions_allow       not measured — settings.json does not parse", out)
        self.assertIn("  unread      enabled_plugin_skills   not measured — settings.json does not parse", out)
        self.assertNotIn("shrunk      ", out)
        self.assertIn("0 grown, 0 shrunk, 0 unchanged, 11 unmeasured", out)

    def test_unparseable_installed_plugins_is_unread_not_zero(self):
        self.put("settings.json", {"enabledPlugins": {"p@m": True}})
        self.put("plugins/installed_plugins.json", "{oops")
        out, _ = self.run_main()
        self.assertIn("unread      enabled_plugin_skills   not measured (plugins/installed_plugins.json does not parse)", out)

    def test_missing_settings_names_the_cause(self):
        out, _ = self.run_main()
        self.assertIn("  unread      permissions_deny        not measured — no settings.json", out)
        self.assertIn("— 4 of 11 surfaces counted below", out)
        self.assertIn("audit surface --record >", out)

    def test_absent_key_is_a_real_zero(self):
        self.put("settings.json", {})
        self.baseline(global_hook_entries={"count": 0})
        out, _ = self.run_main()
        self.assertIn("  unchanged   global_hook_entries     0 (key absent from settings.json)", out)

    def test_growth_names_the_items_on_both_sides(self):
        self.put("settings.json", {"permissions": {"allow": ["a", "b", "c"], "deny": ["x"]}})
        self.baseline(permissions_allow={"count": 2, "keys": ["a", "gone"]}, permissions_deny={"count": 3})
        out, _ = self.run_main()
        self.assertIn("  grown       permissions_allow       2 -> 3 (+1)", out)
        self.assertIn("               added:   b\n               added:   c\n               removed: gone", out)
        self.assertIn("  shrunk      permissions_deny        3 -> 1 (-2)\n               (the baseline recorded a count", out)

    def test_hook_entries_count_commands_not_events(self):
        block = {"matcher": "", "hooks": [{"type": "command"}, {"type": "command"}]}
        self.put("settings.json", {"hooks": {"Stop": [block, block], "SessionStart": [{"matcher": "x"}]}})
        self.baseline(global_hook_entries={"count": 4})
        out, _ = self.run_main()
        self.assertIn("  unchanged   global_hook_entries     4\n", out)

    def test_untracked_and_unusable_baseline_entries_are_unmeasured(self):
        self.put("settings.json", {"permissions": {"deny": []}})
        self.baseline(retired_surface={"count": 1}, permissions_deny={"count": "many"})
        out, _ = self.run_main()
        self.assertIn("  untracked   retired_surface         in the baseline, never measured here", out)
        self.assertIn("  unusable    permissions_deny        baseline holds many, which is not a count", out)

    def test_unreadable_baseline_is_not_a_baseline(self):
        self.put("surface-baseline.json", "{")
        out, _ = self.run_main()
        self.assertIn("exists but is not a surface baseline this can read", out)
        self.assertNotIn("grown,", out)

    def test_plugin_skills_count_the_live_install_only(self):
        live = self.tmp / "cache" / "p" / "2.0.0"
        for skill in ("a", "b"):
            (live / "skills" / skill).mkdir(parents=True)
            (live / "skills" / skill / "SKILL.md").write_text("x")
        (self.tmp / "cache" / "p" / "1.0.0" / "skills" / "old").mkdir(parents=True)
        (self.tmp / "cache" / "p" / "1.0.0" / "skills" / "old" / "SKILL.md").write_text("x")
        self.put("settings.json", {"enabledPlugins": {"p@m": True, "q@m": True, "off@m": False}})
        self.put("plugins/installed_plugins.json", {"plugins": {"p@m": [{"installPath": str(live)}]}})
        self.baseline(enabled_plugin_skills={"count": 2})
        out, _ = self.run_main()
        self.assertIn("  unchanged   enabled_plugin_skills   2 (q@m enabled, nothing installed)", out)


class Record(SurfaceCase):
    def test_keeps_keys_and_carries_hand_notes_forward(self):
        self.put("settings.json", {"permissions": {"allow": ["Bash(ls *)", 'say "hi"']}})
        self.put("agents/reviewer.md", "x")
        self.baseline(permissions_allow={"count": 1, "note": "Accepted: read-only."},
                      global_agents={"count": 0, "note": "no agents/ directory"},
                      global_skills={"count": 0, "note": "Kept empty on purpose."})
        out, err = self.run_main("--record")
        got = json.loads(out)["surfaces"]
        self.assertEqual(got["permissions_allow"], {"count": 2, "keys": ["Bash(ls *)", 'say "hi"'],
                                                    "note": "Accepted: read-only."})
        # A machine remark from an earlier record describes a state that has since changed.
        self.assertEqual(got["global_agents"], {"count": 1, "keys": ["reviewer"]})
        self.assertEqual(got["global_skills"]["note"], "Kept empty on purpose.")
        self.assertEqual(got["global_hook_entries"], {"count": 0, "note": "key absent from settings.json"})

    def test_every_hand_written_field_survives_a_record(self):
        self.put("settings.json", {"permissions": {"allow": ["Bash(ls *)"]}})
        self.put("surface-baseline.json", {"recorded": "2026-09-01", "_comment": "why this baseline",
                                           "project_scope": {"note": "not diffed"},
                                           "surfaces": {"permissions_allow": {"count": 1, "source": "settings.json",
                                                                              "own": ["Bash(ls *)"]}}})
        out, _ = self.run_main("--record")
        got = json.loads(out)
        self.assertEqual((got["_comment"], got["project_scope"]), ("why this baseline", {"note": "not diffed"}))
        self.assertEqual(got["surfaces"]["permissions_allow"]["source"], "settings.json")
        self.assertEqual(got["surfaces"]["permissions_allow"]["own"], ["Bash(ls *)"])

    def test_unreadable_surface_is_null_and_says_so(self):
        out, err = self.run_main("--record")
        self.assertIsNone(json.loads(out)["surfaces"]["permissions_allow"]["count"])
        self.assertIn("permissions_allow could not be read; recording null", err)
        self.assertIn("no baseline at", err)

    def test_says_when_notes_cannot_be_carried(self):
        self.put("settings.json", {})
        self.put("surface-baseline.json", "{")
        out, err = self.run_main("--record")
        json.loads(out)
        self.assertIn("no note was carried forward", err)

    def test_generated_notes_are_told_apart_from_hand_written_ones(self):
        for note in ("no skills/ directory", "no plugins/data directory", "key absent from ~/.claude.json",
                     "a@b enabled, nothing installed; c@d enabled, nothing installed",
                     "plugins/installed_plugins.json does not parse", surface.NEEDS):
            self.assertTrue(surface.GENERATED.fullmatch(note), note)
        for note in ("Unchanged since 2026-07-27.", "key absent from settings.json, and that is deliberate"):
            self.assertFalse(surface.GENERATED.fullmatch(note), note)


if __name__ == "__main__":
    unittest.main()
