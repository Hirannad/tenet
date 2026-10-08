import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tenet import cli, paths, promote, verdict  # noqa: E402
from tenet.observer import run  # noqa: E402
from tests.helpers import VaultCase, note  # noqa: E402


def rec(kind, content, **extra):
    return {"type": kind, "message": {"content": content}, **extra}


def tool(name, tid="t1", **args):
    return {"type": "tool_use", "id": tid, "name": name, "input": args}


class GateBase(VaultCase):
    def setUp(self):
        super().setUp()
        self.data = self.tmp / "data"
        self.write("inbox/2026-09-01-draft.md", note(status="proposed"))

    def transcript(self, *extra, work=20, last="Done."):
        rows = [rec("user", "első kérdés", entrypoint="claude-desktop", origin={"kind": "human"})]
        rows += [rec("assistant", [{"type": "text", "text": "working"}]) for _ in range(work - 1)]
        rows += list(extra)
        rows.append(rec("assistant", [{"type": "text", "text": last}]))
        path = self.tmp / "t.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        return {"session_id": "sess-1", "transcript_path": str(path), "background_tasks": []}


class Gate(GateBase):
    def test_fires_at_rest_and_only_once(self):
        payload = self.transcript()
        text = verdict.gate(payload, self.vault, self.data)
        self.assertIn("TENET VERDICT", text)
        self.assertIn('"header": "Draft 1/1"', text)
        self.assertIsNone(verdict.gate(payload, self.vault, self.data))

    def test_each_condition_holds_it_back(self):
        cases = {
            "re-entry": dict(stop_hook_active=True),
            "little work": dict(work=19),
            "question": dict(last="Mehet?"),
            "background": dict(background_tasks=[{"id": "x"}]),
        }
        for name, change in cases.items():
            with self.subTest(name):
                payload = self.transcript(work=change.pop("work", 20), last=change.pop("last", "Done."))
                payload.update(change)
                payload["session_id"] = name
                self.assertIsNone(verdict.gate(payload, self.vault, self.data))

    def test_open_todo_task_or_pending_question_holds_it_back(self):
        cases = {
            "todo": [rec("assistant", [tool("TodoWrite", todos=[{"content": "x", "status": "pending"}])])],
            "task": [rec("assistant", [tool("TaskCreate", subject="x")]),
                     rec("user", [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}], toolUseResult={"task": {"id": "1"}})],
            "auq": [rec("assistant", [tool("AskUserQuestion", questions=[])])],
        }
        for name, extra in cases.items():
            with self.subTest(name):
                payload = self.transcript(*extra)
                payload["session_id"] = name
                if name == "auq":  # the question must be the last thing said
                    rows = Path(payload["transcript_path"]).read_text().splitlines()[:-1]
                    Path(payload["transcript_path"]).write_text("\n".join(rows) + "\n")
                self.assertIsNone(verdict.gate(payload, self.vault, self.data))

    def test_completed_task_does_not_hold_it_back(self):
        payload = self.transcript(
            rec("assistant", [tool("TaskCreate", subject="x")]),
            rec("user", [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}], toolUseResult={"task": {"id": "1"}}),
            rec("assistant", [tool("TaskUpdate", "t2", taskId="1", status="completed")]))
        self.assertIsNotNone(verdict.gate(payload, self.vault, self.data))

    def test_background_launch_without_the_field_reads_the_transcript(self):
        launch = rec("assistant", [tool("Agent", "t9", prompt="x")])
        payload = self.transcript(launch)
        del payload["background_tasks"]
        self.assertIsNone(verdict.gate(payload, self.vault, self.data))
        done = {"type": "attachment", "attachment": {"type": "queued_command", "prompt":
                "<task-notification>\n<task-id>a1</task-id>\n<tool-use-id>t9</tool-use-id>\n<status>completed</status>\n</task-notification>"}}
        payload = self.transcript(launch, done)
        del payload["background_tasks"]
        payload["session_id"] = "other"
        self.assertIsNotNone(verdict.gate(payload, self.vault, self.data))

    def test_scheduled_or_headless_sessions_are_left_alone(self):
        for entry, first in (("sdk-cli", "x"), ("claude-desktop", "<scheduled-task name=x>")):
            payload = self.transcript()
            rows = Path(payload["transcript_path"]).read_text().splitlines()
            rows[0] = json.dumps(rec("user", first, entrypoint=entry))
            Path(payload["transcript_path"]).write_text("\n".join(rows) + "\n")
            payload["session_id"] = entry
            self.assertIsNone(verdict.gate(payload, self.vault, self.data))

    def test_no_backlog_no_question(self):
        (self.vault / "inbox" / "2026-09-01-draft.md").unlink()
        self.assertIsNone(verdict.gate(self.transcript(), self.vault, self.data))


