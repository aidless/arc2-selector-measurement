#!/usr/bin/env python3
"""Exact two-sided sign test on a paired pass/fail JSONL.

Each line is ``{"task_id", "test_index", "pass": bool}``. Optional ``selector``
selects one arm from a mixed file. This script does not read the candidate
dumps and does not produce a leaderboard score.
"""
import argparse
import json
import math
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from analysis.noise_floor import load_document, same_code_report


def exact_sign_test(gained, lost):
    """Two-sided exact sign test. Under H0 each discordant pair is a fair coin."""
    discordant = gained + lost
    if discordant == 0:
        return 1.0
    smaller = min(gained, lost)
    tail = sum(math.comb(discordant, i) for i in range(smaller + 1)) / (2 ** discordant)
    return min(1.0, 2 * tail)


def load_pass_map(path, selector=None):
    """Return {(task_id, test_index): pass_bool}."""
    out = {}
    with open(path) as handle:
        for lineno, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{lineno}: invalid JSON ({exc})") from exc
            if selector is not None and row.get("selector") != selector:
                continue
            if "pass" not in row:
                raise SystemExit(f"{path}:{lineno}: missing 'pass' field")
            key = (row.get("task_id"), row.get("test_index"))
            if key in out:
                raise SystemExit(f"{path}:{lineno}: duplicate key {key}")
            out[key] = bool(row["pass"])
    return out


def compare_maps(base, cand):
    shared = sorted(set(base) & set(cand))
    if not shared:
        raise SystemExit("no shared keys between the two files")
    gained = sum(1 for key in shared if cand[key] and not base[key])
    lost = sum(1 for key in shared if base[key] and not cand[key])
    both_pass = sum(1 for key in shared if base[key] and cand[key])
    both_fail = sum(1 for key in shared if not base[key] and not cand[key])
    base_hits = both_pass + lost
    cand_hits = both_pass + gained
    return {
        "n": len(shared),
        "both_pass": both_pass,
        "both_fail": both_fail,
        "gained": gained,
        "lost": lost,
        "base_hits": base_hits,
        "cand_hits": cand_hits,
        "base_accuracy_percent": 100.0 * base_hits / len(shared),
        "cand_accuracy_percent": 100.0 * cand_hits / len(shared),
        "sign_p": exact_sign_test(gained, lost),
    }


def floor_note(scores_path):
    """Describe the committed noise floor. Never hard-code the spread."""
    path = Path(scores_path)
    if not path.is_file():
        return "same-code noise floor: UNKNOWN (scores file not found)"
    meta, runs = load_document(path)
    report = same_code_report(meta, runs)
    if report["status"] != "established":
        return f"same-code noise floor: UNKNOWN (status {report['status']})"
    return (
        "same-code noise floor from "
        f"{path.name}: {report['floor_points']} public-score points "
        f"on recorded hash {report['floor_hash']} "
        f"(refs {', '.join(report['floor_refs'])}; "
        f"scores {', '.join(report['floor_scores'])}). "
        "A per-pair pass rate is a different estimand from that public score. "
        "live Kaggle re-pull: no."
    )


def format_comparison(result, baseline_name, candidate_name, note):
    delta = result["cand_accuracy_percent"] - result["base_accuracy_percent"]
    lines = [
        f"pairs compared        : {result['n']}",
        f"both pass             : {result['both_pass']}",
        f"both fail             : {result['both_fail']}",
        f"gained (base->cand)   : {result['gained']}",
        f"lost  (base->cand)   : {result['lost']}",
        (
            f"per-pair accuracy     : {result['base_accuracy_percent']:.2f}% -> "
            f"{result['cand_accuracy_percent']:.2f}% ({delta:+.2f} points/pair)"
        ),
        (
            f"exact sign test (2-sided, n={result['gained'] + result['lost']}): "
            f"p = {result['sign_p']:.4g}"
        ),
        "",
        f"names                 : {baseline_name} -> {candidate_name}",
        f"NOTE: {note}",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", help="baseline pass/fail JSONL")
    parser.add_argument("candidate", help="candidate pass/fail JSONL")
    parser.add_argument("--baseline-name", default="baseline")
    parser.add_argument("--candidate-name", default="candidate")
    parser.add_argument("--baseline-selector", default=None)
    parser.add_argument("--candidate-selector", default=None)
    parser.add_argument(
        "--scores",
        default=str(Path(__file__).resolve().parents[1] / "scores.json"),
        help="committed scores file used only for the noise-floor note",
    )
    args = parser.parse_args(argv)

    result = compare_maps(
        load_pass_map(args.baseline, args.baseline_selector),
        load_pass_map(args.candidate, args.candidate_selector),
    )
    sys.stdout.write(
        format_comparison(
            result,
            args.baseline_name,
            args.candidate_name,
            floor_note(args.scores),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
