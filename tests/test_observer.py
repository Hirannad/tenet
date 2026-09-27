import contextlib
import io
import json
import os
import sys
import time
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tenet import cli, promote  # noqa: E402
from tenet.observer import brief, run, textindex, transcripts, usage  # noqa: E402
from tests.helpers import VaultCase, note  # noqa: E402


def session(root, prompts=(), assistant=(), asked=(), sid="s1", day=None):
    return {"id": sid, "cwd": root, "root": root, "scheduled": False, "prompts": list(prompts),
            "asked": list(asked), "paths": [], "assistant": list(assistant), "date": day or date.today().isoformat()}


def line(record):
    return json.dumps(record) + "\n"


class TextIndex(unittest.TestCase):
    def test_hungarian_and_english_forms_collapse(self):
        for forms in (["hook", "hookok", "hooknak", "hookot"], ["döntés", "döntések", "döntést"],
                      ["schedule", "scheduled", "scheduling"]):
            self.assertEqual(len({textindex.tokens(w)[0] for w in forms}), 1, forms)

    def test_distinct_words_stay_distinct(self):
        self.assertNotEqual(textindex.tokens("kapu"), textindex.tokens("kapcsolat"))

    def test_cosine_prefers_shared_terms(self):
        v = textindex.vectors({"a": "stop hook fires", "b": "gsap animation canvas", "q": "the stop hook"})
        self.assertGreater(textindex.cosine(v["q"], v["a"]), textindex.cosine(v["q"], v["b"]))


class Transcripts(VaultCase):
    def test_only_human_prompts_count(self):
        f = self.tmp / "s.jsonl"
        f.write_text(
            line({"type": "user", "cwd": "/x", "origin": {"kind": "human"}, "message": {"content": "valódi kérdés"}})
            + line({"type": "user", "origin": {"kind": "human"}, "message": {"content": "<system-reminder>x"}})
            + line({"type": "user", "origin": {"kind": "human"}, "isMeta": True, "message": {"content": "meta"}})
            + line({"type": "user", "message": {"content": [{"type": "tool_result", "content": "tool out"}]}})
            + line({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "see [[2026-01-01-a]]"},
                {"type": "tool_use", "name": "AskUserQuestion", "input": {"questions": [
                    {"question": "Melyik út?", "options": [{"label": "Bal", "description": "rövid"}]}]}},
                {"type": "tool_use", "name": "Edit", "input": {"file_path": "/x/src/a.py"}}]}}))
        s = transcripts.read(f)
        self.assertEqual(s["prompts"], ["valódi kérdés"])
        self.assertIn("Melyik út? Bal rövid", s["asked"])
        self.assertEqual(s["paths"], ["/x/src/a.py"])
        self.assertEqual((s["cwd"], s["scheduled"]), ("/x", False))

    def test_scheduled_session_is_marked(self):
        f = self.tmp / "s.jsonl"
        f.write_text(line({"type": "user", "cwd": "/x", "message": {"content": "<scheduled-task name=x>"}}))
        self.assertTrue(transcripts.read(f)["scheduled"])

    def test_worktree_maps_to_main_repo(self):
        main = self.tmp / "repo"
        (main / ".git" / "worktrees" / "w").mkdir(parents=True)
        wt = self.tmp / "wt"
        wt.mkdir()
        (wt / ".git").write_text(f"gitdir: {main}/.git/worktrees/w\n")
        (wt / "sub").mkdir()
        self.assertEqual(transcripts.root_of(wt / "sub"), str(main))
        self.assertEqual(transcripts.root_of(main), str(main))


