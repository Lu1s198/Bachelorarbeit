import os
import re
import unicodedata
from difflib import SequenceMatcher

import pandas as pd

# Schritt 0: Pfade definieren und Eingabedaten laden.
input_path = (
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/"
    r"results_pipeline/2/_reference/cleaning_hard/output.parquet"
)
output_path = (
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/"
    r"results_group/2/dedup/openai_v3_chain_of_thought_r2/output.parquet"
)

df = pd.read_parquet(input_path)

# Schritt 1: Exakte Duplikate über alle vorhandenen Spalten entfernen.
# drop_duplicates behält standardmäßig das erste Vorkommen.
df = df.drop_duplicates(keep="first").copy()

# Schritt 2: Bei identischen E-Mail-Werten nur den jüngsten registered_at-Wert behalten.
# Bei gleichem Datum sorgt der stabile MergeSort dafür, dass das zuerst vorhandene
# Vorkommen erhalten bleibt.
df["_original_order"] = range(len(df))
df["_registered_at_sort"] = pd.to_datetime(df["registered_at"], errors="coerce")

df = (
    df.sort_values(
        by=["email", "_registered_at_sort", "_original_order"],
        ascending=[True, False, True],
        kind="mergesort",
        na_position="last",
    )
    .drop_duplicates(subset=["email"], keep="first")
    .sort_values("_original_order", kind="mergesort")
    .reset_index(drop=True)
)

# Schritt 3a: Hilfsfunktionen zur Normalisierung von Namen und E-Mails definieren.
# Anreden und Titel werden entfernt, Mittelinitialen ignoriert und Groß-/Kleinschreibung,
# Akzente sowie Satzzeichen vereinheitlicht.
titles = {
    "dr", "prof", "professor", "mr", "mrs", "ms", "miss", "mx",
    "herr", "frau", "fr", "hr", "sir", "madam", "madame",
    "dipl", "ing", "mba", "phd", "md",
}

def normalize_text(value):
    if pd.isna(value):
        return ""
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(char for char in value if not unicodedata.combining(char))
    return value.lower().strip()

def normalize_name(value):
    text = normalize_text(value)
    tokens = re.findall(r"[a-z0-9]+", text)

    # Titel und einzelne Mittelinitialen sind kein Bestandteil des Vergleichsnamens.
    tokens = [
        token
        for token in tokens
        if token not in titles and not (len(token) == 1 and token.isalpha())
    ]
    return " ".join(tokens)

def normalize_email(value):
    if pd.isna(value):
        return ""
    email = normalize_text(value).replace(" ", "")
    if "@" not in email:
        return email

    local_part, domain = email.rsplit("@", 1)

    # Punkte im lokalen Teil und abweichende Groß-/Kleinschreibung sind laut Aufgabe
    # lediglich Schreibvarianten derselben E-Mail-Adresse.
    local_part = local_part.replace(".", "")
    return f"{local_part}@{domain}"

def names_indicate_same_person(name_a, name_b):
    # Leere Namen liefern keine ausreichende Namensbestätigung.
    if not name_a or not name_b:
        return False

    # Exakte Übereinstimmung oder gleiche Namensbestandteile in anderer Reihenfolge.
    if name_a == name_b:
        return True

    tokens_a = name_a.split()
    tokens_b = name_b.split()

    if sorted(tokens_a) == sorted(tokens_b):
        return True

    # Tippfehler werden über eine strenge Ähnlichkeitsschwelle erkannt.
    # Für kurze Namen ist die Schwelle höher, um Zufallstreffer zu vermeiden.
    similarity = SequenceMatcher(None, name_a, name_b).ratio()
    minimum_similarity = 0.90 if min(len(name_a), len(name_b)) < 8 else 0.84

    if similarity >= minimum_similarity:
        return True

    # Zusätzlich werden Vor- und Nachname tokenweise verglichen, damit z. B.
    # ein einzelner Tippfehler in einem längeren Namen erkannt wird.
    if len(tokens_a) >= 2 and len(tokens_b) >= 2:
        first_similarity = SequenceMatcher(None, tokens_a[0], tokens_b[0]).ratio()
        last_similarity = SequenceMatcher(None, tokens_a[-1], tokens_b[-1]).ratio()

        if first_similarity >= 0.80 and last_similarity >= 0.80:
            return True

    return False

# Schritt 3b: Vergleichsschlüssel erzeugen.
df["_normalized_name"] = df["full_name"].map(normalize_name)
df["_normalized_email"] = df["email"].map(normalize_email)

# Schritt 3c: Unscharfe Dubletten innerhalb derselben normalisierten E-Mail erkennen.
# Eine Zusammenführung erfolgt nur, wenn sowohl die E-Mail als auch der Name
# auf dieselbe Person hindeuten.
parent = list(range(len(df)))

def find(index):
    while parent[index] != index:
        parent[index] = parent[parent[index]]
        index = parent[index]
    return index

def union(left, right):
    root_left = find(left)
    root_right = find(right)
    if root_left != root_right:
        parent[root_right] = root_left

for _, group in df.groupby("_normalized_email", dropna=False, sort=False):
    indices = group.index.tolist()

    # Ungültige bzw. leere E-Mail-Werte dienen nicht als unscharfer Match-Schlüssel.
    if not indices or not str(group["_normalized_email"].iloc[0]).strip():
        continue

    for position, left_index in enumerate(indices):
        for right_index in indices[position + 1:]:
            left_name = df.at[left_index, "_normalized_name"]
            right_name = df.at[right_index, "_normalized_name"]

            if names_indicate_same_person(left_name, right_name):
                union(left_index, right_index)

# Schritt 3d: Pro zusammenhängender Dublettengruppe die kleinste customer_id behalten.
df["_duplicate_group"] = [find(index) for index in range(len(df))]

df = (
    df.sort_values(
        by=["_duplicate_group", "customer_id", "_original_order"],
        ascending=[True, True, True],
        kind="mergesort",
    )
    .drop_duplicates(subset=["_duplicate_group"], keep="first")
    .sort_values("_original_order", kind="mergesort")
    .drop(
        columns=[
            "_original_order",
            "_registered_at_sort",
            "_normalized_name",
            "_normalized_email",
            "_duplicate_group",
        ]
    )
    .reset_index(drop=True)
)

# Schritt 4: Ergebnisverzeichnis anlegen und das Endergebnis als Parquet schreiben.
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)