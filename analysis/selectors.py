"""Selector orderings used by the offline dump analysis.

These match the rules in ``src/arc_decoder.py`` (count minus mean NLL,
count-descending with NLL tie-break, and the 0.06 normalized-Hamming
diversity constraint). They do not score correctness.
"""


def norm(grid):
    return tuple(tuple(int(cell) for cell in row) for row in grid)


def hamming(a, b):
    """Normalized Hamming distance. Different shapes count as distance 1."""
    fa = [cell for row in a for cell in row]
    fb = [cell for row in b for cell in row]
    if len(fa) != len(fb):
        return 1.0
    if not fa:
        return 0.0
    return sum(1 for x, y in zip(fa, fb) if x != y) / len(fa)


def pick_kgmon(cands):
    """v3 signal: count minus mean augmentation NLL, descending."""
    return sorted(cands, key=lambda c: -(c["count"] - c["nll"]))


def pick_count(cands):
    """v2 default: count descending, lower NLL as the tie-break."""
    return sorted(cands, key=lambda c: (-c["count"], c["nll"]))


def pick_diverse(cands, min_dist=0.06):
    """v2div: count order, then a normalized-Hamming gap above ``min_dist``."""
    ordered = pick_count(cands)
    if not ordered:
        return ordered
    out = [ordered[0]]
    for cand in ordered[1:]:
        if len(out) >= 2:
            break
        if all(hamming(cand["sol"], other["sol"]) > min_dist for other in out):
            out.append(cand)
    if len(out) < 2:
        for cand in ordered:
            if len(out) >= 2:
                break
            if all(hamming(cand["sol"], other["sol"]) > 0 for other in out):
                out.append(cand)
    return out


SELECTORS = {
    "kgmon": pick_kgmon,
    "count": pick_count,
    "diverse": pick_diverse,
}


def selected_set(cands, picker):
    """Unordered set of grids in the top two slots. Order is not part of the set."""
    return frozenset(cand["sol"] for cand in picker(cands)[:2])