class Brief(VaultCase):
    def setUp(self):
        super().setUp()
        old = (date.today() - timedelta(days=40)).isoformat()
        self.write(f"{old}-stop-hook.md", note(decision_words=5).replace("szó szó szó szó szó", "a stop hook minden válasz után kérdez")
                   .replace("2026-09-01", old))
        self.write(f"{old}-gsap-canvas.md", note(decision_words=5).replace("szó szó szó szó szó", "gsap animáció canvas elemen")
                   .replace("2026-09-01", old))
        self.write(f"{old}-rejected.md", note(status="rejected").replace("2026-09-01", old))

    def build(self, sessions):
        notes = brief.corpus(self.vault)
        projs = brief.projects(sessions)
        return notes, projs, brief.score(notes, projs)

    def test_project_ranks_its_own_notes_first(self):
        sessions = [session("/p/hooks", ["a stop hook zajos"]), session("/p/anim", ["gsap canvas animáció"], sid="s2")]
        notes, projs, scores = self.build(sessions)
        top = lambda r: max(scores[r], key=scores[r].get)
        self.assertTrue(top("/p/hooks").endswith("stop-hook"))
        self.assertTrue(top("/p/anim").endswith("gsap-canvas"))
        self.assertFalse(any(k.endswith("rejected") for k in notes))

    def test_fresh_window_is_fourteen_days(self):
        for days in (13, 15):
            d = (date.today() - timedelta(days=days)).isoformat()
            self.write(f"{d}-f{days}.md", note().replace("2026-09-01", d))
        notes, projs, scores = self.build([session("/p/x", ["semmi köze"])])
        text = brief.render(self.vault, "/p/x", notes, projs, scores, [], "today")
        fresh = text.split("## Fresh")[1]
        self.assertIn("f13", fresh)
        self.assertNotIn("f15", fresh)

    def test_zero_matches_is_said_not_left_blank(self):
        notes, projs, scores = self.build([session("/p/x", ["zzzz qqqq"])])
        text = brief.render(self.vault, "/p/x", notes, projs, scores, [], "today")
        self.assertIn("project matches: 0 of 2 notes above threshold (1 session(s) read)", text)

    def test_budget_says_what_it_withheld_and_cap_holds(self):
        old = (date.today() - timedelta(days=40)).isoformat()
        for i in range(40):
            self.write(f"{old}-stop-hook-{i:02}.md", note(decision_words=5).replace(
                "szó szó szó szó szó", "a stop hook minden válasz után kérdez " + "hosszú " * 12).replace("2026-09-01", old))
        notes, projs, scores = self.build([session("/p/hooks", ["a stop hook zajos"])])
        text = brief.render(self.vault, "/p/hooks", notes, projs, scores, [], "today")
        self.assertIn("more withheld", text)
        self.assertLessEqual(len(text.encode()), brief.MAX_BYTES)

    def test_write_and_lookup(self):
        data, repo = self.tmp / "data", os.path.realpath(self.tmp) + "/repo"
        os.makedirs(repo + "/.git")
        brief.write_all(self.vault, data, [session(repo, ["a stop hook"])], "today")
        text, matched = brief.lookup(data, repo + "/src")
        self.assertTrue(matched)
        self.assertIn("TENET BRIEF · " + repo, text)
        text, matched = brief.lookup(data, "/elsewhere")
        self.assertFalse(matched)
        self.assertIn("no project match", text)


class Usage(VaultCase):
    def test_citations_count_but_ledger_sessions_and_hubs_do_not(self):
        self.write("2026-01-01-a.md", note())
        sessions = [session("/work", assistant=["per [[2026-01-01-a]] and Methods"], sid="w"),
                    session(str(self.vault.resolve()), assistant=["2026-01-01-a"], sid="l")]
        self.assertEqual(usage.update(self.vault, sessions, "2026-08-29"), 1)
        events = usage.load(self.vault)
        self.assertEqual([(e["note"], e["source"]) for e in events], [("2026-01-01-a", "w")])
        self.assertEqual(usage.update(self.vault, sessions, "2026-08-29"), 0)  # re-scan adds nothing

    def test_draft_related_link_counts_and_measured_since_is_set_once(self):
        self.write("2026-01-01-a.md", note())
        self.write("inbox/d.md", note(status="proposed", extra='related:\n  - "[[2026-01-01-a]]"\n'))
        usage.update(self.vault, [], "2026-08-29")
        self.assertEqual(usage.load(self.vault)[0]["source"], "d.md")
        usage.update(self.vault, [], "2026-09-10")
        self.assertEqual(usage.measured_since(self.vault), "2026-08-29")


class Runner(VaultCase):
    def test_due_and_banners(self):
        data = self.tmp / "data"
        self.assertEqual(run.due(self.vault, data, True), "no brief computed yet")
        run._write_status(data, last_ok=time.time() - 8 * 86400, last_attempt=time.time() - 25 * 3600)
        self.assertEqual(run.due(self.vault, data, True), "stale")
        self.assertIn("TENET BRIEF STALE", run.banners(data)[0])
        run._write_status(data, last_ok=time.time(), last_attempt=time.time(), error="Boom: x")
        self.assertIsNone(run.due(self.vault, data, True))
        self.assertIn("TENET OBSERVER FAILING: Boom: x", run.banners(data))

    def test_second_scan_yields_to_the_lock(self):
        import fcntl
        data = self.tmp / "data"
        (data / "observer").mkdir(parents=True)
        with open(data / "observer" / "lock", "w") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            self.assertIsNone(run.scan(self.vault, data))

    def test_hook_prints_brief_and_live_inbox_count(self):
        data = self.tmp / "data"
        cwd = os.path.realpath(self.tmp)
        brief.write_all(self.vault, data, [session(cwd, ["stop hook"])], "today")
        run._write_status(data, last_ok=time.time(), last_attempt=time.time())
        self.write("inbox/d.md", note(status="proposed"))
        os.environ.update(TENET_LEDGER=str(self.vault), TENET_DATA=str(data))
        buf, here = io.StringIO(), os.getcwd()
        os.chdir(self.tmp)
        try:
            with contextlib.redirect_stdout(buf):
                cli.session_start(compact=True)
        finally:
            os.chdir(here)
        out = buf.getvalue()
        self.assertIn("TENET BRIEF · " + cwd, out)
        self.assertIn("1 draft(s) awaiting review", out)

    def test_hook_without_brief_says_so_and_launches_a_scan(self):
        data = self.tmp / "data"
        os.environ.update(TENET_LEDGER=str(self.vault), TENET_DATA=str(data))
        launched, original = [], run.spawn
        run.spawn = lambda data: launched.append(1)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                cli.session_start(compact=False)
        finally:
            run.spawn = original
        self.assertIn("TENET BRIEF: none computed yet — a first scan was launched", buf.getvalue())
        self.assertEqual(launched, [1])

    def test_category_without_a_hub_is_reported(self):
        self.write("2026-09-01-x.md", note(categories=('"[[Nincs Ilyen]]"',)))
        self.assertIn('"[[Nincs Ilyen]]" (no hub note of that name', "\n".join(promote.run(self.vault)))


