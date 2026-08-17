import pandas as pd
import re
import os
from difflib import SequenceMatcher

# -----------------------------
# Load input data
# -----------------------------
input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/anthropic_v1_zero_shot_r2/output.parquet"

df = pd.read_parquet(input_path)

# Ensure expected dtypes
df["customer_id"] = df["customer_id"].astype("int64")
df["full_name"] = df["full_name"].astype(str)
df["email"] = df["email"].astype(str)
df["country"] = df["country"].astype(str)
df["registered_at"] = df["registered_at"].astype(str)

# -----------------------------
# Step 1: Remove exact duplicates (all columns identical), keep first
# -----------------------------
df = df.drop_duplicates(keep="first").reset_index(drop=True)

# -----------------------------
# Step 2: Remove rows with duplicate email, keep the one with the
# most recent registered_at (ISO format YYYY-MM-DD -> lexicographic sort works)
# -----------------------------
df = df.sort_values(by=["email", "registered_at"], ascending=[True, False])
df = df.drop_duplicates(subset=["email"], keep="first")
df = df.reset_index(drop=True)

# -----------------------------
# Step 3: Fuzzy duplicate detection
# -----------------------------

TITLES = {
    "mr", "mrs", "ms", "miss", "mx", "dr", "prof", "professor",
    "herr", "frau", "sir", "madam", "dame"
}


def normalize_email(email: str) -> str:
    email = email.strip().lower()
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    local = local.replace(".", "")
    return f"{local}@{domain}"


def normalize_name(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z\s]", " ", s)
    tokens = [t for t in s.split() if t]
    # remove titles/salutations
    tokens = [t for t in tokens if t not in TITLES]
    # remove middle initials (single-letter tokens)
    tokens = [t for t in tokens if len(t) > 1]
    return " ".join(tokens)


def name_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


df["_norm_email"] = df["email"].apply(normalize_email)
df["_norm_name"] = df["full_name"].apply(normalize_name)

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


# Group indices by normalized email to find candidate fuzzy duplicates
groups = {}
for idx, ne in enumerate(df["_norm_email"]):
    groups.setdefault(ne, []).append(idx)

NAME_SIM_THRESHOLD = 0.80

for ne, idxs in groups.items():
    if len(idxs) < 2:
        continue
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            a_idx, b_idx = idxs[i], idxs[j]
            name_a = df.at[a_idx, "_norm_name"]
            name_b = df.at[b_idx, "_norm_name"]
            if name_a == name_b or name_similarity(name_a, name_b) >= NAME_SIM_THRESHOLD:
                union(a_idx, b_idx)

# Assign component ids
components = {}
for idx in range(n):
    root = find(idx)
    components.setdefault(root, []).append(idx)

keep_indices = []
for root, idxs in components.items():
    # keep the row with the smallest customer_id
    best_idx = min(idxs, key=lambda i: df.at[i, "customer_id"])
    keep_indices.append(best_idx)

df_result = df.loc[sorted(keep_indices)].copy()
df_result = df_result.drop(columns=["_norm_email", "_norm_name"])
df_result = df_result.reset_index(drop=True)

# -----------------------------
# Write output
# -----------------------------
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_result.to_parquet(output_path, index=False)