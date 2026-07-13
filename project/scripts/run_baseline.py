"""Führt die klassische, regelbasierte Pipeline aus und bewertet sie.

Liefert die Vergleichsbasis (Kapitel 4.6). Ergebnis-JSONs landen -- analog zu
den LLM-Läufen -- unter data/results/<seed>/<task>/ mit provider="baseline".

Aufruf:
    uv run python scripts/run_baseline.py --seed 1
"""

import argparse
import json
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

import pandas as pd  # noqa: E402

from baseline import run_baseline_task  # noqa: E402
from config import settings  # noqa: E402
from dataset.scenarios import ALL_TASKS  # noqa: E402
from evaluation import evaluate_correctness  # noqa: E402


def main(seed: int) -> None:
    for task in ALL_TASKS:
        start = time.perf_counter()
        actual = run_baseline_task(task.id, seed=seed)
        duration = time.perf_counter() - start

        expected = pd.read_parquet(settings.ground_truth_dir / str(seed) / task.expected_output)
        correctness = asdict(evaluate_correctness(actual, expected))

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "baseline",
            "model": "rule_based_pandas",
            "prompt_id": None,
            "prompt_strategy": "regelbasiert",
            "task_id": task.id,
            "task_category": task.category,
            "task_difficulty": task.difficulty,
            "seed": seed,
            "repetition": 1,
            "exec_duration_seconds": duration,
            "exec_success": True,
            "cost_usd": 0.0,
            "correctness": correctness,
            "error": None,
        }
        out_dir = settings.results_dir / str(seed) / task.id
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "baseline.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
        )
        print(f"{task.id}: accuracy={correctness['accuracy']:.3f} "
              f"completeness={correctness['completeness']:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    main(seed=args.seed)
