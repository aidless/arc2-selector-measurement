# ARC-AGI-2 selector vs leaderboard noise

[![CI](https://github.com/aidless/arc2-selector-measurement/actions/workflows/ci.yml/badge.svg)](https://github.com/aidless/arc2-selector-measurement/actions/workflows/ci.yml)

**STATUS: WORK-IN-PROGRESS — not A yet.** Version `0.1.0-wip` (`VERSION`).

<!-- problem-begin -->
This repository measures ARC-AGI-2 selector choices against the same-code public-leaderboard noise floor.
It does not claim a prize-winning solver, and it does not report a high score.
Offline recompute covers the noise floor and dump structure only; selector pass rates stay UNKNOWN until ground-truth labels are available.
<!-- problem-end -->

## Offline path

Python 3.11 or newer, standard library only. No GPU, no Kaggle download, no third-party packages. From a fresh clone:

```bash
python3 analysis/noise_floor.py scores.json
python3 analysis/dump_structure.py
python3 analysis/sign_test.py tests/fixtures/base_pass.jsonl tests/fixtures/cand_pass.jsonl
python3 -m unittest discover -s tests -q
```

`.github/workflows/ci.yml` runs that unittest discovery on Python 3.11, then `python -m compileall -q analysis tests`. The suite compiles the importable modules under `src/`. `src/cell_02.py` and `src/cell_08.py` are notebook shell lines (`!pip`, and a kernel launch that names the CUDA `ptxas` binary). They are not Python modules, and the offline commands do not run them. The job does not train, does not install a requirements file, and does not download the competition.

## Noise floor

`scores.json` transcribes `kaggle competitions submissions -c arc-prize-2026-arc-agi-2` on 2026-11-03 (`evidence_status`: `transcribed_not_reverified`). Each recorded `code_sha256` is 16 hex characters as stored. This checkout does not re-hash a submission bundle and does not re-pull Kaggle.

The floor is hash `96e6f2e7f7113147`, refs `57857093` and `57891197`, public scores 29.72 and 27.64, spread 2.08.
Hash `f35df0a5dff359f8` (refs `57652539` and `57757933`, scores 28.47 and 27.22) spreads 1.25.
Refs `57318970` (31.39) and `57358812` (29.31) have no hash. That excluded gap also prints as 2.08.
The block is the output of `analysis/noise_floor.py` via `same_code_report`.

```json
{
  "distinct_eligible_spreads": [
    "2.08",
    "1.25"
  ],
  "excluded_no_hash": [
    {
      "public_score": "31.39",
      "ref": "57318970"
    },
    {
      "public_score": "29.31",
      "ref": "57358812"
    }
  ],
  "excluded_no_hash_spread": "2.08",
  "floor_hash": "96e6f2e7f7113147",
  "floor_points": "2.08",
  "floor_refs": [
    "57857093",
    "57891197"
  ],
  "floor_scores": [
    "29.72",
    "27.64"
  ],
  "hashed_groups": [
    {
      "code_sha256": "f35df0a5dff359f8",
      "hash_hex_chars": 16,
      "n": 2,
      "refs": [
        "57652539",
        "57757933"
      ],
      "scores": [
        "28.47",
        "27.22"
      ],
      "spread": "1.25"
    },
    {
      "code_sha256": "96e6f2e7f7113147",
      "hash_hex_chars": 16,
      "n": 2,
      "refs": [
        "57857093",
        "57891197"
      ],
      "scores": [
        "29.72",
        "27.64"
      ],
      "spread": "2.08"
    }
  ],
  "live_kaggle_repull": false,
  "retrieval_command": "kaggle competitions submissions -c arc-prize-2026-arc-agi-2",
  "retrieved_on": "2026-11-03",
  "source_status": "transcribed_not_reverified",
  "status": "established"
}
```

## Dump structure

Committed dumps store candidate grids and selector features. They do not store a correctness bit, so this section has no pass rate. Set-disagreement counts are how often two selectors choose a different unordered pair of grids.

`preds_t3_full.candidates.json` has 159 rows, `preds_t4_remaining108.candidates.json` has 101, and `preds_t4_n8.candidates.json` has 57. Their key union has 162 keys. Shared keys are 99 (t3 ∩ remaining108), 56 (t3 ∩ n8), and 0 (remaining108 ∩ n8). `preds_t4_seed4321_first64.candidates.json` has 55 rows and `preds_t4_passb_first64.candidates.json` has 59. `first64` is a run label.

```json
{
  "accuracy": null,
  "accuracy_status": "UNKNOWN_no_ground_truth_in_repo",
  "dump_dir": "dumps",
  "merged_files": [
    "preds_t3_full.candidates.json",
    "preds_t4_n8.candidates.json",
    "preds_t4_remaining108.candidates.json"
  ],
  "merged_t3_n8_remaining108_keys": 162,
  "overlaps": [
    {
      "a": "preds_t3_full.candidates.json",
      "b": "preds_t4_n8.candidates.json",
      "shared_keys": 56
    },
    {
      "a": "preds_t3_full.candidates.json",
      "b": "preds_t4_passb_first64.candidates.json",
      "shared_keys": 56
    },
    {
      "a": "preds_t3_full.candidates.json",
      "b": "preds_t4_remaining108.candidates.json",
      "shared_keys": 99
    },
    {
      "a": "preds_t3_full.candidates.json",
      "b": "preds_t4_seed4321_first64.candidates.json",
      "shared_keys": 53
    },
    {
      "a": "preds_t4_n8.candidates.json",
      "b": "preds_t4_passb_first64.candidates.json",
      "shared_keys": 56
    },
    {
      "a": "preds_t4_n8.candidates.json",
      "b": "preds_t4_remaining108.candidates.json",
      "shared_keys": 0
    },
    {
      "a": "preds_t4_n8.candidates.json",
      "b": "preds_t4_seed4321_first64.candidates.json",
      "shared_keys": 54
    },
    {
      "a": "preds_t4_passb_first64.candidates.json",
      "b": "preds_t4_remaining108.candidates.json",
      "shared_keys": 0
    },
    {
      "a": "preds_t4_passb_first64.candidates.json",
      "b": "preds_t4_seed4321_first64.candidates.json",
      "shared_keys": 55
    },
    {
      "a": "preds_t4_remaining108.candidates.json",
      "b": "preds_t4_seed4321_first64.candidates.json",
      "shared_keys": 0
    }
  ],
  "pools": {
    "preds_t3_full.candidates.json": {
      "kgmon_field_mismatches": 0,
      "rows": 159,
      "rows_with_fewer_than_two_candidates": 11,
      "selector_set_disagreements": {
        "count_vs_diverse": 26,
        "kgmon_vs_count": 69,
        "kgmon_vs_diverse": 81
      },
      "tasks": 114
    },
    "preds_t4_n8.candidates.json": {
      "kgmon_field_mismatches": 0,
      "rows": 57,
      "rows_with_fewer_than_two_candidates": 2,
      "selector_set_disagreements": {
        "count_vs_diverse": 13,
        "kgmon_vs_count": 22,
        "kgmon_vs_diverse": 27
      },
      "tasks": 38
    },
    "preds_t4_passb_first64.candidates.json": {
      "kgmon_field_mismatches": 0,
      "rows": 59,
      "rows_with_fewer_than_two_candidates": 3,
      "selector_set_disagreements": {
        "count_vs_diverse": 14,
        "kgmon_vs_count": 15,
        "kgmon_vs_diverse": 22
      },
      "tasks": 40
    },
    "preds_t4_remaining108.candidates.json": {
      "kgmon_field_mismatches": 0,
      "rows": 101,
      "rows_with_fewer_than_two_candidates": 6,
      "selector_set_disagreements": {
        "count_vs_diverse": 17,
        "kgmon_vs_count": 33,
        "kgmon_vs_diverse": 43
      },
      "tasks": 76
    },
    "preds_t4_seed4321_first64.candidates.json": {
      "kgmon_field_mismatches": 0,
      "rows": 55,
      "rows_with_fewer_than_two_candidates": 6,
      "selector_set_disagreements": {
        "count_vs_diverse": 13,
        "kgmon_vs_count": 22,
        "kgmon_vs_diverse": 28
      },
      "tasks": 37
    }
  },
  "schema": "dump-structure-v1"
}
```

## Selectors

| Selector | Rule | Switch in `src/cell_03.py` |
|---|---|---|
| `kgmon` | count minus mean augmentation NLL | `ARC_SELECTOR=kgmon` |
| `count` | count descending, lower NLL breaks ties | `ARC_SELECTOR=v2` (default) |
| `diverse` | count order, then normalized Hamming above 0.06 | `ARC_SELECTOR=v2div` |

`v2` is the default because it is the short deterministic rule. This checkout does not show a pass-rate advantage for it. The OR caliber scores a test index 1 when either chosen grid matches. Order adds nothing, and a second copy of the same grid adds no coverage. A per-pair pass rate is a different estimand from the Kaggle public score.

## Train path

Separate from the offline path and from CI. A Kaggle ARC Prize 2026 kernel with GPU, plus the model `sorokin/qwen3_4b_grids15_sft139` (not redistributed here), is what `src/` was extracted from. Those modules open the kernel mount paths written in `src/starter.py`, `src/arc_solver.py`, and `src/cell_09.py`. The commands in the offline section do not open them. Measurement switches are `ARC_SELECTOR`, `ARC_COST_ORDER`, `ARC_SCORE_SALT`, and `ARC_DEV_TASKS` in `src/cell_03.py`.

Scoring selectors needs a solutions file you already have the right to use. This repository does not commit one and does not commit an expected accuracy:

```bash
python3 analysis/recompute_selectors.py \
  --gt arc-agi_evaluation_solutions.json \
  --dumps dumps/preds_t3_full.candidates.json
```

## Gaps

1. Selector pass rates are UNKNOWN. Dump rows have `task`, `i`, `elapsed_s`, `n_candidates`, and `top` objects with `solution`, `count`, `beam_score`, `aug_nll_mean`, `kgmon`. There is no correctness field, and `arc-agi_evaluation_solutions.json` is not committed, so `analysis/recompute_selectors.py` cannot run in CI. Historical writeups disagree and are not results: an older README table listed merged-pool 24.0741% / 25.9259% / 27.7778% (39/162, 42/162, 45/162), single-pool figures 22.64% vs 22.01% (+1/−2), 24.75% vs 26.73% (+2/−0), 26.32% (+0/−0), diversity +1/−4, and seed/passb +0/−1. A comment formerly in `src/arc_decoder.py` cited 172 pairs, +2/−0, 23.2558% → 24.4186%, and a diversity note of +3/−0 then +0/−2. UNKNOWN.
2. Public scores are the 2026-11-03 transcription in `scores.json`. The 2.08 spread is recomputed from that file. CI does not re-pull Kaggle, and the 16-hex `code_sha256` values are not re-derived from a bundle.
3. Older negative-result counts have no logs in this tree: 0/172, 7/259, 108 rejected outputs, −0.83, 1/10 vs 1/10, and 3/4 vs 1/4 across environments. UNKNOWN.
4. Upstream notebook licence badges are corroborated, not visually re-read (`LINEAGE.md`). The base slug `lb33-89` is not a score measured here. The kernel slug `arc2-bronze-v7` is a name, not a prize in `scores.json`.

## Failure modes

`FAILURE_MODES.md` covers mistaking Δ for a method gain, treating the missing-hash 31.39/29.31 pair as the same-code floor, and OR-metric pitfalls (order, near-duplicates, merged overlapping pools, mixed units).

## Licences

Code written here (`analysis/`, `src/cell_03.py`, `scores.json`, this README, `LINEAGE.md`, `FAILURE_MODES.md`) is MIT-0 (`LICENSE`). The other files in `src/` are Apache-2.0 (`LICENSE-APACHE-2.0`, per-file table in `LINEAGE.md`). Candidate dumps are CC0 (`LICENSE-CC0`).
