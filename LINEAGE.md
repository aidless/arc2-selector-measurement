# Lineage and licences

This repository redistributes code derived from a public Kaggle notebook chain. Every
upstream component and its licence is listed here. The licences of the upstream
notebooks govern their respective code. The inherited modules in `src/` listed
in the table below are covered by `LICENSE-APACHE-2.0`; everything we wrote
ourselves is MIT-0 (`LICENSE`); the candidate dumps are CC0 (`LICENSE-CC0`).

## Notebook chain

```
nihilisticneuralnet/baseline-nvarc-arc-25-winning-solution-for-t4x2   (upstream notebook slug)
  └─ koushikrudra/failed-in-aimo                                     (community base)
        └─ mikelou1/arc-agi2-lb33-89-minimal-perfpatch                (our base notebook)
              └─ liuzewen123/arc2-bronze-v7                          (our kernel slug)
```

- Base notebook URL: https://www.kaggle.com/code/mikelou1/arc-agi2-lb33-89-minimal-perfpatch
- Our kernel URL: https://www.kaggle.com/code/liuzewen123/arc2-bronze-v7

The base slug contains `lb33-89`. Reading that as a public score of 33.89 is a property of the notebook title, not a score recomputed in this repository. `arc2-bronze-v7` is the kernel slug. It is not a prize recorded by `scores.json` or the dumps.

**Licence check (2026-11-03).** All three upstream notebooks are
public and were pulled successfully with `kaggle kernels pull`; each returns
`is_private: false`. The Apache-2.0 terms of the chain are corroborated by the
downstream NVARC notebook
`christopherdaleman/arc-2026-nvarc-trm-evidence-cost-v1`, whose provenance cell
states that NVARC is derived from Koushik Rudra's Apache-2.0 *Failed in AIMO*
notebook and the Apache-2.0 Sorokin Qwen model, and whose own orchestration is
MIT-0 with inherited components retaining their licences. That is the same split
we use here.

Kaggle does not expose a notebook's licence-selection field through the CLI, so the
authoritative check remains a visual read of the licence badge on each upstream
notebook page. Until that is done, treat the Apache-2.0 attribution for `src/` as
corroborated but not directly observed.

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
| `src/arc_loader.py` | Apache-2.0 (inherited) | written by the `%%writefile` cell in our kernel |
| `src/arc_decoder.py` | Apache-2.0 (inherited) | written by the `%%writefile` cell in our kernel; selector surface |
| `src/arc_solver.py` | Apache-2.0 (inherited) | written by the `%%writefile` cell in our kernel |
| `src/starter.py` | Apache-2.0 (inherited) | written by the `%%writefile` cell in our kernel |
| `src/cell_01.py` | Apache-2.0 (inherited) | global submission/write time buffer |
| `src/cell_02.py` | Apache-2.0 (inherited) | baseline environment workaround |
| `src/cell_08.py` | Apache-2.0 (inherited) | solver invocation cell |
| `src/cell_09.py` | Apache-2.0 (inherited) | evaluation / rerun entry point |
| `src/cell_03.py` | MIT-0 | measurement switches; ours |
| `analysis/*.py` | MIT-0 | ours |
| `dumps/*.json` | CC0 | candidate pools and per-candidate scores we produced |
| `README.md`, `LINEAGE.md`, `scores.json` | MIT-0 | ours |

## Third-party dependencies (not redistributed)

`transformers`, `unsloth`, `torch`, `numpy` — each under its own licence, installed
from PyPI at runtime by the notebook.
