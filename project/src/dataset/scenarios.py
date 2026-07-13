"""
Scenarios for the evaluation of the dataset.
Structure:
- 3 Categories: Cleaning, Deduplication, Transformation
- 3 Difficulty Levels per Category
- Hardest Transformation = Join + Aggregation
"""

from dataclasses import dataclass, field
from enum import StrEnum


class Category(StrEnum):
    CLEANING = "cleaning"
    DEDUPLICATION = "deduplication"
    TRANSFORMATION = "transformation"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True)
class Task:
    id: str
    category: Category
    difficulty: Difficulty
    description: str                    # prompt
    input_files: list[str]              # relative to data/synthetic/
    expected_output: str                # relative to data/ground_truth/
    evaluation_focus: list[str]         # criterias
    target_schema: str = ""             # column:type description for schema-enriched prompts
    notes: str = ""                     # notes


# ----- cleaning -----

CLEANING_TASKS: list[Task] = [
    Task(
        id="cleaning_easy_missing_and_whitespace",
        category=Category.CLEANING,
        difficulty=Difficulty.EASY,
        description=(
            "Lies die Datei `customers_raw.csv` ein. Entferne führende und "
            "nachfolgende Leerzeichen aus allen Textspalten. Ersetze fehlende "
            "Werte in der Spalte `country_code` durch 'UNKNOWN'. Schreibe das "
            "Ergebnis als Parquet-Datei `cleaned_customers.parquet`."
        ),
        input_files=["customers_raw.csv"],
        expected_output="cleaning_easy_missing_and_whitespace.parquet",
        evaluation_focus=["accuracy", "completeness"],
        target_schema=(
            "customer_id: int, full_name: string (trimmed), email: string (trimmed), "
            "country: string (trimmed; 'UNKNOWN' where missing), registered_at: string (unchanged)"
        ),
    ),
    Task(
        id="cleaning_medium_date_formats",
        category=Category.CLEANING,
        difficulty=Difficulty.MEDIUM,
        description=(
            "Die Spalte `registered_at` in `customers_raw.csv` enthält "
            "Datumsangaben in unterschiedlichen Formaten (ISO-Datum, "
            "deutsches Format DD.MM.YYYY, US-Format Month DD YYYY und "
            "Unix-Timestamps). Normalisiere alle Werte auf das ISO-Format "
            "YYYY-MM-DD. Schreibe das Ergebnis als Parquet-Datei."
        ),
        input_files=["customers_raw.csv"],
        expected_output="cleaning_medium_date_formats.parquet",
        evaluation_focus=["accuracy", "consistency"],
        target_schema=(
            "customer_id: int, full_name: string, email: string, country: string, "
            "registered_at: string (ISO date, format YYYY-MM-DD)"
        ),
    ),
    Task(
        id="cleaning_hard_semantic_unification",
        category=Category.CLEANING,
        difficulty=Difficulty.HARD,
        description=(
            "Die Spalte `country` in `customers_raw.csv` enthält Länder in "
            "verschiedenen Schreibweisen und Sprachen (z.B. 'DE', 'Deutschland', "
            "'Germany', 'Deutshcland'). Vereinheitliche alle Werte auf den "
            "zweistelligen ISO-3166-1-alpha-2-Code (z.B. 'DE'). Werte, die "
            "sich nicht eindeutig zuordnen lassen, sollen den Wert 'UNKNOWN' "
            "erhalten. Schreibe das Ergebnis als Parquet-Datei."
        ),
        input_files=["customers_raw.csv"],
        expected_output="cleaning_hard_semantic_unification.parquet",
        evaluation_focus=["accuracy", "consistency"],
        target_schema=(
            "customer_id: int, full_name: string, email: string, "
            "country: string (2-letter ISO-3166-1 alpha-2 code, or 'UNKNOWN'), registered_at: string"
        ),
        notes="Hier ist semantisches Verständnis nötig — interessante Achse für LLMs.",
    ),
]


# ----- deduplication -----

