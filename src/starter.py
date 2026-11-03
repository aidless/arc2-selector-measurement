import os
import time
import json
import torch
import argparse
import torch.multiprocessing as mp


def estimated_work(task):
    """Cheap cost proxy: 16x train tokens plus 8x estimated test output cells."""
    def cells(grid):
        return len(grid) * len(grid[0]) if grid and grid[0] else 0

    train_cells = sum(cells(p["input"]) + cells(p["output"]) for p in task["train"])
    test_cells = sum(cells(t["input"]) for t in task["test"])
    ratios = sorted(cells(p["output"]) / max(1, cells(p["input"])) for p in task["train"])
    ratio = ratios[len(ratios) // 2] if ratios else 1.0
    return 16 * train_cells + 8 * round(test_cells * ratio)


def build_queue_keys(data, rerun_mode, dev_tasks):
    """Return the ordered task keys. Baseline order is `sorted(data)`."""
    keys = sorted(data.keys())
    if not rerun_mode:
        if dev_tasks == "all":
            pass
        elif dev_tasks.isdigit():
            n = int(dev_tasks)
            if n > 4:
                keys = keys[: max(n, 4)]
            else:
                keys = [k for k in keys if k in ["0934a4d8", "36a08778", "981571dc", "aa4ec2a5"]]
        else:
            keys = [k for k in keys if k in ["0934a4d8", "36a08778", "981571dc", "aa4ec2a5"]]
    if os.getenv("ARC_COST_ORDER", "0") == "1":
        keys = sorted(keys, key=lambda k: (estimated_work(data[k]), k))
    return keys


def local_worker(rank, queue, end_time):
    
    os.environ["CUDA_VISIBLE_DEVICES"] = str(rank)

    torch.set_default_device("cpu")

    # Fix Unsloth patching issue
    if rank > 0:
        while not os.path.exists(f"/kaggle/worker{rank-1}"):
            time.sleep(5)
    
    from arc_solver import worker

    with open(f"/kaggle/worker{rank}", "w") as f:
        f.write("Ok")
    
    print(f"[Rank {rank}] start!")
    
    worker(rank, queue, end_time)
    
    print(f"[Rank {rank}] done!")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--end-time", type=float, default=0.0)
    args = parser.parse_args()

    rerun_mode = os.getenv("KAGGLE_IS_COMPETITION_RERUN")

    if rerun_mode:
        test_path = "/kaggle/input/competitions/arc-prize-2026-arc-agi-2/arc-agi_test_challenges.json"
    else:
        test_path = "/kaggle/input/competitions/arc-prize-2026-arc-agi-2/arc-agi_evaluation_challenges.json"

    with open(test_path, "r") as f:
        data = json.load(f)

    queue = mp.Manager().Queue()

    dev_tasks = os.getenv("ARC_DEV_TASKS", "4")
    keys = build_queue_keys(data, rerun_mode, dev_tasks)
    print(f"[queue] rerun={bool(rerun_mode)} dev_tasks={dev_tasks} "
          f"cost_order={os.getenv('ARC_COST_ORDER', '0')} n={len(keys)}")
    print(f"[queue] first5={keys[:5]} last2={keys[-2:]}")

    for key in keys:
        queue.put(key)
    for _ in range(4):
        queue.put(None)
    
    mp.spawn(local_worker, args=(queue, args.end_time), nprocs=4)