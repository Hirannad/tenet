import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tenet import ledger, patterns, sweep  # noqa: E402
from tenet.observer import pattern_drafts  # noqa: E402
from tests.helpers import HU_PATTERN_TEMPLATE, PATTERN_SPEC as SPEC, VaultCase, note  # noqa: E402

# Three decisions that each link one another and share vocabulary, plus an unrelated pair.
SHARED = "ellenpróba második kör csendben elcsúszó szám ellenőrzés kapu"


def decision(related, extra_words):
    body = f"## Döntés\n\nrövid\n\n## Miért\n\n{SHARED} {extra_words}\n"
    rel = "".join(f'  - "[[{r}]]"\n' for r in related)
    return (f"---\ntype: decision\ncreated: 2026-09-01\nstatus: accepted\ncategories:\n"
            f'  - "[[Methods]]"\nrevisit: ha X\nrelated:\n{rel}---\n\n{body}')


def prompt_session(text, day="2026-10-01"):
    return {"id": "s", "cwd": "/w", "root": "/w/proj", "scheduled": False, "prompts": [text],
            "asked": [], "paths": [], "assistant": [], "date": day}


class PatternCase(VaultCase):
    def trio(self, names=("2026-09-01-a", "2026-09-02-b", "2026-09-03-c")):
        names = list(names)
        self.write(f"{names[0]}.md", decision([names[1]], "alfa"))
        self.write(f"{names[1]}.md", decision([names[2]], "beta"))
        self.write(f"{names[2]}.md", decision([names[0]], "gamma"))
        return names


class Candidates(PatternCase):
    def test_linked_and_alike_decisions_form_a_group(self):
        names = self.trio()
        examined, groups = patterns.candidates(self.vault)
        self.assertEqual(examined, 3)
        self.assertEqual([m.stem for m in groups[0]["members"]], names)
        self.assertIn("ellenp", groups[0]["terms"])

    def test_a_link_without_overlap_is_no_edge(self):
        self.write("2026-09-01-a.md", decision(["2026-09-02-b"], "alfa"))
        self.write("2026-09-02-b.md", note(extra='related:\n  - "[[2026-09-03-c]]"\n'))
        self.write("2026-09-03-c.md", note())
        self.assertEqual(patterns.candidates(self.vault)[1], [])

    def test_a_pattern_that_derives_from_the_group_retires_it(self):
        names = self.trio()
        self.write("2026-09-09-p.md", f"---\ntype: pattern\nstatus: accepted\n---\n\n[[{names[0]}]] [[{names[1]}]]\n")
        self.assertEqual(patterns.candidates(self.vault)[1], [])

    def test_sweep_says_a_zero_from_a_look_apart_from_a_look_at_nothing(self):
        self.assertIn("not examined", "\n".join(patterns.render(self.vault)))
        self.write("2026-09-01-a.md", decision([], "alfa"))
        self.assertIn("A real zero", "\n".join(patterns.render(self.vault)))
        self.trio()
        self.assertIn("1 group(s)", "\n".join(patterns.render(self.vault)))
        self.assertIn("pattern candidates", "\n".join(sweep.render(self.vault)))


