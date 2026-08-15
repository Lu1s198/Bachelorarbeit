import os
import re
import unicodedata
from difflib import SequenceMatcher

import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r2/dedup_hard/output.parquet"

df = pd.read_parquet(input_path).copy()

for col in ["customer_id", "full_name", "email", "country", "registered_at"]:
    if col not in df.columns:
        df[col] = pd.NA

df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")
df["_row_order"] = np.arange(len(df))


def ascii_normalize(value):
    if pd.isna(value):
        return ""
    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value


title_tokens = {
    "herr", "frau", "dr", "prof", "professor", "mr", "mrs", "ms", "miss",
    "mx", "sir", "madam", "madame", "fr", "frl", "dipl", "ing", "med",
    "phd", "mba", "bsc", "msc", "llm", "jr", "sr"
}


def name_tokens(value):
    text = ascii_normalize(value)
    tokens = re.findall(r"[a-z0-9]+", text)
    tokens = [t for t in tokens if t not in title_tokens]
    if len(tokens) >= 3:
        tokens = [t for i, t in enumerate(tokens) if not (0 < i < len(tokens) - 1 and len(t) == 1)]
    return tokens


def normalized_email(value):
    if pd.isna(value):
        return ""
    text = ascii_normalize(value)
    text = re.sub(r"\s+", "", text)
    if text.count("@") != 1:
        return ""
    local, domain = text.split("@", 1)
    local = local.replace(".", "")
    if not local or not domain:
        return ""
    return f"{local}@{domain}"


def text_similarity(a, b):
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def names_match(tokens_a, tokens_b):
    if not tokens_a or not tokens_b:
        return False

    joined_a = "".join(tokens_a)
    joined_b = "".join(tokens_b)

    if joined_a == joined_b:
        return True

    if len(tokens_a) == 1 or len(tokens_b) == 1:
        return text_similarity(joined_a, joined_b) >= 0.90

    first_similarity = text_similarity(tokens_a[0], tokens_b[0])
    last_similarity = text_similarity(tokens_a[-1], tokens_b[-1])
    full_similarity = text_similarity(" ".join(tokens_a), " ".join(tokens_b))

    if tokens_a[0] == tokens_b[0] and tokens_a[-1] == tokens_b[-1]:
        return True

    return (
        first_similarity >= 0.75
        and last_similarity >= 0.75
        and full_similarity >= 0.72
    )


df["_email_key"] = df["email"].map(normalized_email)
df["_name_tokens"] = df["full_name"].map(name_tokens)

n = len(df)
parent = np.arange(n, dtype=np.int64)
rank = np.zeros(n, dtype=np.int8)


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(a, b):
    root_a = find(a)
    root_b = find(b)
    if root_a == root_b:
        return
    if rank[root_a] < rank[root_b]:
        parent[root_a] = root_b
    elif rank[root_a] > rank[root_b]:
        parent[root_b] = root_a
    else:
        parent[root_b] = root_a
        rank[root_a] += 1


valid_email_rows = df.index[df["_email_key"].ne("")].tolist()
email_groups = df.loc[valid_email_rows].groupby("_email_key", sort=False).groups

for _, index_values in email_groups.items():
    positions = list(index_values)
    if len(positions) < 2:
        continue

    for i in range(len(positions) - 1):
        row_i = positions[i]
        tokens_i = df.at[row_i, "_name_tokens"]
        for j in range(i + 1, len(positions)):
            row_j = positions[j]
            if names_match(tokens_i, df.at[row_j, "_name_tokens"]):
                union(int(row_i), int(row_j))

roots = np.array([find(i) for i in range(n)], dtype=np.int64)
df["_cluster"] = roots

df["_customer_sort"] = df["customer_id"].fillna(np.iinfo(np.int64).max).astype("int64")
df = df.sort_values(["_cluster", "_customer_sort", "_row_order"], kind="stable")
result = df.drop_duplicates(subset=["_cluster"], keep="first")

result = result.drop(
    columns=["_row_order", "_email_key", "_name_tokens", "_cluster", "_customer_sort"],
    errors="ignore"
).sort_values("customer_id", kind="stable")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)