"""README, VERSION, and path hygiene stay aligned with the recomputed evidence."""
import json
import py_compile
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.dump_structure import summarize
from analysis.noise_floor import load_document, same_code_report


def fenced_json(section_text):
    match = re.search(r"```json\n(.*?)\n```", section_text, re.DOTALL)
    if match is None:
        raise AssertionError("missing json fence")
    return json.loads(match.group(1))


class HonestySurfaceTest(unittest.TestCase):
    def setUp(self):
        self.readme = (ROOT / "README.md").read_text()
        self.failures = (ROOT / "FAILURE_MODES.md").read_text()
        self.version = (ROOT / "VERSION").read_text().strip()

    def test_version_is_wip(self):
        self.assertEqual(self.version, "0.1.0-wip")
        self.assertIn(self.version, self.readme)
        self.assertNotIn("1.0.0", self.version)

    def test_problem_statement_is_three_lines(self):
        match = re.search(
            r"<!-- problem-begin -->\n(.*?)<!-- problem-end -->",
            self.readme,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        lines = [line for line in match.group(1).splitlines() if line.strip()]
        self.assertEqual(len(lines), 3)
        blob = " ".join(lines).lower()
        self.assertIn("noise floor", blob)
        self.assertIn("prize-winning", blob)
        self.assertIn("unknown", blob)

    def test_status_and_noise_block_match_scores(self):
        self.assertIn("STATUS: WORK-IN-PROGRESS — not A yet", self.readme)
        meta, runs = load_document(ROOT / "scores.json")
        report = same_code_report(meta, runs)
        noise_section = self.readme.split("## Noise floor", 1)[1].split("## ", 1)[0]
        self.assertEqual(fenced_json(noise_section), report)
        for ref in report["floor_refs"]:
            self.assertIn(ref, noise_section)
        self.assertIn(report["floor_hash"], noise_section)
        self.assertIn(report["floor_points"], noise_section)

    def test_dump_block_matches_recompute(self):
        section = self.readme.split("## Dump structure", 1)[1].split("## ", 1)[0]
        self.assertEqual(fenced_json(section), summarize(ROOT / "dumps"))

    def test_unhashed_rows_are_not_given_a_hash_in_prose(self):
        for line in self.readme.splitlines():
            if "57318970" in line or "31.39" in line:
                self.assertNotIn("f35df0a5dff359f8", line)
                self.assertNotIn("96e6f2e7f7113147", line)

    def test_historical_pass_rates_stay_in_the_unknown_gap(self):
        head, gaps = self.readme.split("## Gaps", 1)
        for token in ("24.0741%", "23.2558%", "0/172", "7/259"):
            self.assertNotIn(token, head)
            self.assertIn(token, gaps)
        self.assertIn("UNKNOWN", gaps)
        self.assertNotIn("23.2558", (ROOT / "src" / "arc_decoder.py").read_text())

    def test_failure_modes_cover_the_three_misreads(self):
        self.assertIn("method gain", self.failures.lower())
        self.assertIn("Missing-hash", self.failures)
        self.assertIn("OR-metric", self.failures)
        meta, runs = load_document(ROOT / "scores.json")
        report = same_code_report(meta, runs)
        self.assertIn(report["floor_hash"], self.failures)
        self.assertIn(report["floor_points"], self.failures)
        for ref, score in zip(report["floor_refs"], report["floor_scores"]):
            self.assertIn(ref, self.failures)
            self.assertIn(score, self.failures)
        summary = summarize(ROOT / "dumps")
        pools = summary["pools"]
        shared = {(row["a"], row["b"]): row["shared_keys"] for row in summary["overlaps"]}
        t3 = "preds_t3_full.candidates.json"
        rem = "preds_t4_remaining108.candidates.json"
        n8 = "preds_t4_n8.candidates.json"
        self.assertIn(
            f"`{t3}` shares {shared[(t3, rem)]} keys with `{rem}` and {shared[(t3, n8)]} keys with `{n8}`",
            self.failures,
        )
        self.assertIn(
            f"The union of the three has {summary['merged_t3_n8_remaining108_keys']} keys, "
            f"fewer than {pools[t3]['rows']} + {pools[rem]['rows']} + {pools[n8]['rows']}",
            self.failures,
        )
        self.assertIn(
            f"({pools[t3]['rows_with_fewer_than_two_candidates']} in the t3 dump, "
            f"{pools[rem]['rows_with_fewer_than_two_candidates']} in remaining108, "
            f"{pools[n8]['rows_with_fewer_than_two_candidates']} in n8)",
            self.failures,
        )

    def test_no_machine_absolute_paths_outside_kernel_sources(self):
        banned = tuple("/" + name for name in ("home/", "Users/", "workspace", "tmp/"))
        roots = [ROOT / "analysis", ROOT / "tests", ROOT / ".github" / "workflows"]
        files = [ROOT / "README.md", ROOT / "FAILURE_MODES.md", ROOT / "VERSION", ROOT / "scores.json", ROOT / "LINEAGE.md"]
        for folder in roots:
            files.extend(path for path in folder.rglob("*") if path.is_file())
        for path in files:
            if path.name == "test_honesty_surface.py":
                continue
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            text = path.read_text(errors="replace")
            for token in banned:
                self.assertNotIn(token, text, f"{path} contains {token}")
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
        self.assertNotIn("/kaggle/", ci)
        self.assertIn("unittest discover -s tests", ci)
        self.assertNotIn("pip install", ci)

    def test_src_compiles_except_notebook_shell_cells(self):
        failed = []
        with tempfile.TemporaryDirectory() as tmp:
            for path in sorted((ROOT / "src").glob("*.py")):
                try:
                    py_compile.compile(
                        str(path),
                        cfile=str(Path(tmp) / (path.name + "c")),
                        doraise=True,
                    )
                except py_compile.PyCompileError:
                    failed.append(path.name)
        self.assertEqual(failed, ["cell_02.py", "cell_08.py"])
        analysis_text = "\n".join(
            path.read_text() for path in (ROOT / "analysis").rglob("*.py")
        )
        self.assertNotIn("/kaggle/", analysis_text)


if __name__ == "__main__":
    unittest.main()
