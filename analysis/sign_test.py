#!/usr/bin/env python3
"""Exact sign test for a paired selector comparison on frozen candidate dumps.

The official ARC-AGI-2 caliber scores a pair 1 if EITHER of the two predicted
outputs matches ground truth (a pure OR over 2 attempts). Under that caliber the
score of a pair depends only on the UNORDERED SET of two selected candidates,
so a pair-level pass/fail vector is the right unit of analysis.

This script compares two such vectors (e.g. count-desc vs. kgmon) and reports
the discordant-pair counts plus an exact two-sided sign test, which is the
statistic we used in the writeup.

Usage:
    python3 sign_test.py baseline.jsonl candidate.jsonl
      --baseline score_kgmon --candidate score_count_plain

Each input JSONL line must be a JSON object with at least:
    {"task_id": ..., "test_index": ..., "pass": true/false}
and may carry "selector": <name> to select a specific arm from a mixed file.
"""
import argparse
import json
import math
import sys
from collections import defaultdict


def load(path, selector=None):
    """Return {key: pass_bool}. Keys are (task_id, test_index)."""
    out = {}
    with open(path) as handle:
        for lineno, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{lineno}: invalid JSON ({exc})")
            if selector is not None and row.get("selector") != selector:
                continue
            if "pass" not in row:
                raise SystemExit(f"{path}:{lineno}: missing 'pass' field")
            key = (row.get("task_id"), row.get("test_index"))
            if key in out:
                raise SystemExit(f"{path}:{lineno}: duplicate key {key}")
            out[key] = bool(row["pass"])
    return out


def exact_sign_test(gained, lost):
    """Two-sided exact sign test on discordant pairs.

    Under H0 the gained/lost split is Binomial(n, 0.5). We report the
    two-sided p-value as 2 * P(X <= min(gained, lost)), capped at 1.
    """
    n = gained + lost
    if n == 0:
        return 1.0
    k = min(gained, lost)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", help="baseline dumps JSONL")
    parser.add_argument("candidate", help="candidate dumps JSONL")
    parser.add_argument("--baseline-name", default="score_kgmon")
    parser.add_argument("--candidate-name", default="score_count_plain")
    parser.add_argument("--baseline-selector", default=None)
    parser.add_argument("--candidate-selector", default=None)
    args = parser.parse_args()

    base = load(args.baseline, args.baseline_selector)
    cand = load(args.candidate, args.candidate_selector)

    shared = sorted(set(base) & set(cand))
    if not shared:
        raise SystemExit("no shared keys between the two dump files")

    gained = sum(1 for k in shared if cand[k] and not base[k])
    lost = sum(1 for k in shared if base[k] and not cand[k])
    both_pass = sum(1 for k in shared if base[k] and cand[k])
    both_fail = sum(1 for k in shared if not base[k] and not cand[k])

    base_acc = 100.0 * (both_pass + gained) / len(shared)
    cand_acc = 100.0 * (both_pass + lost) / len(shared)

    print(f"pairs compared        : {len(shared)}")
    print(f"both pass             : {both_pass}")
    print(f"both fail             : {both_fail}")
    print(f"gained (base->cand)   : {gained}")
    print(f"lost  (base->cand)   : {lost}")
    print(f"per-pair accuracy     : {base_acc:.2f}% -> {cand_acc:.2f}% "
          f"({cand_acc - base_acc:+.2f} points/pair)")
    print(f"exact sign test (2-sided, n={gained + lost}): "
          f"p = {exact_sign_test(gained, lost):.4g}")
    print()
    print("NOTE: a paired result is only meaningful relative to the leaderboard")
    print("      noise floor. On this baseline the same-bytes spread is 2.08 points,")
    print("      so a per-pair delta of this size is a hypothesis, not an effect.")


if __name__ == "__main__":
    main()
