"""Selector ordering, OR scoring on a synthetic fixture, and the sign test.

The fixture grids are invented for the unit test. They are not leaderboard rows.
"""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.recompute_selectors import load_dumps, report
from analysis.selectors import hamming, pick_count, pick_diverse, pick_kgmon
from analysis.sign_test import compare_maps, exact_sign_test, load_pass_map


class SignTestMath(unittest.TestCase):
    def test_known_tails(self):
        self.assertEqual(exact_sign_test(0, 0), 1.0)
        self.assertEqual(exact_sign_test(3, 0), 0.25)
        self.assertEqual(exact_sign_test(6, 0), 0.03125)
        self.assertEqual(exact_sign_test(1, 1), 1.0)

    def test_accuracy_follows_the_named_arm(self):
        base = load_pass_map(ROOT / "tests" / "fixtures" / "base_pass.jsonl")
        cand = load_pass_map(ROOT / "tests" / "fixtures" / "cand_pass.jsonl")
        result = compare_maps(base, cand)
        self.assertEqual(result["gained"], 0)
        self.assertEqual(result["lost"], 1)
        self.assertEqual(result["base_hits"], 2)
        self.assertEqual(result["cand_hits"], 1)
        self.assertAlmostEqual(result["base_accuracy_percent"], 200 / 3)
        self.assertAlmostEqual(result["cand_accuracy_percent"], 100 / 3)

    def test_cli_note_uses_the_committed_floor(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "analysis" / "sign_test.py"),
                str(ROOT / "tests" / "fixtures" / "base_pass.jsonl"),
                str(ROOT / "tests" / "fixtures" / "cand_pass.jsonl"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("66.67% -> 33.33%", completed.stdout)
        self.assertIn("96e6f2e7f7113147", completed.stdout)
        self.assertIn("2.08", completed.stdout)
        self.assertIn("different estimand", completed.stdout)


class SelectorRules(unittest.TestCase):
    def test_diverse_skips_a_near_duplicate(self):
        base = [[0] * 10 for _ in range(10)]
        near = [row[:] for row in base]
        near[0][0] = 1
        far = [[1] * 10 for _ in range(10)]
        self.assertLess(hamming(tuple(map(tuple, base)), tuple(map(tuple, near))), 0.06)
        cands = [
            {"sol": tuple(map(tuple, base)), "count": 3, "nll": 1.0},
            {"sol": tuple(map(tuple, near)), "count": 2, "nll": 1.0},
            {"sol": tuple(map(tuple, far)), "count": 1, "nll": 1.0},
        ]
        chosen = [cand["sol"] for cand in pick_diverse(cands)]
        self.assertEqual(chosen[0], cands[0]["sol"])
        self.assertEqual(chosen[1], cands[2]["sol"])
        self.assertEqual(pick_count(cands)[1]["sol"], cands[1]["sol"])

    def test_or_caliber_on_a_synthetic_pool(self):
        truth = [[1]]
        rows = [
            {
                "task": "toy",
                "i": 0,
                "top": [
                    {"solution": [[1]], "count": 3, "aug_nll_mean": 100.0},
                    {"solution": [[0]], "count": 3, "aug_nll_mean": 0.0},
                    {"solution": [[2]], "count": 2, "aug_nll_mean": 0.0},
                ],
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            dump_path = Path(tmp) / "toy.json"
            gt_path = Path(tmp) / "gt.json"
            dump_path.write_text(json.dumps(rows))
            gt_path.write_text(json.dumps({"toy": [truth]}))
            gt = json.loads(gt_path.read_text())
            items = load_dumps([dump_path], gt)
        self.assertEqual(len(items), 1)
        cands = next(iter(items.values()))
        count_top = pick_count(cands)[:2]
        kgmon_top = pick_kgmon(cands)[:2]
        self.assertTrue(any(cand["correct"] for cand in count_top))
        self.assertFalse(any(cand["correct"] for cand in kgmon_top))
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            report(items, "toy")
        printed = buffer.getvalue()
        self.assertIn("=== toy  (n = 1 items)", printed)
        self.assertIn("kgmon -> count: +1/-0", printed)


if __name__ == "__main__":
    unittest.main()
