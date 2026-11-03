#!/usr/bin/env python3
"""Recompute the selector comparison reported in our ARC-AGI-2 writeup.

This is the script that produced the numbers in the "Results" section:
  - kgmon         : 24.07% (39/162)
  - count-desc    : 25.93% (42/162)   -> +3 gained / 0 lost vs kgmon, sign p = .25
  - count+diverse : 27.78% (45/162) on the merged pool, BUT
                     +0 / -1 on each of two independent smaller pools (non-replication)

It reads the official evaluation ground truth and one or more candidate-dump
JSONL files, applies each selector under the official OR caliber
(a pair scores 1 if EITHER of the two selected candidates matches exactly),
and prints the paired comparison plus the exact two-sided sign test.

Candidate dump line format (one JSON object per line):
    {"task": "0934a4d8", "i": 0, "top": [
        {"solution": [[..]], "count": 3, "aug_nll_mean": 43.94, ...}, ...]}

Usage:
    python3 recompute_selectors.py --gt arc-agi_evaluation_solutions.json \\
        --dumps pool_a.jsonl pool_b.jsonl [...] [--label pool_a --label pool_b]
"""
import argparse
import json
import math
import os
from collections import OrderedDict


def norm(grid):
    return tuple(tuple(row) for row in grid)


def hamming(a, b):
    fa = [x for row in a for x in row]
    fb = [x for row in b for x in row]
    if len(fa) != len(fb):
        return 1.0
    return sum(1 for x, y in zip(fa, fb) if x != y) / max(1, len(fa))


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


def pick_kgmon(cands):
    """v3 baseline signal: count minus mean augmentation NLL."""
    return sorted(cands, key=lambda c: -(c["count"] - c["nll"]))


def pick_count(cands):
    """v2 shipped default: count-desc with NLL tiebreak."""
    return sorted(cands, key=lambda c: (-c["count"], c["nll"]))


def pick_diverse(cands, min_dist=0.06):
    """v2div: count-desc plus a normalized-Hamming diversity constraint."""
    ordered = pick_count(cands)
    if not ordered:
        return ordered
    out = [ordered[0]]
    for cand in ordered[1:]:
        if len(out) >= 2:
            break
        if all(hamming(cand["sol"], o["sol"]) > min_dist for o in out):
            out.append(cand)
    if len(out) < 2:
        for cand in ordered:
            if len(out) >= 2:
                break
            if all(hamming(cand["sol"], o["sol"]) > 0 for o in out):
                out.append(cand)
    return out


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


def exact_sign_test(gained, lost):
    n = gained + lost
    if n == 0:
        return 1.0
    k = min(gained, lost)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def compare(base, cand, base_name, cand_name):
    gained = sum(1 for k in base if cand[k] and not base[k])
    lost = sum(1 for k in base if base[k] and not cand[k])
    p = exact_sign_test(gained, lost)
    print(f"  {base_name} -> {cand_name}: +{gained}/-{lost}  sign p = {p:.4g}")


def report(items, title):
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
    print("Interpretation: the diversity constraint looked positive on the largest")
    print("pool and negative on both independent checks. A gain that appears only on")
    print("the pool used to discover it is not a gain -- which is why v2div is not the")
    print("default selector.")


if __name__ == "__main__":
    main()
