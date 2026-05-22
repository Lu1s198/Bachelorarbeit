"""Zentrale Konfiguration. Liest .env und stellt typsichere Settings bereit."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Globale Einstellungen. Werte kommen aus .env oder Umgebungsvariablen."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API-Keys (optional, damit Tests ohne Keys laufen können)
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    google_api_key: str | None = None
    ollama_host: str = "http://localhost:11434"

    # Reproduzierbarkeit
    random_seed: int = 42

    # Pfade
    data_dir: Path = PROJECT_ROOT / "data"
    synthetic_dir: Path = PROJECT_ROOT / "data" / "synthetic"
    ground_truth_dir: Path = PROJECT_ROOT / "data" / "ground_truth"
    results_dir: Path = PROJECT_ROOT / "data" / "results"
    prompts_dir: Path = PROJECT_ROOT / "prompts"


settings = Settings()
