"""Unit tests for check_ledger.py. Run: python -m unittest discover -s evals"""
import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import check_ledger as cl  # noqa: E402

AS_OF = dt.date(2026, 11, 21)


def run(name):
    kind, rows, problems = cl.read(HERE / name)
    assert not problems, problems
    if kind == "rules":
        return kind, *cl.check_rules(rows, AS_OF, False)
    return kind, *cl.check_partners(rows, AS_OF, False, 24)


class Rules(unittest.TestCase):
    def setUp(self):
        self.kind, self.errors, self.warns, self.summary = run("fixture_rules.csv")

    def has(self, items, rule_id, text):
        return any(rule_id in i and text in i for i in items)

    def test_kind(self):
        self.assertEqual(self.kind, "rules")

    def test_clean_row_passes(self):
        self.assertFalse(any("(ok," in e for e in self.errors + self.warns))

    def test_model_cannot_confirm_law(self):
        self.assertTrue(self.has(self.errors, "model-confirmed", "cannot confirm"))

    def test_instrument_required(self):
        self.assertTrue(self.has(self.errors, "no-instrument", "names no instrument"))

    def test_rate_needs_date(self):
        self.assertTrue(self.has(self.errors, "rate-no-date", "in_force_from"))

    def test_guidance_warns(self):
        self.assertTrue(self.has(self.warns, "rate-no-date", "guidance"))

    def test_as_made_warns(self):
        self.assertTrue(self.has(self.warns, "as-made", "as made"))

    def test_future_rate_warns(self):
        self.assertTrue(self.has(self.warns, "future", "after the scan date"))

    def test_contents_page_warns(self):
        self.assertTrue(self.has(self.warns, "contents", "contents page"))

    def test_itself_amendment_is_not_an_exemption(self):
        self.assertTrue(self.has(self.warns, "loophole", "as made"))

    def test_unknown_topic(self):
        self.assertTrue(self.has(self.errors, "bad-topic", "unknown topic"))


class Partners(unittest.TestCase):
    def setUp(self):
        self.kind, self.errors, self.warns, self.summary = run("fixture_partners.csv")

    def status(self, oid):
        return self.summary[oid]["status"]

    def test_verified(self):
        self.assertTrue(self.status("good").startswith("VERIFIED"))

    def test_dissolved_dropped(self):
        self.assertEqual(self.status("dissolved"), "DROP (not operating)")

    def test_undated_confirmation_is_error(self):
        self.assertTrue(any("Undated Ltd" in e and "source_date" in e for e in self.errors))

    def test_material_gap(self):
        self.assertTrue(self.status("nomaterial").startswith("OPERATING, material not confirmed"))

    def test_model_cannot_confirm(self):
        self.assertTrue(any("Model Co" in e and "cannot confirm" in e for e in self.errors))

    def test_claim_check_skips_age_warning(self):
        self.assertFalse(any("Old Name Ltd" in w and "months old" in w for w in self.warns))

    def test_invented_dropped(self):
        self.assertEqual(self.status("invented"), "DROP (invented)")


class Shape(unittest.TestCase):
    def test_unquoted_comma(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.csv"
            p.write_text("org_id,org,field,value,source_url,source_type,source_date,accessed,verdict,note\n"
                         "a,A Ltd,exists,Leeds, UK,https://x,register,2026,2026-11-21,confirmed,\n", encoding="utf-8")
            _, _, problems = cl.read(p)
            self.assertTrue(problems and "wrong number of columns" in problems[0])

    def test_unknown_header(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.csv"
            p.write_text("a,b\n1,2\n", encoding="utf-8")
            kind, _, problems = cl.read(p)
            self.assertIsNone(kind)
            self.assertIn("neither ledger", problems[0])


if __name__ == "__main__":
    unittest.main()