class StopHook(GateBase):
    """The hook entry point: what Claude Code actually runs, stdin in and JSON out."""

    def run_hook(self, payload):
        for var in ("CLAUDE_PLUGIN_OPTION_LEDGER", "CLAUDE_PLUGIN_DATA"):
            os.environ.pop(var, None)
        os.environ.update(TENET_LEDGER=str(self.vault), TENET_DATA=str(self.data))
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), contextlib.redirect_stdout(out):
            self.assertEqual(cli.stop_hook(), 0)
        return out.getvalue()

    def test_fires_as_stop_additional_context(self):
        got = json.loads(self.run_hook(self.transcript()))["hookSpecificOutput"]
        self.assertEqual(got["hookEventName"], "Stop")
        self.assertIn("TENET VERDICT", got["additionalContext"])

    def test_a_failure_is_silent_now_and_shown_at_the_next_session_start(self):
        with mock.patch.object(verdict, "gate", side_effect=RuntimeError("boom")):
            self.assertEqual(self.run_hook(self.transcript()), "")
        self.assertIn("RuntimeError: boom", paths.verdict_errors(self.data).read_text())
        self.assertTrue(any(b.startswith("TENET VERDICT GATE: 1 error(s)") for b in run.banners(self.data)))


class ReviewFindings(GateBase):
    """Regressions from the verdict review, each with the input that broke it."""

    def test_a_reused_task_id_is_open_again(self):
        created = lambda tid, n: [rec("assistant", [tool("TaskCreate", tid, subject=n)]),
                                  rec("user", [{"type": "tool_result", "tool_use_id": tid, "content": "ok"}], toolUseResult={"task": {"id": "1"}})]
        payload = self.transcript(*created("a", "first"), rec("assistant", [tool("TaskUpdate", "b", taskId="1", status="completed")]),
                                  *created("c", "second"))
        self.assertEqual(verdict.busy(payload), "open tasks")

    def test_a_pending_wakeup_holds_it_back(self):
        payload = self.transcript()
        payload["session_crons"] = [{"id": "loop"}]
        self.assertEqual(verdict.busy(payload), "background work")

    def test_two_drafts_with_one_slug_get_distinct_questions(self):
        self.write("inbox/2026-09-15-draft.md", note(status="proposed"))
        text = verdict.gate(self.transcript(), self.vault, self.data)
        questions = [q["question"] for q in json.loads(text.split("\n")[2])]
        self.assertEqual(len(set(questions)), len(questions))

    def test_a_marker_created_by_a_racing_hook_wins(self):
        payload = self.transcript()
        real_exists = Path.exists
        # The other process creates the marker between our check and our write.
        def racing(p):
            if p.name == payload["session_id"] and not real_exists(p):
                p.write_text("other\n")
                return False
            return real_exists(p)
        Path.exists = racing
        try:
            self.assertIsNone(verdict.gate(payload, self.vault, self.data))
        finally:
            Path.exists = real_exists


