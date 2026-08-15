import pandas as pd
import numpy as np
import re
import difflib

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df["customer_id"] = df["customer_id"].astype("int64")
df["full_name"] = df["full_name"].astype(str)
df["email"] = df["email"].astype(str)
df["country"] = df["country"].astype(str)
df["registered_at"] = df["registered_at"].astype(str)

TITLES = {
    "mr", "mrs", "ms", "miss", "mx", "dr", "prof", "professor",
    "herr", "frau", "sir", "madam", "dame", "rev", "fr", "st"
}

def normalize_email(email):
    if email is None:
        return ""
    e = str(email).strip().lower()
    if "@" in e:
        local, domain = e.split("@", 1)
        local = local.replace(".", "")
        return local + "@" + domain
    return e

def normalize_name(name):
    if name is None:
        return ""
    n = str(name).strip()
    n = re.sub(r"[^\w\s\-']", " ", n)
    tokens = n.split()
    cleaned_tokens = []
    for t in tokens:
        t_clean = t.strip(".").lower()
        if t_clean in TITLES:
            continue
        cleaned_tokens.append(t_clean)
    # remove middle initials (single-letter tokens that are not first or last)
    if len(cleaned_tokens) >= 3:
        filtered = []
        for i, t in enumerate(cleaned_tokens):
            if 0 < i < len(cleaned_tokens) - 1 and len(t) == 1:
                continue
            filtered.append(t)
        cleaned_tokens = filtered
    return " ".join(cleaned_tokens)

df["_norm_email"] = df["email"].apply(normalize_email)
df["_norm_name"] = df["full_name"].apply(normalize_name)

def name_similarity(a, b):
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()

parent = {}

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry:
        parent[rx] = ry

for idx in df.index:
    parent[idx] = idx

for email_key, group in df.groupby("_norm_email"):
    idx_list = list(group.index)
    n = len(idx_list)
    for i in range(n):
        for j in range(i + 1, n):
            idx_i = idx_list[i]
            idx_j = idx_list[j]
            name_i = df.at[idx_i, "_norm_name"]
            name_j = df.at[idx_j, "_norm_name"]
            sim = name_similarity(name_i, name_j)
            if sim >= 0.82:
                union(idx_i, idx_j)

df["_cluster"] = [find(idx) for idx in df.index]

min_ids = df.groupby("_cluster")["customer_id"].transform("min")
df["_is_min"] = df["customer_id"] == min_ids

result = df[df["_is_min"]].copy()
result = result.drop_duplicates(subset=["_cluster"], keep="first")

result = result[["customer_id", "full_name", "email", "country", "registered_at"]]
result = result.sort_values("customer_id").reset_index(drop=True)

result.to_parquet(output_path, index=False)