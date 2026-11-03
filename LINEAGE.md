# Lineage and licences

This repository redistributes code derived from a public Kaggle notebook chain. Every
upstream component and its licence is listed here. The licences of the upstream
notebooks govern their respective code; the files in `src/` are the same code as
produced by the notebook and are covered by the upstream terms plus the Apache-2.0
`LICENSE` in this repository for the parts we wrote.

## Notebook chain

```
nihilisticneuralnet/baseline-nvarc-arc-25-winning-solution-for-t4x2   (ARC'25 champion solution)
  └─ koushikrudra/failed-in-aimo                                     (community base, 1046 votes)
        └─ mikelou1/arc-agi2-lb33-89-minimal-perfpatch                (our base, LB 33.89, 226 votes)
              └─ liuzewen123/arc2-bronze-v7                          (our kernel)
```

- Base notebook URL: https://www.kaggle.com/code/mikelou1/arc-agi2-lb33-89-minimal-perfpatch
- Our kernel URL: https://www.kaggle.com/code/liuzewen123/arc2-bronze-v7

**Action required before publishing this repository:** open the base notebook on Kaggle
and read the licence field in the top-right panel, then record it below. The base
notebook's licence was not verified at the time this file was written, so the
redistribution terms of `src/` should be treated as *pending verification* rather
than assumed to be permissive.

## Model

| Item | Value |
|---|---|
| Model | `sorokin/qwen3_4b_grids15_sft139` |
| Type | Qwen3-4B SFT decoder |
| Licence | Apache-2.0 (verify on the model page before publication) |
| Role | Provides the candidate pool; it is not redistributed here |

## Files in this repository

| Path | Licence | Origin |
|---|---|---|
| `src/arc_loader.py` | upstream notebook licence (verify) | written by the `%%writefile` cell in our kernel |
| `src/arc_decoder.py` | upstream notebook licence (verify) | written by the `%%writefile` cell in our kernel; selector surface |
| `src/arc_solver.py` | upstream notebook licence (verify) | written by the `%%writefile` cell in our kernel |
| `src/starter.py` | upstream notebook licence (verify) | written by the `%%writefile` cell in our kernel |
| `src/cell_03.py` | Apache-2.0 | measurement switches; ours |
| `analysis/*.py` | Apache-2.0 | ours |
| `dumps/*.json` | CC0 | candidate pools and per-candidate scores we produced |
| `README.md`, `LINEAGE.md` | Apache-2.0 | ours |

## Third-party dependencies (not redistributed)

`transformers`, `unsloth`, `torch`, `numpy` — each under its own licence, installed
from PyPI at runtime by the notebook.