class Apply(VaultCase):
    def setUp(self):
        super().setUp()
        self.data = self.tmp / "data"

    def ask(self, n):
        for i in range(n):
            self.write(f"inbox/2026-09-{i + 1:02}-d{i}.md", note(status="proposed"))
        rows = [rec("user", "q", entrypoint="cli")] + [rec("assistant", [{"type": "text", "text": "w"}])] * 20
        path = self.tmp / "t.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        text = verdict.gate({"session_id": "s", "transcript_path": str(path), "background_tasks": []}, self.vault, self.data)
        questions = json.loads(text.split("\n")[2])
        ticket = text.split("--ticket ")[1].split()[0]
        return ticket, [q["question"] for q in questions]

    def test_caps_are_the_ones_promote_applies(self):
        # The whole-note cap binds decisions and gotchas; a long pattern draft must still reach a verdict.
        self.write("inbox/2026-09-01-pattern.md", note(kind="pattern", status="proposed", decision_words=450))
        self.write("inbox/2026-09-02-decision.md", note(status="proposed") + "\n## Más\n\n" + "szó " * 450 + "\n")
        self.assertEqual([d.name for d in verdict.eligible(self.vault)], ["2026-09-01-pattern.md"])
        out = "\n".join(promote.run(self.vault))
        self.assertIn("2026-09-02-decision.md — whole note:", out)
        self.assertNotIn("2026-09-01-pattern.md", out)

    def test_batch_size_follows_the_backlog(self):
        self.assertEqual([verdict.batch_size(b) for b in (0, 1, 2, 5, 6, 11, 12, 33)], [0, 1, 2, 2, 3, 3, 4, 4])

    def test_set_status_changes_one_line_only(self):
        path = self.write("inbox/x.md", note(status="proposed"))
        before = path.read_text()
        verdict.set_status(path, "accepted")
        after = path.read_text()
        self.assertEqual(after, before.replace("status: proposed", "status: accepted", 1))

    def test_set_status_never_touches_the_body(self):
        path = self.write("inbox/y.md", "---\ntype: decision\n---\n\nstatus: a line of prose\n")
        with self.assertRaises(ValueError):
            verdict.set_status(path, "accepted")
        self.assertIn("status: a line of prose", path.read_text())

    def test_each_answer_does_what_it_says(self):
        ticket, qs = self.ask(12)
        out = verdict.apply(self.vault, self.data, ticket, {"answers": {
            qs[0]: "Accept", qs[1]: "Discard", qs[2]: "To memory", qs[3]: "szűkítsd egy mondatra"}})
        self.assertTrue((self.vault / "2026-09-01-d0.md").exists())          # accepted and promoted
        self.assertFalse((self.vault / "inbox" / "2026-09-02-d1.md").exists())  # discarded
        self.assertFalse((self.vault / "inbox" / "2026-09-03-d2.md").exists())  # routed to memory
        self.assertTrue((self.vault / "inbox" / "2026-09-04-d3.md").exists())   # edit requested, still proposed
        text = "\n".join(out)
        self.assertIn("TO MEMORY", text)
        self.assertIn("EDIT REQUESTED", text)
        self.assertIn("1 promoted", text)
        log = (self.vault / "_meta" / "observer" / "verdicts.jsonl").read_text()
        self.assertEqual(len(log.splitlines()), 4)

    def test_later_twice_removes_the_option(self):
        for session in ("a", "b", "c"):
            ticket, qs = self.ask(1) if session == "a" else self.reask(session)
            if session != "c":
                verdict.apply(self.vault, self.data, ticket, {"answers": {qs[0]: "Later"}})
        self.assertNotIn('"label": "Later"', self.last_text)

    def reask(self, session):
        rows = [rec("user", "q", entrypoint="cli")] + [rec("assistant", [{"type": "text", "text": "w"}])] * 20
        path = self.tmp / f"{session}.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        self.last_text = verdict.gate({"session_id": session, "transcript_path": str(path), "background_tasks": []}, self.vault, self.data)
        return self.last_text.split("--ticket ")[1].split()[0], [q["question"] for q in json.loads(self.last_text.split("\n")[2])]

    def test_a_ticket_answers_once(self):
        ticket, qs = self.ask(1)
        verdict.apply(self.vault, self.data, ticket, {"answers": {qs[0]: "Later"}})
        self.assertIn("no ticket", verdict.apply(self.vault, self.data, ticket, {"answers": {qs[0]: "Later"}})[0])

    def test_crlf_draft_keeps_its_line_endings(self):
        path = self.write("inbox/crlf.md", note(status="proposed"))
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        verdict.set_status(path, "accepted")
        data = path.read_bytes()
        self.assertIn(b"status: accepted\r\n", data)
        self.assertEqual(data.count(b"\n"), data.count(b"\r\n"))

    def test_an_untracked_discard_stays_recoverable(self):
        ticket, qs = self.ask(1)
        verdict.apply(self.vault, self.data, ticket, {"answers": {qs[0]: "Discard"}})
        self.assertTrue((self.data / "verdict" / "removed" / "2026-09-01-d0.md").exists())

    def test_timeout_is_not_a_verdict_and_changed_drafts_are_refused(self):
        ticket, qs = self.ask(1)
        self.assertIn("timed out", verdict.apply(self.vault, self.data, ticket, {"afk": True, "answers": {qs[0]: "Accept"}})[0])
        draft = self.vault / "inbox" / "2026-09-01-d0.md"
        draft.write_text(draft.read_text() + "\nmore\n")
        self.assertIn("VERDICT REFUSED", verdict.apply(self.vault, self.data, ticket, {"answers": {qs[0]: "Accept"}})[0])
        self.assertIn("proposed", draft.read_text())
        self.assertIn("no ticket", verdict.apply(self.vault, self.data, "nope", {})[0])


if __name__ == "__main__":
    unittest.main()
