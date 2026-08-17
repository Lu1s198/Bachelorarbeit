import pandas as pd
import re
from difflib import SequenceMatcher

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/anthropic_v2_few_shot_r2/output.parquet"

df = pd.read_parquet(input_path)

# Step 1: remove exact duplicates
df = df.drop_duplicates(keep="first").reset_index(drop=True)

# Step 2: remove rows with duplicate email, keep newest registered_at
df["registered_at"] = pd.to_datetime(df["registered_at"])
df = df.sort_values("registered_at", ascending=False)
df = df.drop_duplicates(subset="email", keep="first")
df = df.reset_index(drop=True)

# Step 3: fuzzy duplicate detection

TITLES = [
    "mr", "mrs", "ms", "miss", "dr", "prof", "herr", "frau",
    "mag", "ing", "sir", "madam"
]
title_pattern = re.compile(
    r"^(?:" + "|".join(TITLES) + r")\.?\s+", flags=re.IGNORECASE
)
middle_initial_pattern = re.compile(r"\b[a-zA-Z]\.\s*")
whitespace_pattern = re.compile(r"\s+")


def normalize_name(name):
    if pd.isna(name):
        return ""
    n = str(name).strip().lower()
    n = title_pattern.sub("", n)
    n = middle_initial_pattern.sub("", n)
    n = whitespace_pattern.sub(" ", n)
    n = n.strip()
    return n


def normalize_email(email):
    if pd.isna(email):
        return ""
    e = str(email).strip().lower()
    if "@" in e:
        local, domain = e.split("@", 1)
        local = local.replace(".", "")
        e = local + "@" + domain
    return e


df["name_norm"] = df["full_name"].apply(normalize_name)
df["email_norm"] = df["email"].apply(normalize_email)

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


def name_similar(a, b):
    if not a or not b:
        return False
    if a == b:
        return True
    ratio = SequenceMatcher(None, a, b).ratio()
    return ratio >= 0.85


# Group by email_norm; within each group, connect rows whose names are similar
email_groups = df.groupby("email_norm").groups

for email_key, idxs in email_groups.items():
    idxs = list(idxs)
    if len(idxs) < 2:
        continue
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            a_idx, b_idx = idxs[i], idxs[j]
            name_a = df.loc[a_idx, "name_norm"]
            name_b = df.loc[b_idx, "name_norm"]
            if email_key != "" and name_similar(name_a, name_b):
                union(a_idx, b_idx)

df["cluster"] = [find(i) for i in range(n)]

df = df.sort_values("customer_id", ascending=True)
df = df.drop_duplicates(subset="cluster", keep="first")

df = df.drop(columns=["name_norm", "email_norm", "cluster"])
df["registered_at"] = df["registered_at"].dt.strftime("%Y-%m-%d")

df = df.sort_values("customer_id").reset_index(drop=True)

df.to_parquet(output_path, index=False)