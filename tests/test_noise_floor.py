"""Drift guard: the same-code floor is recomputed from scores.json."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.noise_floor import load_document, points, same_code_report


class NoiseFloorTest(unittest.TestCase):
    def setUp(self):
        meta, runs = load_document(ROOT / "scores.json")
        self.meta = meta
        self.runs = runs
        self.report = same_code_report(meta, runs)

    def test_provenance_is_a_transcription(self):
        self.assertEqual(self.meta["evidence_status"], "transcribed_not_reverified")
        self.assertEqual(self.meta["retrieved_on"], "2026-11-03")
        self.assertIn("kaggle competitions submissions", self.meta["retrieval_command"])
        self.assertFalse(self.report["live_kaggle_repull"])

    def test_floor_identity(self):
        self.assertEqual(self.report["status"], "established")
        self.assertEqual(self.report["floor_points"], "2.08")
        self.assertEqual(self.report["floor_hash"], "96e6f2e7f7113147")
        self.assertEqual(self.report["floor_refs"], ["57857093", "57891197"])
        self.assertEqual(self.report["floor_scores"], ["29.72", "27.64"])
        self.assertEqual(points(29.72 - 27.64), "2.08")

    def test_recorded_hashes_are_16_hex_chars(self):
        for group in self.report["hashed_groups"]:
            self.assertEqual(group["hash_hex_chars"], 16)
            self.assertEqual(len(group["code_sha256"]), 16)
            int(group["code_sha256"], 16)

    def test_second_pair_and_excluded_pair(self):
        by_hash = {group["code_sha256"]: group for group in self.report["hashed_groups"]}
        other = by_hash["f35df0a5dff359f8"]
        self.assertEqual(other["refs"], ["57652539", "57757933"])
        self.assertEqual(other["scores"], ["28.47", "27.22"])
        self.assertEqual(other["spread"], "1.25")
        self.assertEqual(
            self.report["excluded_no_hash"],
            [
                {"ref": "57318970", "public_score": "31.39"},
                {"ref": "57358812", "public_score": "29.31"},
            ],
        )
        self.assertEqual(self.report["excluded_no_hash_spread"], "2.08")
        self.assertNotEqual(self.report["floor_hash"], "f35df0a5dff359f8")
        for row in self.report["excluded_no_hash"]:
            self.assertNotIn(row["ref"], self.report["floor_refs"])

    def test_cli_names_the_hash(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "analysis" / "noise_floor.py"), str(ROOT / "scores.json")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        text = completed.stdout
        self.assertIn("NOISE FLOOR = 2.08 points", text)
        self.assertIn("floor hash = 96e6f2e7f7113147", text)
        self.assertIn("floor refs = 57857093,57891197", text)
        self.assertIn("excluded (no code_sha256 recorded)", text)
        self.assertIn("ref 57318970", text)
        self.assertIn("NOT included in the floor", text)
        self.assertIn("live Kaggle re-pull: no", text)

    def test_ambiguous_widest_spread_is_not_a_floor(self):
        report = same_code_report(
            {},
            [
                {"ref": "1", "code_sha256": "aaaaaaaaaaaaaaaa", "public_score": 10.0},
                {"ref": "2", "code_sha256": "aaaaaaaaaaaaaaaa", "public_score": 12.0},
                {"ref": "3", "code_sha256": "bbbbbbbbbbbbbbbb", "public_score": 3.0},
                {"ref": "4", "code_sha256": "bbbbbbbbbbbbbbbb", "public_score": 5.0},
            ],
        )
        self.assertEqual(report["status"], "ambiguous")
        self.assertIsNone(report["floor_hash"])
        self.assertIsNone(report["floor_points"])

    def test_missing_hash_is_not_invented(self):
        report = same_code_report(
            {},
            [
                {"ref": "9", "public_score": 31.39},
                {"ref": "8", "code_sha256": "cccccccccccccccc", "public_score": 1.0},
                {"ref": "7", "code_sha256": "cccccccccccccccc", "public_score": 1.5},
            ],
        )
        self.assertEqual(report["floor_hash"], "cccccccccccccccc")
        self.assertEqual(report["floor_points"], "0.50")
        self.assertEqual(report["excluded_no_hash"][0]["ref"], "9")
        joined = json.dumps(report["hashed_groups"])
        self.assertNotIn("31.39", joined)


if __name__ == "__main__":
    unittest.main()
