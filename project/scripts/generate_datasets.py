"""Erzeugt den synthetischen Datensatz UND die Ground Truth für einen Seed.

Aufruf:
    uv run python scripts/generate_datasets.py            # Seed 1
    uv run python scripts/generate_datasets.py --seed 99
"""

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from dataset.generator import generate_full_dataset  # noqa: E402
from dataset.reference import build_all_ground_truth  # noqa: E402


def main(seed: int = 1) -> None:
    paths = generate_full_dataset(seed=seed)
    print(f"Rohdaten & saubere Referenz (Seed {seed}):")
    for name, p in paths.items():
        print(f"  {name}: {p}")

    gt = build_all_ground_truth(seed=seed)
    print("Ground Truth je Aufgabe:")
    for task_id, p in gt.items():
        print(f"  {task_id}: {p}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    main(seed=args.seed)
