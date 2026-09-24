import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from conversion_truth.engine import audit


class GoldenAuditTests(unittest.TestCase):
    def setUp(self):
        self.base = ROOT / "tests"
        self.report = audit(
            self.base / "fixtures" / "truth.csv",
            self.base / "fixtures" / "ga4.csv",
        )

    def test_golden_dataset(self):
        expected = json.loads((self.base / "expected" / "golden.json").read_text())
        self.assertEqual(self.report["summary"], expected["summary"])
        by_key = {f["key"]: f["classification"] for f in self.report["findings"]}
        self.assertEqual(by_key, expected["expected_by_key"])

    def test_value_mismatch_has_explicit_evidence(self):
        finding = next(f for f in self.report["findings"] if f["key"] == "ORD-1005")
        self.assertEqual(finding["classification"], "MISMATCH")
        self.assertEqual(finding["subtype"], "VALUE_MISMATCH")
        self.assertEqual(finding["truth_value"], "200.00")
        self.assertEqual(finding["ga4_value"], "250.00")
        self.assertEqual(finding["confidence"], "HIGH")

    def test_unkeyed_ga4_never_becomes_phantom(self):
        finding = next(f for f in self.report["findings"] if f["key"] == "G-007")
        self.assertEqual(finding["classification"], "UNKNOWN")
        self.assertEqual(finding["confidence"], "LOW")
        self.assertEqual(finding["reason"], "NO_TRANSACTION_ID")


class DecisionEngineTests(unittest.TestCase):
    def setUp(self):
        self.base = ROOT / "tests"
        self.report = audit(
            self.base / "fixtures" / "truth.csv",
            self.base / "fixtures" / "ga4.csv",
        )

    def test_golden_dataset_blocks_trust_with_explicit_policy(self):
        d = self.report["decision"]
        self.assertEqual(d["decision"], "BLOCK_TRUST")
        self.assertEqual(d["evidence_status"], "PARTIAL")
        self.assertEqual(d["confirmed_discrepancies"], 5)
        self.assertEqual(d["confirmed_error_rate"], "71.43%")
        self.assertEqual(d["policy"]["block_error_rate"], "5.00%")

    def test_value_evidence_is_not_called_revenue_loss(self):
        value = self.report["decision"]["value"]
        self.assertEqual(value["ga4_reported"]["EUR"], "870.00")
        self.assertEqual(value["confirmed_overreported"]["EUR"], "220.00")
        self.assertEqual(value["confirmed_underreported"]["EUR"], "110.00")
        self.assertEqual(value["confirmed_discrepancy"]["EUR"], "330.00")
        self.assertEqual(value["unresolved"]["EUR"], "120.00")

    def test_html_report_contains_decision_and_evidence(self):
        from conversion_truth.report import render_html
        html = render_html(self.report)
        self.assertIn("BLOCK_TRUST", html)
        self.assertIn("ORD-1002", html)
        self.assertIn("Confirmed overreported", html)


if __name__ == "__main__":
    unittest.main()
