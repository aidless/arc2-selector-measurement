#!/usr/bin/env python3
"""Compute the same-bytes leaderboard noise floor for a baseline kernel.

The floor is the largest observed public-score spread between runs whose code
bytes are identical. It bounds the resolution of any leaderboard-based A/B
comparison: deltas smaller than the floor are not attributable to the change
under test.

Usage:
    python3 noise_floor.py scores.json

scores.json format:
    {"runs": [{"ref": "57318970", "code_sha256": "f35df0a5...", "public_score": 31.39},
              {"ref": "57857093", "code_sha256": "f35df0a5...", "public_score": 29.31}]}
"""
import argparse
import json
import sys
from collections import defaultdict


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scores", help="JSON file describing the runs")
    args = parser.parse_args()

    with open(args.scores) as handle:
        data = json.load(handle)
    runs = data["runs"] if isinstance(data, dict) else data

    by_code = defaultdict(list)
    for run in runs:
        sha = run.get("code_sha256")
        score = run.get("public_score")
        if sha is None or score is None:
            continue
        by_code[sha].append((run.get("ref"), float(score)))

    floor = 0.0
    print(f"{'code_sha256':18} {'n':>2}  {'scores':28}  spread")
    for sha, entries in sorted(by_code.items()):
        scores = [s for _, s in entries]
        spread = max(scores) - min(scores)
        if len(entries) >= 2:
            floor = max(floor, spread)
        refs = ",".join(str(r) for r, _ in entries)
        print(f"{sha[:16]:18} {len(entries):>2}  {str(scores):28}  {spread:.2f}")
        if len(entries) >= 2:
            print(f"{'':18}    refs: {refs}")

    print()
    if floor > 0:
        print(f"NOISE FLOOR = {floor:.2f} points")
        print("Any leaderboard delta below this is unresolvable by deployment alone.")
    else:
        print("NOISE FLOOR = not established (no code sha256 has >= 2 runs)")
        print("Collect more same-bytes runs before trusting any sub-point delta.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
