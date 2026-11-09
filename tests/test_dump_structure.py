"""Recompute dump structure from the committed JSON. No ground truth, no pass rate."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.dump_structure import summarize


class DumpStructureTest(unittest.TestCase):
    def setUp(self):
        self.summary = summarize(ROOT / "dumps")

    def test_accuracy_is_explicitly_unknown(self):
        self.assertIsNone(self.summary["accuracy"])
        self.assertEqual(self.summary["accuracy_status"], "UNKNOWN_no_ground_truth_in_repo")

    def test_headline_pools(self):
        pools = self.summary["pools"]
        self.assertEqual(pools["preds_t3_full.candidates.json"]["rows"], 159)
        self.assertEqual(pools["preds_t3_full.candidates.json"]["tasks"], 114)
        self.assertEqual(pools["preds_t4_remaining108.candidates.json"]["rows"], 101)
        self.assertEqual(pools["preds_t4_remaining108.candidates.json"]["tasks"], 76)
        self.assertEqual(pools["preds_t4_n8.candidates.json"]["rows"], 57)
        self.assertEqual(pools["preds_t4_n8.candidates.json"]["tasks"], 38)
        self.assertEqual(pools["preds_t4_seed4321_first64.candidates.json"]["rows"], 55)
        self.assertEqual(pools["preds_t4_passb_first64.candidates.json"]["rows"], 59)
        self.assertEqual(self.summary["merged_t3_n8_remaining108_keys"], 162)

    def test_overlaps_and_set_disagreement(self):
        shared = {(row["a"], row["b"]): row["shared_keys"] for row in self.summary["overlaps"]}
        self.assertEqual(
            shared[("preds_t3_full.candidates.json", "preds_t4_remaining108.candidates.json")],
            99,
        )
        self.assertEqual(
            shared[("preds_t3_full.candidates.json", "preds_t4_n8.candidates.json")],
            56,
        )
        self.assertEqual(
            shared[("preds_t4_n8.candidates.json", "preds_t4_remaining108.candidates.json")],
            0,
        )
        t3 = self.summary["pools"]["preds_t3_full.candidates.json"]["selector_set_disagreements"]
        self.assertEqual(t3["kgmon_vs_count"], 69)
        self.assertEqual(t3["kgmon_vs_diverse"], 81)
        self.assertEqual(t3["count_vs_diverse"], 26)
        for pool in self.summary["pools"].values():
            self.assertEqual(pool["kgmon_field_mismatches"], 0)

    def test_cli_matches_function(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "analysis" / "dump_structure.py")],
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), self.summary)


if __name__ == "__main__":
    unittest.main()
