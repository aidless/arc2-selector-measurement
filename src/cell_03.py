# ---- v4 measurement switches (edit these three lines to define a variant) ----
# Dev-mode only: "4" | "16" | "64" | "all".  Ignored during competition rerun.
import os
os.environ["ARC_DEV_TASKS"] = "all"
# "1" = cheap tasks first, "0" = v3 dictionary order.
os.environ["ARC_COST_ORDER"] = "0"
# "" = keep v3 salted hash(task_id); any integer = deterministic crc32 seed.
os.environ["ARC_SCORE_SALT"] = ""
print("[v4] switches", {k: os.environ.get(k) for k in ("ARC_DEV_TASKS", "ARC_COST_ORDER", "ARC_SCORE_SALT")})
# selector: "v2" = count-desc (default), "v2div" = count+Hamming>.06, "kgmon" = v3 baseline
os.environ.setdefault("ARC_SELECTOR", "v2")
