"""Tests for check_ledger.py against a fixture with one seeded fault per facility.

Run: python -m unittest discover -s evals   (from the skill folder)
"""
import datetime as dt
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import check_ledger  # noqa: E402

AS_OF = dt.date(2026, 11, 8)


class LedgerChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.errors, cls.warns, cls.summary = check_ledger.run(HERE / "fixture_ledger.csv", AS_OF, 24, False)
        cls.err = "\n".join(cls.errors)
        cls.warn = "\n".join(cls.warns)

    def status(self, fid):
        return self.summary[fid]["status"]

    def test_good_facility_verified(self):
        self.assertTrue(self.status("good").startswith("VERIFIED"))
        self.assertNotIn("Good Recycler", self.err)

    def test_invented_facility_dropped(self):
        self.assertEqual(self.status("ghost"), "DROP (invented)")

    def test_closed_plant_dropped_and_old_source_warned(self):
        self.assertEqual(self.status("stale"), "DROP (not operating)")
        self.assertIn("Stale Plant, exists): source is 90 months old", self.warn)

    def test_capacity_needs_basis(self):
        self.assertIn("No Basis Co, capacity): capacity without a basis", self.err)

    def test_aggregator_cannot_confirm(self):
        self.assertIn("an aggregator alone cannot confirm", self.err)
        self.assertEqual(self.status("agg"), "UNVERIFIED")

    def test_model_cannot_confirm(self):
        self.assertIn("Model Confirmed, exists): a model answer cannot confirm", self.err)
        self.assertIn("Model Confirmed, exists): confirmed without a source URL", self.err)

    def test_confirmed_needs_date(self):
        self.assertIn("No Date Co, exists): confirmed claim has no source_date", self.err)

    def test_confirmed_closure_drops_facility(self):
        # regression: first version marked a liquidated company VERIFIED
        self.assertEqual(self.status("closed"), "DROP (not operating)")

    def test_wrong_process_is_not_an_outlet(self):
        self.assertEqual(self.status("yarn"), "RECHECK FIT (a process or polymer claim was wrong)")

    def test_url_findings(self):
        self.assertEqual(check_ledger.url_finding("200"), "ok")
        self.assertEqual(check_ledger.url_finding("404"), "error")
        self.assertEqual(check_ledger.url_finding("403"), "warning")
        self.assertEqual(check_ledger.url_finding("SSL certificate problem"), "warning")

    def test_unquoted_comma_gives_clear_error(self):
        errors, _, _ = check_ledger.run(HERE / "fixture_bad_commas.csv", AS_OF, 24, False)
        self.assertIn("wrong number of columns", errors[0])

    def test_exit_code_fails_on_errors(self):
        self.assertTrue(self.errors)


if __name__ == "__main__":
    unittest.main()
