"""Generator für den synthetischen Datensatz.

Der Datensatz simuliert typische ETL-Herausforderungen:
- Inkonsistente Datumsformate
- Duplikate (exakt und fuzzy)
- Fehlende Werte
- Inkonsistente Kategorien (z.B. "DE", "Deutschland", "Germany")
- Outliers / unrealistische Werte
- Joins über mehrere Quellen mit unterschiedlichen Schlüsseln

Alle Generatoren nehmen einen `seed`-Parameter — damit ist der Datensatz
exakt reproduzierbar. Das ist die Grundlage für die Reproduzierbarkeit
der ganzen Studie.
"""

from pathlib import Path

import pandas as pd
from faker import Faker

from project.src.config import settings


def generate_customers(n_rows: int = 1000, seed: int = settings.random_seed) -> pd.DataFrame:
    """Erzeugt eine Kundentabelle mit absichtlichen Datenqualitätsproblemen.

    TODO: erweitern um:
    - Duplikate (5% der Zeilen)
    - Datumsformate mischen
    - Tippfehler in Ländern
    """
    fake = Faker("de_DE")
    Faker.seed(seed)

    rows = [
        {
            "customer_id": i,
            "name": fake.name(),
            "email": fake.email(),
            "country": fake.country_code(),
            "registered_at": fake.date_this_decade().isoformat(),
        }
        for i in range(n_rows)
    ]
    return pd.DataFrame(rows)


def save_dataset(df: pd.DataFrame, name: str, output_dir: Path | None = None) -> Path:
    """Speichert einen DataFrame als Parquet (kompakt, typsicher)."""
    output_dir = output_dir or settings.synthetic_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}.parquet"
    df.to_parquet(path, index=False)
    return path
