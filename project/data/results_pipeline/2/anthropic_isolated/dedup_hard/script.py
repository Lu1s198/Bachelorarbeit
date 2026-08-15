import pandas as pd
import numpy as np
import re
import difflib
import os

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df["customer_id"] = df["customer_id"].astype("int64")
df["full_name"] = df["full_name"].astype(str)
df["email"] = df["email"].astype(str)
df["country"] = df["country"].astype(str)
df["registered_at"] = df["registered_at"].astype(str)

TITLES = {
    "mr", "mrs", "ms", "miss", "mx", "dr", "prof", "professor",
    "herr", "frau", "fraulein", "fräulein", "sir", "madam", "madame",
    "monsieur", "mme", "mlle", "senor", "senora", "senorita",
    "sr", "sra", "srta", "ing", "dipl", "jr", "sr."
}

def normalize_email(email):
    if not isinstance(email, str):
        return ""
    email = email.strip().lower()
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    local = local.replace(".", "")
    return f"{local}@{domain}"

def normalize_name(name):
    if not isinstance(name, str):
        return ""
    name = name.strip().lower()
    name = re.sub(r"[^\w\s]", " ", name, flags=re.UNICODE)
    tokens = name.split()
    cleaned_tokens = []
    for tok in tokens:
        tok_clean = tok.strip(".")
        if tok_clean in TITLES:
            continue
        if len(tok_clean) == 1:
            continue
        if tok_clean == "":
            continue
        cleaned_tokens.append(tok_clean)
    return " ".join(cleaned_tokens)

df["email_key"] = df["email"].apply(normalize_email)
df["name_key"] = df["full_name"].apply(normalize_name)

n = len(df)
parent = list(range(n))

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry:
        if rx < ry:
            parent[ry] = rx
        else:
            parent[rx] = ry

groups = {}
for idx, key in enumerate(df["email_key"].tolist()):
    groups.setdefault(key, []).append(idx)

SIMILARITY_THRESHOLD = 0.80

names_list = df["name_key"].tolist()

for key, idxs in groups.items():
    if len(idxs) < 2:
        continue
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            a = idxs[i]
            b = idxs[j]
            name_a = names_list[a]
            name_b = names_list[b]
            if name_a == "" and name_b == "":
                ratio = 1.0
            elif name_a == "" or name_b == "":
                ratio = 0.0
            else:
                ratio = difflib.SequenceMatcher(None, name_a, name_b).ratio()
            if ratio >= SIMILARITY_THRESHOLD:
                union(a, b)

df["_cluster"] = [find(i) for i in range(n)]

df_sorted = df.sort_values("customer_id", ascending=True)
first_rows = df_sorted.drop_duplicates(subset="_cluster", keep="first")

result = first_rows[["customer_id", "full_name", "email", "country", "registered_at"]].reset_index(drop=True)
result = result.sort_values("customer_id").reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)