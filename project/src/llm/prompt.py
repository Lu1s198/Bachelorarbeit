"""Laden und Rendern der versionierten Prompt-Vorlagen (prompts/*.yaml)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from config import settings


@dataclass(frozen=True)
class PromptTemplate:
    id: str
    version: int
    strategy: str
    system: str
    user_template: str

    def render(self, **variables: str) -> str:
        """Füllt die Platzhalter des user_template."""
        return self.user_template.format(**variables)


def load_prompt(prompt_id: str, prompts_dir: Path | None = None) -> PromptTemplate:
    """Lädt eine Prompt-Vorlage anhand des Dateinamens (ohne .yaml)."""
    prompts_dir = prompts_dir or settings.prompts_dir
    path = prompts_dir / f"{prompt_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt-Vorlage nicht gefunden: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return PromptTemplate(
        id=data["id"],
        version=int(data["version"]),
        strategy=data["strategy"],
        system=data["system"],
        user_template=data["user_template"],
    )


def list_prompt_ids(prompts_dir: Path | None = None) -> list[str]:
    prompts_dir = prompts_dir or settings.prompts_dir
    return sorted(p.stem for p in prompts_dir.glob("*.yaml"))