DEDUPLICATION_TASKS: list[Task] = [
    Task(
        id="dedup_easy_exact_duplicates",
        category=Category.DEDUPLICATION,
        difficulty=Difficulty.EASY,
        description=(
            "Lies `customers_raw.csv` ein und entferne exakte Duplikate "
            "(Zeilen, in denen alle Spaltenwerte identisch sind). Behalte "
            "jeweils das erste Vorkommen. Schreibe das Ergebnis als Parquet-Datei."
        ),
        input_files=["customers_raw.csv"],
        expected_output="dedup_easy_exact_duplicates.parquet",
        evaluation_focus=["accuracy", "completeness"],
        target_schema=(
            "customer_id: int, full_name: string, email: string, country: string, "
            "registered_at: string (same columns as input, one row per exact duplicate group)"
        ),
    ),
    Task(
        id="dedup_medium_key_duplicates",
        category=Category.DEDUPLICATION,
        difficulty=Difficulty.MEDIUM,
        description=(
            "Entferne in `customers_raw.csv` Zeilen, in denen die `email` "
            "mehrfach vorkommt. Bei mehreren Zeilen mit gleicher E-Mail soll "
            "die Zeile mit dem jüngsten `registered_at`-Wert behalten werden. "
            "Schreibe das Ergebnis als Parquet-Datei."
        ),
        input_files=["customers_raw.csv"],
        expected_output="dedup_medium_key_duplicates.parquet",
        evaluation_focus=["accuracy"],
        target_schema=(
            "customer_id: int, full_name: string, email: string, country: string, "
            "registered_at: string (same columns as input, one row per unique email)"
        ),
    ),
    Task(
        id="dedup_hard_fuzzy_duplicates",
        category=Category.DEDUPLICATION,
        difficulty=Difficulty.HARD,
        description=(
            "In `customers_raw.csv` befinden sich Fuzzy-Duplikate: gleiche "
            "Person, aber unterschiedliche Schreibweisen des Namens (Tippfehler, "
            "unterschiedliche Groß-/Kleinschreibung, mit/ohne Mittelinitial) "
            "und unterschiedliche E-Mail-Schreibweisen (Punkte vor dem @, "
            "unterschiedliche Groß-/Kleinschreibung). Erkenne diese Duplikate "
            "und entferne sie. Behalte jeweils die Zeile mit der vollständigsten "
            "Information. Schreibe das Ergebnis als Parquet-Datei."
        ),
        input_files=["customers_raw.csv"],
        expected_output="dedup_hard_fuzzy_duplicates.parquet",
        evaluation_focus=["accuracy", "consistency"],
        target_schema=(
            "customer_id: int, full_name: string, email: string, country: string, "
            "registered_at: string (same columns as input, one row per real person)"
        ),
        notes="Hauptmessung: Fuzzy-Matching-Strategie der LLMs.",
    ),
]


# ----- transformations -----

TRANSFORMATION_TASKS: list[Task] = [
    Task(
        id="transform_easy_type_conversion",
        category=Category.TRANSFORMATION,
        difficulty=Difficulty.EASY,
        description=(
            "Lies `products_raw.csv` ein. Konvertiere die Spalte `price_eur` "
            "von Text (z.B. '19,99', '€19.99', '19.99 EUR') in einen "
            "numerischen Wert (Float, Dezimaltrennzeichen Punkt). Konvertiere "
            "die Spalte `in_stock` von Text ('ja'/'nein', 'true'/'false', '1'/'0') "
            "in Boolean. Schreibe das Ergebnis als Parquet-Datei."
        ),
        input_files=["products_raw.csv"],
        expected_output="transform_easy_type_conversion.parquet",
        evaluation_focus=["accuracy", "consistency"],
        target_schema=(
            "product_id: int, name: string, category: string, "
            "price_eur: float (decimal point '.'), in_stock: bool"
        ),
    ),
    Task(
        id="transform_medium_derived_columns",
        category=Category.TRANSFORMATION,
        difficulty=Difficulty.MEDIUM,
        description=(
            "Lies `orders_raw.csv` ein. Berechne für jede Bestellzeile eine "
            "neue Spalte `total_eur` als `quantity * unit_price_eur`. "
            "Extrahiere aus `ordered_at` zusätzlich die Spalten `order_year` "
            "(Integer) und `order_month` (Integer, 1-12). Schreibe das Ergebnis "
            "als Parquet-Datei."
        ),
        input_files=["orders_raw.csv"],
        expected_output="transform_medium_derived_columns.parquet",
        evaluation_focus=["accuracy", "completeness"],
        target_schema=(
            "order_id: int, customer_id: int, product_id: int, quantity: int, "
            "unit_price_eur: float, ordered_at: string (ISO date), "
            "total_eur: float (= quantity * unit_price_eur), "
            "order_year: int, order_month: int (1-12)"
        ),
    ),
    Task(
        id="transform_hard_join_and_aggregate",
        category=Category.TRANSFORMATION,
        difficulty=Difficulty.HARD,
        description=(
            "Verknüpfe `orders_raw.csv`, `customers_raw.csv` und `products_raw.csv` "
            "über die jeweiligen ID-Spalten. Bereinige dabei die Daten so weit "
            "wie nötig (Typkonvertierungen, fehlende Werte sinnvoll behandeln). "
            "Aggregiere anschließend pro Land (`country_code`, ISO-2) und "
            "Produktkategorie (`category`) den Gesamtumsatz "
            "(`total_revenue_eur = sum(quantity * unit_price_eur)`) und die "
            "Anzahl Bestellungen (`order_count`). Sortiere absteigend nach "
            "Gesamtumsatz. Schreibe das Ergebnis als Parquet-Datei."
        ),
        input_files=["orders_raw.csv", "customers_raw.csv", "products_raw.csv"],
        expected_output="transform_hard_join_and_aggregate.parquet",
        evaluation_focus=["accuracy", "completeness", "consistency", "efficiency"],
        target_schema=(
            "country_code: string (2-letter ISO code), category: string, "
            "total_revenue_eur: float (rounded to 2 decimals), order_count: int "
            "(one row per country/category combination, sorted descending by total_revenue_eur)"
        ),
        notes="Königsdisziplin: 3-Tabellen-Join + Bereinigung + Aggregation.",
    ),
]


ALL_TASKS: list[Task] = [
    *CLEANING_TASKS,
    *DEDUPLICATION_TASKS,
    *TRANSFORMATION_TASKS,
]


def get_task(task_id: str) -> Task:
    """Returns a task by its ID."""
    for task in ALL_TASKS:
        if task.id == task_id:
            return task
    raise KeyError(f"Unbekannte Task-ID: {task_id}")