class Drafts(PatternCase):
    QUOTE = "Egy második ellenpróba kör csak ott kell, ahol a szám csendben elcsúszhat."

    def setUp(self):
        super().setUp()
        (self.vault / "templates" / "Pattern Template.md").write_text(HU_PATTERN_TEMPLATE)
        self.trio()

    def test_no_quote_no_draft(self):
        self.assertEqual(pattern_drafts.write(self.vault, [prompt_session("csinálj egy commitot kérlek")]), (1, 0))
        self.assertEqual(ledger.md_files(self.vault / "inbox"), [])

    def test_a_topic_mention_is_not_a_quote(self):
        # Two group terms in a sentence are a topic, below MIN_HITS.
        self.assertEqual(pattern_drafts.write(self.vault, [prompt_session("nézd meg az ellenpróba kapu állapotát most")])[1], 0)

    def test_the_quote_is_evidence_and_it_is_proposed_once(self):
        self.assertEqual(pattern_drafts.write(self.vault, [prompt_session(self.QUOTE)]), (1, 1))
        (draft,) = ledger.md_files(self.vault / "inbox")
        fm, _, body = ledger.read(draft)
        self.assertEqual((fm["type"], fm["status"]), ("pattern", "proposed"))
        self.assertEqual(fm["derived"], ["[[2026-09-01-a]]", "[[2026-09-02-b]]", "[[2026-09-03-c]]"])
        # Nothing is stated yet and no heading stands empty: the statement comes before any verdict.
        self.assertEqual(list(ledger.sections(body)), ["Honnan jött"])
        self.assertIn("> " + self.QUOTE, ledger.sections(body)["Honnan jött"])
        self.assertEqual(pattern_drafts.pending(self.vault), [draft])
        draft.unlink()  # discarded at review: not proposed again
        self.assertEqual(pattern_drafts.write(self.vault, [prompt_session(self.QUOTE)])[1], 0)
        self.assertEqual(ledger.md_files(self.vault / "inbox"), [])

    def test_the_draft_is_named_from_its_decisions_not_its_key(self):
        for f in ledger.notes(self.vault):
            if f.stem.startswith("2026-09-0"):
                f.unlink()
        self.trio(("2026-09-01-alfa", "2026-09-02-ellenproba-kapu-csendben", "2026-09-03-gamma"))
        pattern_drafts.write(self.vault, [prompt_session(self.QUOTE)])
        (draft,) = ledger.md_files(self.vault / "inbox")
        key = patterns.candidates(self.vault)[1][0]["key"]
        self.assertEqual(draft.name, f"{date.today().isoformat()}-pattern-ellenproba-kapu-csendben.md")
        self.assertNotIn(key, draft.name)
        self.assertIn(f"<!-- pattern-key: {key} -->", draft.read_text())

    def test_naming_states_the_rule_first_and_renames_the_draft_after_it(self):
        pattern_drafts.write(self.vault, [prompt_session(self.QUOTE)])
        (draft,) = ledger.md_files(self.vault / "inbox")
        block = ledger.read(draft)[1]
        out = pattern_drafts.name(self.vault, draft.name, SPEC)
        named = self.vault / "inbox" / f"{date.today().isoformat()}-ellenproba-ott-ahol-a-szam-csuszhat.md"
        self.assertEqual(ledger.md_files(self.vault / "inbox"), [named], out)
        _, after, body = ledger.read(named)
        self.assertEqual(after, block)
        got = ledger.sections(body)
        self.assertEqual(list(got), ["A meglátás", "Hol érvényes", "Hol NEM érvényes", "Honnan jött"])
        self.assertEqual(got["A meglátás"].strip(), SPEC["statement"])
        self.assertEqual(got["Hol NEM érvényes"].strip(), SPEC["holds_not"])
        self.assertIn("> " + self.QUOTE, got["Honnan jött"])
        self.assertIn("<!-- pattern-key: ", got["Honnan jött"])
        self.assertEqual(pattern_drafts.pending(self.vault), [])
        self.assertEqual(pattern_drafts.write(self.vault, [prompt_session(self.QUOTE)])[1], 0)  # dedup outlives the rename

    def test_naming_refuses_rather_than_writing_half_a_draft(self):
        pattern_drafts.write(self.vault, [prompt_session(self.QUOTE)])
        (draft,) = ledger.md_files(self.vault / "inbox")
        text = draft.read_text()
        taken = f"{date.today().isoformat()}-ellenproba-ott-ahol-a-szam-csuszhat.md"
        self.write(taken, note())
        cases = {
            "holds_not missing": (draft.name, dict(SPEC, holds_not=" ")),
            "not a pattern draft waiting": ("2026-01-01-nincs.md", SPEC),
            "is taken": (draft.name, SPEC),
        }
        for reason, (name, spec) in cases.items():
            with self.subTest(reason):
                out = pattern_drafts.name(self.vault, name, spec)[0]
                self.assertTrue(out.startswith("PATTERN REFUSED") and reason in out, out)
                self.assertEqual(draft.read_text(), text)
        (self.vault / taken).unlink()
        pattern_drafts.name(self.vault, draft.name, SPEC)
        stated = ledger.md_files(self.vault / "inbox")[0]
        self.assertIn("not a pattern draft waiting", pattern_drafts.name(self.vault, stated.name, SPEC)[0])

    def test_a_scalar_category_is_not_read_letter_by_letter(self):
        for f in ledger.notes(self.vault):
            f.write_text(f.read_text().replace('categories:\n  - "[[Methods]]"', 'categories: "[[Methods]]"'))
        pattern_drafts.write(self.vault, [prompt_session(self.QUOTE)])
        (draft,) = ledger.md_files(self.vault / "inbox")
        self.assertFalse(any(len(c) == 1 for c in ledger.read(draft)[0]["categories"]))


if __name__ == "__main__":
    unittest.main()
