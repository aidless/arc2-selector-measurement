import os
import bz2
import pickle
import numpy as np

def hashable(guess):
    return tuple(map(tuple, guess))

def score_sum(guesses, getter):
    guess_list = list(guesses.values())
    scores = {}
    for g in guess_list:
        h = hashable(g["solution"])
        x = scores[h] = scores.get(h, [[], g["solution"]])
        x[0].append(g)
    scores = [(getter(sc), o) for sc, o in scores.values()]
    scores = sorted(scores, key=(lambda x: x[0]), reverse=True)
    ordered_outputs = [x[-1] for x in scores]
    return ordered_outputs

def getter_full_probmul_3(guesses, baseline=3):
    inf_score = np.sum([baseline-g["beam_score"] for g in guesses])
    aug_score = np.mean([np.sum([baseline-s for s in g["score_aug"]]) for g in guesses])
    return inf_score + aug_score

def score_full_probmul_3(guesses):
    return score_sum(guesses, getter_full_probmul_3)

def getter_kgmon(guesses):
    inf_score = len(guesses)
    aug_score = np.mean([np.mean(g["score_aug"]) for g in guesses])
    return inf_score - aug_score

def score_kgmon(guesses):
    return score_sum(guesses, getter_kgmon)


# ---- selector v2 (bronze v5): count-desc ordering ----
# Evidence (2026-10-30, official caliber = "any of the 2 predicted outputs
# matches the ground truth exactly, you score 1", a pure OR over attempts,
# averaged over 172 pairs): count-desc beats kgmon 2 gained / 0 lost,
# exact sign p = .25, 23.2558% -> 24.4186% per pair. Attempt order is worth
# nothing under OR -- only the SET of two candidates is scored. The diversity
# constraint (attempt_2 Hamming > .06) gained +3/-0 on these dumps but FAILED
# replication on an independent passk pool (+0/-2 overall and +0/-2 within the
# oracle-solvable subset; pooled sign p = .50), so it is NOT the default - it
# stays available as ARC_SELECTOR=v2div for further testing.
def getter_count(guesses):
    # count-desc with kgmon tiebreak; kgmon = count - mean nll is the v3 signal
    return (len(guesses), -(np.mean([np.mean(g["score_aug"]) for g in guesses])))

def score_count(guesses):
    return score_sum(guesses, getter_count)

def _norm_hamming(a, b):
    a = np.asarray(a); b = np.asarray(b)
    if a.shape != b.shape:
        return 1.0
    return float((a != b).mean())

def _pick_diverse(ordered_outputs, min_dist=0.06, n_guesses=2):
    outs = [ordered_outputs[0]]
    for o in ordered_outputs[1:]:
        if len(outs) >= n_guesses:
            break
        if all(_norm_hamming(o, u) > min_dist for u in outs):
            outs.append(o)
    if len(outs) < n_guesses:  # fallback: best remaining distinct solution
        for o in ordered_outputs:
            if len(outs) >= n_guesses:
                break
            if all(_norm_hamming(o, u) > 0 for u in outs):
                outs.append(o)
    return outs

def score_count_diverse(guesses):
    return _pick_diverse(score_sum(guesses, getter_count))

def score_kgmon_diverse(guesses):
    return _pick_diverse(score_sum(guesses, getter_kgmon))

# shipped default: count-desc WITHOUT the diversity constraint (unproven-gain discipline)
def score_count_plain(guesses):
    return score_sum(guesses, getter_count)

selection_algorithms = [
    score_count_plain,
    score_kgmon,
]


class ArcDecoder:
    
    def __init__(self, dataset, n_guesses):
        self.dataset = dataset
        self.n_guesses = n_guesses
        self.decoded_results = {}

    def load_decoded_results(self, store, run_name=""):
        for key in os.listdir(store):
            with bz2.BZ2File(os.path.join(store, key)) as f:
                outputs = pickle.load(f)
            base_key = key.split(".")[0]
            self.decoded_results[base_key] = self.decoded_results.get(base_key, {})
            for i, sample in enumerate(outputs):
                self.decoded_results[base_key][f"{key}{run_name}.out{i}"] = sample

    def run_selection_algo(self, selection_algorithm=None):
        if selection_algorithm is None:
            mode = os.getenv("ARC_SELECTOR", "v2")
            if mode == "kgmon":
                selection_algorithm = score_kgmon
            elif mode == "v2div":
                selection_algorithm = score_count_diverse
            else:  # v2 (default): count-desc, no diversity constraint
                selection_algorithm = score_count_plain
        return {bk: selection_algorithm({k: g for k, g in v.items()}) for bk, v in self.decoded_results.items()}

    def benchmark_selection_algos(self):
        print("*** Benchmark selection algorithms...")

        labels = {}
        num_tasks_per_puzzle = {}
        num_solved_keys = 0
        num_total_keys = 0

        correct_beam_scores = []

        for basekey, basevalues in self.decoded_results.items():

            mult_key, mult_sub = basekey.split("_")
            num_tasks_per_puzzle[mult_key] = max(num_tasks_per_puzzle.get(mult_key, 0), int(mult_sub) + 1)

            labels[basekey] = correct_solution = self.dataset.replies[basekey][0]

            for subkey, sample in basevalues.items():

                solution = sample["solution"]
                beam_score = sample["beam_score"]
                aug_mean = np.mean(sample["score_aug"])

                if np.shape(correct_solution) != np.shape(solution):
                    corr_str = "bad_xy_size"
                elif np.array_equal(correct_solution, solution):
                    corr_str = "ALL_CORRECT"
                    num_solved_keys += 1
                    correct_beam_scores.append(beam_score)
                else:
                    corr_str = "bad_content"

                output_len = f"{solution.shape[0]}x{solution.shape[1]}"

                if corr_str == "ALL_CORRECT":
                    print(f"{corr_str}:{beam_score:8.5f} - {aug_mean:8.5f} {output_len:5s} [{subkey}]")
                num_total_keys += 1

        print(f" subkeys: {num_solved_keys}/{num_total_keys}")
        print(f" avg correct beam score: {np.mean(correct_beam_scores):8.5f}")
        print(f" max correct beam score: {np.max(correct_beam_scores):8.5f}")

        num_puzzles = len(num_tasks_per_puzzle)

        for selection_algorithm in selection_algorithms:
            name = selection_algorithm.__name__
            selected = self.run_selection_algo(selection_algorithm)
            correct_puzzles = {k for k, v in selected.items() if any(np.array_equal(guess, labels[k]) for guess in v[:self.n_guesses])}
            print(correct_puzzles)
            score = sum(1/num_tasks_per_puzzle[k.split("_")[0]] for k in correct_puzzles)
            print(f" acc: {score:5.1f}/{num_puzzles:3} ('{name}')")