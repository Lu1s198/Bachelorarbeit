import os
import re
import unicodedata
from difflib import SequenceMatcher

import pandas as pd

# Schritt 0: Eingabe laden und die ursprüngliche Reihenfolge speichern,
# damit bei exakten Duplikaten und Gleichständen deterministisch das erste
# Vorkommen erhalten bleibt.
input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/openai_v3_chain_of_thought/output.parquet"

df = pd.read_parquet(input_path).copy()
df["_original_order"] = range(len(df))

# Schritt 1: Exakte Duplikate über alle ursprünglichen Spalten entfernen.
# keep="first" bewahrt dabei das erste Auftreten in der Quelldatei.
original_columns = [col for col in df.columns if col != "_original_order"]
df = df.drop_duplicates(subset=original_columns, keep="first").copy()

# Schritt 2: Bei exakt gleicher E-Mail-Adresse die jüngste Registrierung behalten.
# Ein stabiler Sortieralgorithmus stellt sicher, dass bei gleichem Datum das
# zuerst vorkommende Element aus Schritt 1 bestehen bleibt.
df["_registered_at_dt"] = pd.to_datetime(df["registered_at"], errors="coerce")
df = df.sort_values(
    by=["email", "_registered_at_dt", "_original_order"],
    ascending=[True, False, True],
    kind="mergesort",
)
df = df.drop_duplicates(subset=["email"], keep="first").copy()

# Schritt 3a: Hilfsfunktionen zur Normalisierung von Namen und E-Mails definieren.
# Anreden und Titel werden entfernt, einzelne Mittelinitialen ignoriert und
# Schreibweise, Akzente sowie Satzzeichen vereinheitlicht.
title_pattern = re.compile(
    r"\b(?:herr|frau|mr|mrs|ms|miss|dr|prof|professor|doktor|sir|madam|mme|mx)\.?\b",
    flags=re.IGNORECASE,
)

def normalize_name(value):
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value)).casefold()
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = title_pattern.sub(" ", text)
    tokens = re.findall(r"[a-z0-9]+", text)
    # Einzelne Buchstaben gelten als Mittelinitialen und werden nicht für den
    # Personenabgleich verwendet.
    tokens = [token for token in tokens if len(token) > 1]
    return " ".join(tokens)

def normalize_email(value):
    if pd.isna(value):
        return ""
    email = str(value).strip().casefold()
    if "@" not in email:
        return email
    local_part, domain = email.rsplit("@", 1)
    # Punkte im lokalen Teil und Groß-/Kleinschreibung sind laut Aufgabe
    # reine Schreibvarianten.
    local_part = local_part.replace(".", "")
    return f"{local_part}@{domain}"

def names_indicate_same_person(name_a, name_b):
    # Leere Namen liefern keinen ausreichenden Personenhinweis.
    if not name_a or not name_b:
        return False

    if name_a == name_b:
        return True

    tokens_a = name_a.split()
    tokens_b = name_b.split()

    # Vor- und Nachname müssen bei mehrteiligen Namen konsistent bleiben.
    if len(tokens_a) >= 2 and len(tokens_b) >= 2:
        first_similarity = SequenceMatcher(None, tokens_a[0], tokens_b[0]).ratio()
        last_similarity = SequenceMatcher(None, tokens_a[-1], tokens_b[-1]).ratio()
        return first_similarity >= 0.80 and last_similarity >= 0.80

    # Für einteilige Namen wird ein strengerer globaler Ähnlichkeitsschwellenwert
    # verwendet, um zufällige Treffer zu vermeiden.
    return SequenceMatcher(None, name_a, name_b).ratio() >= 0.90

df["_normalized_name"] = df["full_name"].map(normalize_name)
df["_normalized_email"] = df["email"].map(normalize_email)

# Schritt 3b: Kandidaten nur innerhalb derselben normalisierten E-Mail bilden.
# Dadurch müssen sowohl Name als auch E-Mail auf dieselbe reale Person hindeuten.
# Union-Find fasst transitive unscharfe Duplikatgruppen korrekt zusammen.
parent = list(range(len(df)))
rank = [0] * len(df)

def find(index):
    while parent[index] != index:
        parent[index] = parent[parent[index]]
        index = parent[index]
    return index

def union(left, right):
    root_left = find(left)
    root_right = find(right)
    if root_left == root_right:
        return
    if rank[root_left] < rank[root_right]:
        parent[root_left] = root_right
    elif rank[root_left] > rank[root_right]:
        parent[root_right] = root_left
    else:
        parent[root_right] = root_left
        rank[root_left] += 1

df = df.reset_index(drop=True)

for _, group in df.groupby("_normalized_email", dropna=False, sort=False):
    indices = group.index.tolist()
    for position, left_index in enumerate(indices):
        for right_index in indices[position + 1:]:
            if names_indicate_same_person(
                df.at[left_index, "_normalized_name"],
                df.at[right_index, "_normalized_name"],
            ):
                union(left_index, right_index)

# Schritt 3c: Pro erkannter Duplikatgruppe die Zeile mit der kleinsten customer_id behalten.
df["_fuzzy_group"] = [find(index) for index in range(len(df))]
df = df.sort_values(
    by=["_fuzzy_group", "customer_id", "_original_order"],
    ascending=[True, True, True],
    kind="mergesort",
)
df = df.drop_duplicates(subset=["_fuzzy_group"], keep="first").copy()

# Schritt 4: Hilfsspalten entfernen, Ergebnis in die verlangte Ausgabedatei schreiben.
df = df.drop(
    columns=[
        "_original_order",
        "_registered_at_dt",
        "_normalized_name",
        "_normalized_email",
        "_fuzzy_group",
    ]
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)