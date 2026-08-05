import pandas as pd
import numpy as np
import re

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

if "customer_id" in df.columns:
    try:
        df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce")
    except Exception:
        pass

TITLES = {
    "mr", "mrs", "ms", "miss", "mx", "dr", "prof", "professor", "sir",
    "madam", "herr", "frau", "fraeulein", "fräulein", "jr", "sr", "st"
}

def normalize_name(name):
    if pd.isna(name):
        return ""
    s = str(name).lower()
    s = re.sub(r"[^a-z\s]", " ", s)
    tokens = s.split()
    tokens = [t for t in tokens if t not in TITLES]
    tokens = [t for t in tokens if len(t) > 1]
    return " ".join(tokens)

def normalize_email(email):
    if pd.isna(email):
        return ""
    s = str(email).strip().lower()
    if "@" in s:
        local, domain = s.split("@", 1)
        local = local.replace(".", "")
        return local + "@" + domain
    return s

def levenshtein(a, b):
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * lb
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[lb]

name_col = "full_name" if "full_name" in df.columns else None
email_col = "email" if "email" in df.columns else None

df["_norm_name"] = df[name_col].apply(normalize_name) if name_col else ""
df["_norm_email"] = df[email_col].apply(normalize_email) if email_col else ""

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
        parent[rx] = ry

email_groups = {}
for idx, val in enumerate(df["_norm_email"]):
    if val:
        email_groups.setdefault(val, []).append(idx)
for indices in email_groups.values():
    if len(indices) > 1:
        first = indices[0]
        for other in indices[1:]:
            union(first, other)

name_groups = {}
for idx, val in enumerate(df["_norm_name"]):
    if val:
        name_groups.setdefault(val, []).append(idx)
for indices in name_groups.values():
    if len(indices) > 1:
        first = indices[0]
        for other in indices[1:]:
            union(first, other)

bucket_groups = {}
for idx, val in enumerate(df["_norm_name"]):
    if val and len(val) >= 3:
        key = (val[0], len(val) // 3)
        bucket_groups.setdefault(key, []).append(idx)

for indices in bucket_groups.values():
    m = len(indices)
    if m > 1 and m <= 500:
        for i in range(m):
            for j in range(i + 1, m):
                a_idx, b_idx = indices[i], indices[j]
                a_name = df["_norm_name"].iloc[a_idx]
                b_name = df["_norm_name"].iloc[b_idx]
                if abs(len(a_name) - len(b_name)) <= 1:
                    dist = levenshtein(a_name, b_name)
                    if dist <= 1:
                        union(a_idx, b_idx)

df["_group"] = [find(i) for i in range(n)]

if "customer_id" in df.columns:
    idx_min = df.groupby("_group")["customer_id"].idxmin()
else:
    idx_min = df.groupby("_group").apply(lambda g: g.index[0])

result = df.loc[idx_min].copy()

result = result.drop(columns=["_norm_name", "_norm_email", "_group"], errors="ignore")

if "customer_id" in result.columns:
    result = result.sort_values("customer_id").reset_index(drop=True)
else:
    result = result.reset_index(drop=True)

result.to_parquet(output_path, index=False)