import pandas as pd
import re
import os
from difflib import SequenceMatcher

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/anthropic_v2_few_shot/output.parquet"

df = pd.read_parquet(input_path)

# Step 1: remove exact duplicate rows, keep first occurrence
df = df.drop_duplicates(keep="first").reset_index(drop=True)

# Step 2: remove rows with duplicate email, keep the one with the newest registered_at
df["_registered_at_dt"] = pd.to_datetime(df["registered_at"])
df = df.sort_values("_registered_at_dt", ascending=False)
df = df.drop_duplicates(subset="email", keep="first")
df = df.drop(columns=["_registered_at_dt"]).reset_index(drop=True)

# Step 3: fuzzy dedup on name (typos, case, middle initial, titles) and email (dots, case)
TITLES = {
    "dr", "dr.", "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "miss",
    "mx", "prof", "prof.", "herr", "frau", "herrn", "frl", "frl."
}

def normalize_name(name):
    name = str(name).lower()
    name = re.sub(r"[.,]", "", name)
    tokens = name.split()
    tokens = [t for t in tokens if t not in TITLES]
    tokens = [t for t in tokens if len(t) > 1]  # drop middle initials
    return " ".join(tokens)

def normalize_email(email):
    email = str(email).strip().lower()
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    local = local.replace(".", "")
    return f"{local}@{domain}"

df["_norm_name"] = df["full_name"].apply(normalize_name)
df["_norm_email"] = df["email"].apply(normalize_email)

def name_similar(n1, n2, threshold=0.8):
    if n1 == n2:
        return True
    if not n1 or not n2:
        return False
    return SequenceMatcher(None, n1, n2).ratio() >= threshold

parent = {idx: idx for idx in df.index}

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(x, y):
    px, py = find(x), find(y)
    if px != py:
        if px < py:
            parent[py] = px
        else:
            parent[px] = py

for _, group in df.groupby("_norm_email"):
    idxs = list(group.index)
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            ni = df.loc[idxs[i], "_norm_name"]
            nj = df.loc[idxs[j], "_norm_name"]
            if name_similar(ni, nj):
                union(idxs[i], idxs[j])

df["_group"] = df.index.map(find)

result = df.loc[df.groupby("_group")["customer_id"].idxmin()]
result = result[["customer_id", "full_name", "email", "country", "registered_at"]]
result = result.sort_values("customer_id").reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)