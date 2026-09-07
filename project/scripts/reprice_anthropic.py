"""Recalculate stored Anthropic costs without making new model calls."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FACTOR = 2 / 3


def scale_costs(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "cost_usd" and isinstance(child, (int, float)):
                value[key] = round(child * FACTOR, 6)
            else:
                scale_costs(child)
    elif isinstance(value, list):
        for child in value:
            scale_costs(child)


def is_anthropic(record: dict) -> bool:
    identifiers = [record.get("provider"), record.get("model"),
                   record.get("requested_model")]
    return any(
        (isinstance(identifier, str) and identifier.startswith("claude-"))
        or identifier == "anthropic"
        for identifier in identifiers
    )


def main() -> None:
    changed = 0
    for path in (ROOT / "data").rglob("*.json"):
        with path.open(encoding="utf-8") as handle:
            record = json.load(handle)
        if not isinstance(record, dict) or not is_anthropic(record):
            continue
        scale_costs(record)
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        changed += 1
    print(f"Updated Anthropic result files: {changed}")


if __name__ == "__main__":
    main()
