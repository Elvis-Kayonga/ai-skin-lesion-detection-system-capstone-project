"""Score System Usability Scale (SUS) questionnaires.

Usage (from the repo root):
    python backend/scripts/sus_score.py docs/usability/sus_responses.csv

Each row is one participant with answers q1..q10 on a 1-5 scale. Odd statements are positive
(score = answer - 1), even statements are negative (score = 5 - answer); the sum x 2.5 gives 0-100.
"""
import csv
import json
import math
import statistics
import sys
from pathlib import Path

TARGET = 65  # proposal target


def sus_score(answers: list[int]) -> float:
    if len(answers) != 10 or any(a not in (1, 2, 3, 4, 5) for a in answers):
        raise ValueError(f"need 10 answers between 1 and 5, got {answers}")
    total = sum((a - 1) if i % 2 == 0 else (5 - a) for i, a in enumerate(answers))
    return total * 2.5


def summarise(scores: list[float]) -> dict:
    n = len(scores)
    mean = statistics.mean(scores)
    sd = statistics.stdev(scores) if n > 1 else 0.0
    half = 1.96 * sd / math.sqrt(n) if n > 1 else float("nan")   # normal approximation; small n is only indicative
    return {"participants": n, "mean": round(mean, 1), "sd": round(sd, 1), "ci95": [round(mean - half, 1), round(mean + half, 1)],
            "min": min(scores), "max": max(scores), "target": TARGET, "meets_target": mean >= TARGET}


def main(path: str) -> None:
    rows = [r for r in csv.DictReader(open(path, newline="", encoding="utf-8")) if r.get("q1", "").strip()]
    if not rows:
        sys.exit("no filled-in responses found")
    scores = []
    for r in rows:
        s = sus_score([int(r[f"q{i}"]) for i in range(1, 11)])
        scores.append(s)
        print(f"{r['participant']:>4s} ({r.get('role', '')}): {s:5.1f}")
    task_cols = [c for c in rows[0] if c.startswith("task") and c.endswith("_ok")]
    completion = {c: sum(r[c].strip().lower() in ("1", "yes", "y", "true") for r in rows) / len(rows)
                  for c in task_cols if any(r[c].strip() for r in rows)}
    result = {"sus": summarise(scores), "task_completion_rate": completion}
    print(json.dumps(result, indent=2))
    out = Path(path).with_name("sus_results.json")
    out.write_text(json.dumps(result, indent=2))
    print("saved", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/usability/sus_responses.csv")
