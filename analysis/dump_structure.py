#!/usr/bin/env python3
"""Summarise committed candidate dumps without ground truth.

Reports row counts, task counts, key overlap, whether the stored ``kgmon``
field equals ``count - aug_nll_mean``, and how often two selectors choose a
different unordered pair of grids. Pass rate is not computed: the dumps have
no correctness bit.
"""
import json
import sys
from collections import OrderedDict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from analysis.selectors import SELECTORS, norm, selected_set

REPO_ROOT = Path(__file__).resolve().parents[1]
HEADLINE_MERGE = (
    "preds_t3_full.candidates.json",
    "preds_t4_n8.candidates.json",
    "preds_t4_remaining108.candidates.json",
)


def load_pool(path):
    with open(path) as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise SystemExit(f"{path}: expected a JSON list of candidate rows")

    items = OrderedDict()
    tasks = set()
    mismatches = 0
    short_rows = 0
    for row_index, row in enumerate(rows):
        try:
            key = (row["task"], row["i"])
        except KeyError as exc:
            raise SystemExit(f"{path}:{row_index}: missing {exc}") from exc
        if key in items:
            raise SystemExit(f"{path}:{row_index}: duplicate key {key}")
        tasks.add(row["task"])
        cands = []
        seen = set()
        for cand in row["top"]:
            sol = norm(cand["solution"])
            if sol in seen:
                raise SystemExit(f"{path}:{row_index}: duplicate solution inside top")
            seen.add(sol)
            count = cand["count"]
            nll = cand["aug_nll_mean"]
            recorded = cand["kgmon"]
            if abs((count - nll) - recorded) > 1e-6:
                mismatches += 1
            cands.append({"sol": sol, "count": count, "nll": nll})
        if len(cands) < 2:
            short_rows += 1
        items[key] = cands
    return items, {
        "rows": len(items),
        "tasks": len(tasks),
        "kgmon_field_mismatches": mismatches,
        "rows_with_fewer_than_two_candidates": short_rows,
    }


def _set_diffs(items):
    names = ("kgmon", "count", "diverse")
    chosen = {
        name: {key: selected_set(cands, SELECTORS[name]) for key, cands in items.items()}
        for name in names
    }
    diffs = {}
    for left_index, left in enumerate(names):
        for right in names[left_index + 1 :]:
            diffs[f"{left}_vs_{right}"] = sum(
                1 for key in items if chosen[left][key] != chosen[right][key]
            )
    return diffs


def summarize(dump_dir):
    dump_dir = Path(dump_dir)
    paths = sorted(dump_dir.glob("*.json"))
    if not paths:
        raise SystemExit(f"no JSON dumps in {dump_dir}")

    pools = {}
    indexes = {}
    for path in paths:
        items, stats = load_pool(path)
        stats["selector_set_disagreements"] = _set_diffs(items)
        pools[path.name] = stats
        indexes[path.name] = set(items)

    overlaps = []
    names = list(indexes)
    for left_index, left in enumerate(names):
        for right in names[left_index + 1 :]:
            overlaps.append(
                {
                    "a": left,
                    "b": right,
                    "shared_keys": len(indexes[left] & indexes[right]),
                }
            )

    missing = [name for name in HEADLINE_MERGE if name not in indexes]
    if missing:
        raise SystemExit(f"headline dumps missing: {missing}")
    merged = set()
    for name in HEADLINE_MERGE:
        merged |= indexes[name]

    return {
        "accuracy": None,
        "accuracy_status": "UNKNOWN_no_ground_truth_in_repo",
        "dump_dir": "dumps",
        "merged_t3_n8_remaining108_keys": len(merged),
        "merged_files": list(HEADLINE_MERGE),
        "overlaps": overlaps,
        "pools": pools,
        "schema": "dump-structure-v1",
    }


def main():
    summary = summarize(REPO_ROOT / "dumps")
    json.dump(summary, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
