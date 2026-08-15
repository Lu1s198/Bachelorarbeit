import pandas as pd
import numpy as np
import re
import difflib

INPUT_PATH = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
OUTPUT_PATH = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r4/dedup_hard/output.parquet"

df = pd.read_parquet(INPUT_PATH)

df["customer_id"] = df["customer_id"].astype(int)
df["full_name"] = df["full_name"].astype(str)
df["email"] = df["email"].astype(str)
df["country"] = df["country"].astype(str)
df["registered_at"] = df["registered_at"].astype(str)

TITLES = {
    "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "miss", "miss.",
    "dr", "dr.", "prof", "prof.", "professor",
    "herr", "frau", "frl", "frl.",
    "mx", "mx.", "sir", "madam", "madame", "mme", "mme.",
    "monsieur", "senor", "senora", "señor", "señora",
}

def normalize_name(name: str) -> str:
    if name is None:
        return ""
    n = name.strip().lower()
    n = re.sub(r"[^a-zäöüßàâçéèêëîïôûùüÿñæœ\s\-']", " ", n)
    tokens = n.split()
    tokens = [t.strip(".") for t in tokens if t.strip(".") not in TITLES]
    tokens = [t for t in tokens if len(t) > 1]
    tokens = [t.rstrip(".") for t in tokens]
    return " ".join(tokens)

def normalize_email(email: str) -> str:
    if email is None:
        return ""
    e = email.strip().lower()
    if "@" in e:
        local, domain = e.split("@", 1)
        local = local.replace(".", "")
        return f"{local}@{domain}"
    return e

df["_norm_name"] = df["full_name"].apply(normalize_name)
df["_norm_email"] = df["email"].apply(normalize_email)

n = len(df)
parent = list(range(n))

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[max(ra, rb)] = min(ra, rb)

names = df["_norm_name"].tolist()
emails = df["_norm_email"].tolist()

def name_similar(a, b):
    if a == b:
        return True
    if not a or not b:
        return False
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    return ratio >= 0.85

def email_similar(a, b):
    if a == b:
        return True
    if not a or not b:
        return False
    a_local, _, a_dom = a.partition("@")
    b_local, _, b_dom = b.partition("@")
    if a_dom != b_dom:
        return False
    ratio = difflib.SequenceMatcher(None, a_local, b_local).ratio()
    return ratio >= 0.85

for i in range(n):
    for j in range(i + 1, n):
        if name_similar(names[i], names[j]) and email_similar(emails[i], emails[j]):
            union(i, j)

df["_cluster"] = [find(i) for i in range(n)]

df_sorted = df.sort_values("customer_id")
idx_keep = df_sorted.groupby("_cluster")["customer_id"].idxmin()

result = df.loc[idx_keep].copy()
result = result[["customer_id", "full_name", "email", "country", "registered_at"]]
result = result.sort_values("customer_id").reset_index(drop=True)

result.to_parquet(OUTPUT_PATH, index=False)