class ObserverReviewFindings(VaultCase):
    """Regressions from the observer review, each with the input that broke it."""

    def test_a_damaged_usage_line_loses_nothing(self):
        self.write("2026-01-01-a.md", note())
        usage.update(self.vault, [session("/w", assistant=["2026-01-01-a"], sid="w1")], "2026-08-29")
        log = self.vault / "_meta" / "observer" / "usage.jsonl"
        log.write_text(log.read_text() + '{"date": "2026-09-27", "note": "trunc\n')
        usage.update(self.vault, [session("/w", assistant=["2026-01-01-a"], sid="w2")], "2026-08-29")
        text = log.read_text()
        self.assertIn('"source": "w1"', text)
        self.assertIn('"source": "w2"', text)
        self.assertIn('"note": "trunc', text)

    def test_a_note_renamed_into_the_root_makes_the_brief_due(self):
        data = self.tmp / "data"
        brief.write_all(self.vault, data, [session("/w")], "today")
        run._write_status(data, last_ok=time.time(), last_attempt=time.time() - 3600)
        past = time.time() - 7200
        os.utime(data / "briefs" / "index.tsv", (past, past))
        draft = self.write("inbox/new.md", note())
        os.utime(draft, (past - 60, past - 60))
        os.rename(draft, self.vault / "new.md")  # keeps the file's old mtime
        self.assertEqual(run.due(self.vault, data, True), "notes changed")

    def test_withheld_counts_every_eligible_note(self):
        items = [f"- [[n{i}]] · d · x" for i in range(30)]
        section = brief._section("T", items, 10000, 20)
        self.assertIn("(+10 more withheld; ask by name)", section)

    def test_worktree_outside_the_repo_gets_the_repo_brief(self):
        data, repo, wt = self.tmp / "data", os.path.realpath(self.tmp) + "/repo", os.path.realpath(self.tmp) + "/repo-wt"
        os.makedirs(repo + "/.git/worktrees/w")
        os.makedirs(wt)
        Path(wt + "/.git").write_text(f"gitdir: {repo}/.git/worktrees/w\n")
        brief.write_all(self.vault, data, [session(repo, ["x"])], "today")
        self.assertTrue(brief.lookup(data, wt)[1])

    def test_a_plain_parent_does_not_capture_its_subprojects(self):
        data, parent = self.tmp / "data", os.path.realpath(self.tmp) + "/container"
        os.makedirs(parent + "/newproj")
        brief.write_all(self.vault, data, [session(parent, ["x"])], "today")
        self.assertTrue(brief.lookup(data, parent)[1])
        self.assertFalse(brief.lookup(data, parent + "/newproj")[1])

    def test_core_leaves_out_notes_relevant_nowhere(self):
        for name in ("a", "b"):
            self.write(f"2026-01-01-{name}.md", note())
        notes = brief.corpus(self.vault)
        projs = {r: {"sessions": 3, "prompts": 1, "text": "x"} for r in ("/r1", "/r2")}
        scores = {r: {k: 0.0 for k in notes} for r in projs}
        self.assertEqual(brief.core(notes, projs, scores), [])

    def test_a_scan_that_never_started_is_reported(self):
        data = self.tmp / "data"
        run._write_status(data, spawned=time.time() - 600)
        self.assertTrue(any("never recorded a start" in b for b in run.banners(data)))

    def test_an_aliased_category_resolves_to_its_hub(self):
        self.write("2026-09-01-x.md", note(categories=('"[[Methods|módszerek]]"',)))
        self.assertEqual(promote.run(self.vault), [])


if __name__ == "__main__":
    unittest.main()
