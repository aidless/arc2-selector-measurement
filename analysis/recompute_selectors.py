#!/usr/bin/env python3
"""Score selectors against a ground-truth file the caller supplies.

This repository does not commit ``arc-agi_evaluation_solutions.json`` and does
not pin a pass rate. With no ground-truth file, use ``analysis/dump_structure.py``,
which reports overlap and set disagreement only.

When ``--gt`` is a local solutions file the caller is allowed to use, each
(task, test index) scores 1 if either of the two selected grids matches that
index exactly (OR over two attempts). The script then prints paired counts and
an exact two-sided sign test. Those counts are not a Kaggle public score.

Dump rows are JSON lists (one object per test index) with ``task``, ``i``, and
``top[].solution / count / aug_nll_mean``.

Usage:
    python3 analysis/recompute_selectors.py --gt arc-agi_evaluation_solutions.json \\
        --dumps dumps/preds_t3_full.candidates.json
"""
import argparse
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from analysis.selectors import norm, pick_count, pick_diverse, pick_kgmon
from analysis.sign_test import exact_sign_test


def load_dumps(paths, gt):
    """Merge one or more candidate dumps into {(task, index): [candidate, ...]}."""
    items = OrderedDict()
    for path in paths:
        with open(path) as handle:
            rows = json.load(handle)
        if isinstance(rows, dict):
            rows = list(rows.values())
        for row in rows:
            task, idx = row["task"], row["i"]
            if task not in gt:
                continue
            truth = norm(gt[task][idx])
            key = (task, idx)
            bucket = items.setdefault(key, OrderedDict())
            for cand in row["top"]:
                sol = norm(cand["solution"])
                bucket[sol] = {
                    "sol": sol,
                    "count": cand.get("count", 0),
                    "nll": cand.get("aug_nll_mean", 0.0),
                    "correct": sol == truth,
                }
    return OrderedDict(
        (k, list(v.values())) for k, v in items.items() if v
    )


SELECTORS = OrderedDict([
    ("kgmon", pick_kgmon),
    ("count", pick_count),
    ("diverse", pick_diverse),
])


def or_caliber_vector(items, picker):
    """Pass vector: True iff either of the top-2 selected candidates is exact."""
    return OrderedDict(
        (k, any(c["correct"] for c in picker(cands)[:2]))
        for k, cands in items.items()
    )


def compare(base, cand, base_name, cand_name):
    gained = sum(1 for k in base if cand[k] and not base[k])
    lost = sum(1 for k in base if base[k] and not cand[k])
    p = exact_sign_test(gained, lost)
    print(f"  {base_name} -> {cand_name}: +{gained}/-{lost}  sign p = {p:.4g}")


def report(items, title):
    if not items:
        print(f"\n=== {title}  (n = 0 items)")
        print("  no rows matched the ground-truth file")
        return {}
    vectors = {name: or_caliber_vector(items, fn) for name, fn in SELECTORS.items()}
    print(f"\n=== {title}  (n = {len(items)} items)")
    for name, vec in vectors.items():
        acc = 100.0 * sum(vec.values()) / len(vec)
        print(f"  {name:9} acc = {acc:.4f}%  ({sum(vec.values())}/{len(vec)})")
    compare(vectors["kgmon"], vectors["count"], "kgmon", "count")
    compare(vectors["kgmon"], vectors["diverse"], "kgmon", "diverse")
    compare(vectors["count"], vectors["diverse"], "count", "diverse")
    oracle = {k: any(c["correct"] for c in cands) for k, cands in items.items()}
    sub = [k for k in vectors["kgmon"] if oracle[k]]
    if sub:
        print(f"  -- within oracle-solvable subset (n = {len(sub)}) --")
        for a, b in (("kgmon", "diverse"), ("kgmon", "count")):
            gained = sum(1 for k in sub if vectors[b][k] and not vectors[a][k])
            lost = sum(1 for k in sub if vectors[a][k] and not vectors[b][k])
            print(f"  {a} -> {b}: +{gained}/-{lost}  sign p = {exact_sign_test(gained, lost):.4g}")
    return vectors


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gt", required=True, help="arc-agi_evaluation_solutions.json")
    ap.add_argument("--dumps", nargs="+", required=True, help="candidate dump JSONL/JSON files")
    ap.add_argument("--label", action="append", default=None,
                    help="label for a dump file; repeatable, order matches --dumps")
    args = ap.parse_args()

    with open(args.gt) as handle:
        gt = json.load(handle)

    labels = args.label or [os.path.basename(p) for p in args.dumps]
    if len(labels) == 1 and len(args.dumps) > 1:
        # A single label may describe several files (e.g. one merged pool).
        labels = labels * len(args.dumps)
    if len(labels) != len(args.dumps):
        raise SystemExit("--label count must match --dumps count")

    for label, path in zip(labels, args.dumps):
        report(load_dumps([path], gt), label)

    if len(args.dumps) > 1:
        report(load_dumps(args.dumps, gt), "MERGED (all pools)")

    print()
    print("These percentages use only the ground-truth file passed on the command line.")
    print("This repository does not pin them. Overlapping dumps are not independent samples.")
    print("A per-pair accuracy is not a Kaggle public score.")


if __name__ == "__main__":
    main()
