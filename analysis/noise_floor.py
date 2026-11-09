#!/usr/bin/env python3
"""Recompute the same-code public-score spread from a committed scores file.

The floor is the largest spread between runs that share a recorded code hash.
Runs with no hash are printed and excluded. A matching numeric gap on the
excluded rows is not the floor: identity is the hash and the submission refs.

The values are whatever the JSON file stores. This script does not contact
Kaggle and does not re-hash a submission bundle.
"""
import argparse
import json
import sys
from collections import OrderedDict


def points(value):
    """Leaderboard points at the two-decimal precision used in scores.json."""
    return f"{float(value):.2f}"


def load_document(path):
    with open(path) as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        runs = data["runs"]
        meta = {key: value for key, value in data.items() if key != "runs"}
    elif isinstance(data, list):
        runs = data
        meta = {}
    else:
        raise SystemExit(f"{path}: expected an object with 'runs' or a list")
    return meta, runs


def same_code_report(meta, runs):
    """Group runs by recorded hash. Do not invent hashes for rows that lack one."""
    groups = OrderedDict()
    unhashed = []
    for run in runs:
        score = run.get("public_score")
        if score is None:
            raise SystemExit(f"run {run.get('ref')!r} has no public_score")
        ref = str(run.get("ref"))
        sha = run.get("code_sha256")
        if sha is None or sha == "":
            unhashed.append({"ref": ref, "public_score": points(score)})
            continue
        groups.setdefault(str(sha), []).append(
            {"ref": ref, "public_score": points(score)}
        )

    hashed = []
    for sha, entries in groups.items():
        score_values = [float(entry["public_score"]) for entry in entries]
        hashed.append(
            {
                "code_sha256": sha,
                "hash_hex_chars": len(sha),
                "n": len(entries),
                "refs": [entry["ref"] for entry in entries],
                "scores": [entry["public_score"] for entry in entries],
                "spread": points(max(score_values) - min(score_values))
                if len(entries) >= 2
                else None,
            }
        )

    eligible = [group for group in hashed if group["spread"] is not None]
    unique_spreads = {group["spread"] for group in eligible}
    floor = None
    status = "not_established"
    if eligible:
        widest = max(eligible, key=lambda group: float(group["spread"]))
        tied = [group for group in eligible if group["spread"] == widest["spread"]]
        if len(tied) == 1:
            floor = tied[0]
            status = "established"
        else:
            status = "ambiguous"

    excluded_spread = None
    if len(unhashed) >= 2:
        excluded_values = [float(row["public_score"]) for row in unhashed]
        excluded_spread = points(max(excluded_values) - min(excluded_values))

    return {
        "source_status": meta.get("evidence_status", "UNKNOWN"),
        "retrieved_on": meta.get("retrieved_on"),
        "retrieval_command": meta.get("retrieval_command"),
        "live_kaggle_repull": False,
        "status": status,
        "floor_points": None if floor is None else floor["spread"],
        "floor_hash": None if floor is None else floor["code_sha256"],
        "floor_refs": [] if floor is None else list(floor["refs"]),
        "floor_scores": [] if floor is None else list(floor["scores"]),
        "hashed_groups": hashed,
        "excluded_no_hash": unhashed,
        "excluded_no_hash_spread": excluded_spread,
        "distinct_eligible_spreads": sorted(unique_spreads, key=float, reverse=True),
    }


def format_report(report):
    lines = [
        f"{'code_sha256':18} {'n':>2}  {'scores':28}  spread",
    ]
    for group in report["hashed_groups"]:
        spread = group["spread"] if group["spread"] is not None else "n/a"
        score_text = ", ".join(group["scores"])
        lines.append(
            f"{group['code_sha256'][:16]:18} {group['n']:>2}  "
            f"{score_text:28}  {spread}"
        )
        if group["n"] >= 2:
            lines.append(f"{'':18}    refs: {','.join(group['refs'])}")
    lines.append("")
    lines.append("excluded (no code_sha256 recorded):")
    if not report["excluded_no_hash"]:
        lines.append("  (none)")
    else:
        for row in report["excluded_no_hash"]:
            lines.append(f"  ref {row['ref']}  public_score {row['public_score']}")
        lines.append(
            "  numeric spread of excluded rows: "
            f"{report['excluded_no_hash_spread']}"
        )
        lines.append(
            "  NOT included in the floor. The same printed spread does not identify it."
        )
    lines.append("")
    if report["status"] == "established":
        lines.append(f"NOISE FLOOR = {report['floor_points']} points")
        lines.append(f"floor hash = {report['floor_hash']}")
        lines.append(f"floor refs = {','.join(report['floor_refs'])}")
        lines.append(
            "Any smaller public-score gap between two different submissions "
            "is inside this same-code spread."
        )
    elif report["status"] == "ambiguous":
        lines.append("NOISE FLOOR = ambiguous (two recorded hashes share the widest spread)")
    else:
        lines.append("NOISE FLOOR = not established (no recorded hash has >= 2 runs)")
    lines.append("live Kaggle re-pull: no")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scores", help="JSON file describing the runs")
    args = parser.parse_args(argv)
    meta, runs = load_document(args.scores)
    report = same_code_report(meta, runs)
    sys.stdout.write(format_report(report))
    return 0 if report["status"] == "established" else 2


if __name__ == "__main__":
    sys.exit(main())
