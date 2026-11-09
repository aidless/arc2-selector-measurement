# FAILURE_MODES

Ways this measurement is misread, and the committed evidence each one collides with.

## Reading Δ as a method gain

The same-code floor is **2.08** public-score points on recorded hash `96e6f2e7f7113147`, refs `57857093` and `57891197`, scores **29.72** and **27.64**. Those two rows are the same recorded code with different public scores. The gap is a noise floor for leaderboard comparisons. A later submission that lands one or two public points away from either row has not shown that a selector, a prompt, or a schedule worked. The other hashed pair, `f35df0a5dff359f8` (refs `57652539`, `57757933`, scores 28.47 and 27.22), spreads **1.25**. In `scores.json`, 2.08 is the widest same-code spread, not a constant of the whole leaderboard.

`analysis/noise_floor.py` recomputes that identification from `scores.json`. CI does not re-pull Kaggle. The recorded `code_sha256` strings are 16 hex characters. This tree does not re-hash a submission bundle.

## Missing-hash pairs are weaker

Refs `57318970` (31.39) and `57358812` (29.31) store no `code_sha256`. Their numeric gap also prints as **2.08**. Matching the printed number does not make them the floor. Assigning hash `f35df0a5dff359f8` to those two scores, which an older README example did, names the wrong rows and still produces a printout of 2.08. The script excludes empty hashes, prints them under `excluded`, and reports the floor hash and refs on their own lines.

## OR-metric pitfalls

The pair score is 1 when either of the two predicted grids matches the ground-truth grid. Consequences:

- Attempt order carries no points. A ranker and a set-coverage rule are different procedures. `kgmon` orders by count minus mean NLL. The metric only asks what the two chosen grids cover.
- A second grid at normalized Hamming 0 adds no coverage. `diverse` (Hamming greater than 0.06) can change the unordered pair. A set-disagreement count is not an accuracy.
- Overlapping dumps are not independent samples. `preds_t3_full.candidates.json` shares 99 keys with `preds_t4_remaining108.candidates.json` and 56 keys with `preds_t4_n8.candidates.json`. The remaining108 and n8 files share 0 keys. The union of the three has 162 keys, fewer than 159 + 101 + 57. A comparison that appears only after merging those files is a description of a stitched pool.
- A per-pair pass rate on a dump is a different estimand from the Kaggle public score. Placing a pass-rate gap "under" the 2.08 public-score floor mixes units.
- Pass rate needs ground truth. The committed dumps have `task`, `i`, `elapsed_s`, `n_candidates`, and `top` entries with `solution`, `count`, `beam_score`, `aug_nll_mean`, and `kgmon`. There is no correctness field, and `arc-agi_evaluation_solutions.json` is not in the repo. Historical writeups that disagree with each other stay UNKNOWN: a merged-pool table of 24.0741% / 25.9259% / 27.7778% (39/162, 42/162, 45/162), single-pool notes of 22.64% vs 22.01% (+1/−2), 24.75% vs 26.73% (+2/−0), 26.32% (+0/−0), diversity +1/−4 and +0/−1, and a code comment that cited 172 pairs, +2/−0, 23.2558% → 24.4186% plus a diversity note of +3/−0 then +0/−2.
- The exact two-sided sign test on a handful of discordant pairs stays easy to over-read. As a property of the test, +3/−0 gives p = 0.25 and +6/−0 gives p = 0.03125. Those identities are checked in `tests/`. They are not measured selector effects in this checkout.
- Some rows have fewer than two candidates (11 in the t3 dump, 6 in remaining108, 2 in n8). Those rows cannot fill both attempt slots.
- `preds_t4_seed4321_first64.candidates.json` has 55 rows and `preds_t4_passb_first64.candidates.json` has 59 rows. `first64` is a run label, not a row count.

## What a green check mark is

CI runs `python -m unittest discover -s tests -q` and a syntax compile. A passing run means those commands passed on the committed files. It is not competition acceptance, a leaderboard rank, or a prize. The kernel slug `arc2-bronze-v7` is a notebook name.
