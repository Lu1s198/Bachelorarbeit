"""Führt die LLM-Experimente über die Matrix Modell x Prompt x Aufgabe aus.

Beispiele:
    # Alles (alle Provider mit Key, alle Prompts, alle Aufgaben):
    uv run python scripts/run_experiments.py

    # Nur ein Provider, eine Strategie, eine Aufgabe (schneller Test):
    uv run python scripts/run_experiments.py \
        --providers anthropic --prompts v1_zero_shot \
        --tasks cleaning_easy_missing_and_whitespace --repetitions 1
"""

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from dataset.scenarios import ALL_TASKS  # noqa: E402
from experiments.runner import run_experiments  # noqa: E402
from llm.prompt import list_prompt_ids  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--providers", nargs="+", default=["anthropic", "openai", "google", "ollama"])
    parser.add_argument("--prompts", nargs="+", default=None, help="Default: alle Vorlagen in prompts/")
    parser.add_argument("--tasks", nargs="+", default=None, help="Default: alle neun Aufgaben")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()

    prompt_ids = args.prompts or list_prompt_ids()
    task_ids = args.tasks or [t.id for t in ALL_TASKS]

    results = run_experiments(
        providers=args.providers,
        prompt_ids=prompt_ids,
        task_ids=task_ids,
        seed=args.seed,
        repetitions=args.repetitions,
        temperature=args.temperature,
    )
    ok = sum(1 for r in results if (r.get("correctness") or {}).get("comparable"))
    print(f"\nFertig: {len(results)} Läufe, davon {ok} auswertbar.")


if __name__ == "__main__":
    main()
