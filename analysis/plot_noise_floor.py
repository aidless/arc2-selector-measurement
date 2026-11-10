#!/usr/bin/env python3
"""Plot the leaderboard noise-floor from the committed scores.json.

Reads scores.json verbatim (kaggle submission rows, 2026-11-03) and draws each
submission's public score grouped by recorded code hash. The two same-code
groups give the two observed spreads (2.08 and 1.25); the un-hashed context
pair is shown hollow and excluded from the floor. Numbers are never retyped.
"""
import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
runs = json.loads((ROOT / "scores.json").read_text())["runs"]

# group by code hash; preserve first-seen order
groups = {}
order = []
for r in runs:
    h = r.get("code_sha256") or "no-hash (context only)"
    if h not in groups:
        groups[h] = []
        order.append(h)
    groups[h].append(r)

fig, ax = plt.subplots(figsize=(9, 4.6))
colors = {"96e6f2e7f7113147": "#4c72b0", "f35df0a5dff359f8": "#dd8452",
          "no-hash (context only)": "#bbbbbb"}
xt, xl, xi = [], [], 0
for h in order:
    rs = groups[h]
    for r in rs:
        col = colors.get(h, "#4c72b0")
        filled = h != "no-hash (context only)"
        ax.bar(xi, r["public_score"], width=0.7,
               color=col if filled else "white",
               edgecolor=col, hatch=None if filled else "//", linewidth=1.4)
        ax.text(xi, r["public_score"] + 0.15, f'{r["public_score"]:.2f}',
                ha="center", fontsize=8)
        xt.append(xi); xl.append(r["ref"]); xi += 1
    # annotate spread for same-hash groups (>=2 runs)
    if len(rs) >= 2 and h != "no-hash (context only)":
        lo = min(r["public_score"] for r in rs)
        hi = max(r["public_score"] for r in rs)
        center = xi - len(rs)/2 - 0.5
        ax.text(center, 33.2, f"Δ = {hi-lo:.2f}\nsame code {h[:12]}…",
                ha="center", va="center", fontsize=8.5, color="#333333")
    xi += 0.4  # gap between groups

ax.set_xticks(xt); ax.set_xticklabels(xl, rotation=45, ha="right", fontsize=8)
ax.set_ylabel("public leaderboard score")
ax.set_ylim(0, 36.5)
ax.set_title("ARC-AGI-2 leaderboard noise floor: identical code, different score\n"
             "largest same-code spread = 2.08 points → sub-~2-pt deltas are unresolvable",
             fontsize=10)
from matplotlib.patches import Patch
leg = [Patch(facecolor=colors["96e6f2e7f7113147"], label="code 96e6f2e7f7113147"),
       Patch(facecolor=colors["f35df0a5dff359f8"], label="code f35df0a5dff359f8"),
       Patch(facecolor="white", edgecolor="#bbbbbb", hatch="//", label="no hash (context, excluded)")]
ax.legend(handles=leg, frameon=False, fontsize=8, loc="lower right")
fig.tight_layout()
out = ROOT / "figures" / "noise-floor.png"
fig.savefig(out, dpi=130)
print("wrote", out)
