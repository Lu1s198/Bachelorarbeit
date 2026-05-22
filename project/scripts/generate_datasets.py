from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from dataset.generator import generate_full_dataset


def main(seed: int = 1):
    paths = generate_full_dataset(seed=seed)
    for name, p in paths.items():
        print(f"{name}: {p}")


if __name__ == "__main__":
    main()
