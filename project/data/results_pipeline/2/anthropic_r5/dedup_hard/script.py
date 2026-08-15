import pandas as pd
import numpy as np
import re
from difflib import SequenceMatcher

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r5/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r5/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df["customer_id"] = df["customer_id"].astype("int64")
df["full_name"] = df["full_name"].astype(str)
df["email"] = df["email"].astype(str)
df["country"] = df["country"].astype(str)
df["registered_at"] = df["registered_at"].astype(str)

TITLES = [
    "dr", "prof", "mr", "mrs", "ms", "miss", "herr", "frau", "mag",
    "ing", "dipl", "sir", "madam", "dr.", "prof.", "mr.", "mrs.", "ms."
]

def normalize_name(name):
    if not isinstance(name, str):
        return ""
    n = name.strip().lower()
    n = re.sub(r"[.,]", " ", n)
    tokens = n.split()
    filtered = []
    for t in tokens:
        t_clean = t.strip()
        if t_clean in TITLES:
            continue
        if len(t_clean) == 1:
            continue
        filtered.append(t_clean)
    n = " ".join(filtered)
    n = re.sub(r"[^a-z\s]", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n

def normalize_email(email):
    if not isinstance(email, str):
        return ""
    e = email.strip().lower()
    if "@" in e:
        local, domain = e.split("@", 1)
        local = local.replace(".", "")
        e = local + "@" + domain
    return e

df["norm_name"] = df["full_name"].apply(normalize_name)
df["norm_email"] = df["email"].apply(normalize_email)

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
        parent[max(rx, ry)] = min(rx, ry)

groups = {}
for idx, email in enumerate(df["norm_email"]):
    groups.setdefault(email, []).append(idx)

for email, idx_list in groups.items():
    if len(idx_list) < 2:
        continue
    for i in range(len(idx_list)):
        for j in range(i + 1, len(idx_list)):
            a, b = idx_list[i], idx_list[j]
            name_a = df.at[a, "norm_name"]
            name_b = df.at[b, "norm_name"]
            if name_a == "" or name_b == "":
                ratio = 0.0
            else:
                ratio = SequenceMatcher(None, name_a, name_b).ratio()
            if ratio >= 0.82:
                union(a, b)

df["cluster"] = [find(i) for i in range(n)]

df_sorted = df.sort_values("customer_id")
result = df_sorted.groupby("cluster", as_index=False).first()

result = result[["customer_id", "full_name", "email", "country", "registered_at"]]
result = result.sort_values("customer_id").reset_index(drop=True)

result.to_parquet(output_path, index=False)