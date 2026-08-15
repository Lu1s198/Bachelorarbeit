import os
import re
import unicodedata
from difflib import SequenceMatcher

import numpy as np
import pandas as pd


input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai_isolated/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

required_columns = ["customer_id", "full_name", "email", "country", "registered_at"]
for column in required_columns:
    if column not in df.columns:
        df[column] = pd.NA

df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")
df["full_name"] = df["full_name"].astype("string")
df["email"] = df["email"].astype("string")

title_tokens = {
    "mr", "mrs", "ms", "miss", "mx", "dr", "prof", "professor",
    "sir", "madam", "lady", "lord", "rev", "reverend", "fr",
    "frau", "herr", "hr", "frl", "doktor", "drs", "ing",
    "dipl", "mag", "mba", "phd", "md", "dds", "jr", "sr"
}


def ascii_fold(value):
    value = "" if value is None or pd.isna(value) else str(value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.casefold()


def normalize_email(value):
    if value is None or pd.isna(value):
        return ""
    value = str(value).strip().casefold().replace(" ", "")
    if value.count("@") != 1:
        return ""
    local, domain = value.split("@", 1)
    if not local or not domain:
        return ""
    local = local.replace(".", "")
    return f"{local}@{domain}"


def name_components(value):
    text = ascii_fold(value)
    tokens = re.findall(r"[a-z0-9]+", text)
    while tokens and tokens[0] in title_tokens:
        tokens.pop(0)
    while tokens and tokens[-1] in {"jr", "sr"}:
        tokens.pop()
    if not tokens:
        return (), "", "", ""
    meaningful = tuple(token for token in tokens if len(token) > 1)
    if not meaningful:
        meaningful = tuple(tokens)
    first = meaningful[0] if meaningful else ""
    last = meaningful[-1] if len(meaningful) > 1 else ""
    compact = "".join(meaningful)
    return meaningful, first, last, compact


def similarity(a, b):
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def close_token(a, b):
    if not a or not b:
        return False
    if a == b:
        return True
    ratio = similarity(a, b)
    shortest = min(len(a), len(b))
    if shortest <= 3:
        return ratio >= 0.66
    if shortest <= 5:
        return ratio >= 0.75
    return ratio >= 0.80


def names_match(left, right):
    tokens_a, first_a, last_a, compact_a = left
    tokens_b, first_b, last_b, compact_b = right

    if not compact_a or not compact_b:
        return False

    if compact_a == compact_b:
        return True

    if len(tokens_a) == 1 or len(tokens_b) == 1:
        only_a = compact_a
        only_b = compact_b
        return similarity(only_a, only_b) >= 0.86

    first_equal = first_a == first_b
    last_equal = last_a == last_b
    first_close = close_token(first_a, first_b)
    last_close = close_token(last_a, last_b)

    if first_equal and last_close:
        return True
    if last_equal and first_close:
        return True
    if first_close and last_close:
        return True

    return similarity(compact_a, compact_b) >= 0.88


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


emails = [normalize_email(value) for value in df["email"].tolist()]
names = [name_components(value) for value in df["full_name"].tolist()]

email_groups = {}
for idx, email in enumerate(emails):
    if email:
        email_groups.setdefault(email, []).append(idx)

for indices in email_groups.values():
    group_size = len(indices)
    if group_size < 2:
        continue

    for pos in range(group_size):
        left_idx = indices[pos]
        for other_pos in range(pos + 1, group_size):
            right_idx = indices[other_pos]
            if names_match(names[left_idx], names[right_idx]):
                union(left_idx, right_idx)

components = {}
for idx in range(n):
    root = find(idx)
    components.setdefault(root, []).append(idx)

keep_indices = []
customer_ids = df["customer_id"].tolist()

for members in components.values():
    valid_members = [
        idx for idx in members
        if customer_ids[idx] is not pd.NA and not pd.isna(customer_ids[idx])
    ]
    if valid_members:
        chosen = min(valid_members, key=lambda idx: (int(customer_ids[idx]), idx))
    else:
        chosen = min(members)
    keep_indices.append(chosen)

keep_indices.sort()
result = df.iloc[keep_indices].copy()

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)