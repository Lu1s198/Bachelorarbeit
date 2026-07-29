"""Referenz-Musterlösung für das Few-Shot-Beispiel (prompts/v2_few_shot.yaml).

Dieses Skript ist bewusst KEINE der neun evaluierten ETL-Aufgaben, sondern eine
eigenständige, andersartige Beispielaufgabe (Mitarbeitertabelle). Es dient
ausschließlich dazu, dem Modell im Few-Shot-Prompt den erwarteten Lösungsstil zu
demonstrieren, ohne die Lösung einer der Bewertungsaufgaben vorwegzunehmen.

Ausführbar zur Kontrolle:  python employees_clean.py
Erzeugt neben diesem Skript die Datei employees_clean.parquet.
"""

import pandas as pd

# Rohdaten einlesen
df = pd.read_csv("employees_raw.csv")

# 1. Führende/nachfolgende Leerzeichen in allen Textspalten entfernen
for column in ["full_name", "department"]:
    df[column] = df[column].str.strip()

# 2. Fehlende Abteilungen einheitlich als 'UNKNOWN' kennzeichnen
df["department"] = df["department"].fillna("UNKNOWN").replace("", "UNKNOWN")

# 3. Gehalt aus Text (z. B. "€60000", "52000 EUR") in einen Float überführen
df["annual_salary_eur"] = (
    df["annual_salary_eur"]
    .astype(str)
    .str.replace("€", "", regex=False)
    .str.replace("EUR", "", regex=False)
    .str.strip()
    .astype(float)
)

# 4. Textuelle Wahrheitswerte ('ja'/'nein') in Boolean umwandeln
df["active"] = df["active"].str.strip().eq("ja")

# 5. Ergebnis als Parquet schreiben
df.to_parquet("employees_clean.parquet", index=False)
