import os
import re
import unicodedata
from collections import defaultdict
from functools import lru_cache

import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

required_columns = ["customer_id", "full_name", "email", "country", "registered_at"]
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

df = df.reset_index(drop=True)
n = len(df)

title_tokens = {
    "herr", "frau", "mr", "mrs", "ms", "miss", "mx",
    "dr", "prof", "professor", "doktor", "doctor",
    "sir", "dame", "lord", "lady", "rev", "reverend",
    "fr", "sr", "br", "schwester", "bruder",
    "ing", "dipl", "mba", "msc", "bsc", "ma", "ba",
    "phd", "md", "dds", "dvm", "jd", "esq"
}

suffix_tokens = {
    "jr", "junior", "sr", "senior", "ii", "iii", "iv", "v",
    "phd", "md", "dds", "dvm", "esq", "mba", "msc", "bsc"
}

def ascii_fold(value):
    value = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in value if not unicodedata.combining(ch))

def normalize_email(value):
    if pd.isna(value):
        return ""
    value = str(value).strip().casefold()
    if not value or "@" not in value:
        return ""
    local, domain = value.rsplit("@", 1)
    local = re.sub(r"\s+", "", local)
    domain = re.sub(r"\s+", "", domain)
    if not local or not domain:
        return ""
    local = local.replace(".", "")
    return f"{local}@{domain}"

def normalize_name(value):
    if pd.isna(value):
        return ()
    value = ascii_fold(str(value)).casefold().strip()
    if not value:
        return ()
    value = re.sub(r"['`´’\-]", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    tokens = [token for token in value.split() if token]
    while tokens and tokens[0] in title_tokens:
        tokens.pop(0)
    while tokens and tokens[-1] in suffix_tokens:
        tokens.pop()
    tokens = [token for token in tokens if token not in title_tokens]
    tokens = [token for token in tokens if len(token) > 1 or token.isdigit()]
    return tuple(tokens)

@lru_cache(maxsize=250000)
def levenshtein_distance(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            cost = 0 if char_a == char_b else 1
            current.append(min(
                current[-1] + 1,
                previous[j] + 1,
                previous[j - 1] + cost
            ))
        previous = current
    return previous[-1]

def token_close(a, b):
    if a == b:
        return True
    if not a or not b:
        return False
    max_len = max(len(a), len(b))
    min_len = min(len(a), len(b))
    distance = levenshtein_distance(a, b)
    if max_len <= 2:
        return False
    if max_len <= 4:
        return distance <= 1 and min_len >= 3
    return distance <= max(1, int(max_len * 0.20))

def names_compatible(tokens_a, tokens_b):
    if not tokens_a or not tokens_b:
        return False

    if tokens_a == tokens_b:
        return True

    compact_a = "".join(tokens_a)
    compact_b = "".join(tokens_b)
    if compact_a == compact_b:
        return True

    if len(tokens_a) == len(tokens_b) and sorted(tokens_a) == sorted(tokens_b):
        return True

    if len(tokens_a) == 1 or len(tokens_b) == 1:
        if len(tokens_a) == 1 and len(tokens_b) == 1:
            return token_close(tokens_a[0], tokens_b[0])
        return False

    first_a, last_a = tokens_a[0], tokens_a[-1]
    first_b, last_b = tokens_b[0], tokens_b[-1]

    direct_match = token_close(first_a, first_b) and token_close(last_a, last_b)
    reversed_match = token_close(first_a, last_b) and token_close(last_a, first_b)

    if direct_match or reversed_match:
        return True

    if len(compact_a) >= 6 and len(compact_b) >= 6:
        distance = levenshtein_distance(compact_a, compact_b)
        allowed = max(1, int(max(len(compact_a), len(compact_b)) * 0.16))
        return distance <= allowed

    return False

parent = list(range(n))
rank = [0] * n

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

email_values = df["email"].tolist()
name_values = df["full_name"].tolist()

normalized_emails = [normalize_email(value) for value in email_values]
normalized_names = [normalize_name(value) for value in name_values]

email_groups = defaultdict(list)
for idx, email in enumerate(normalized_emails):
    if email and normalized_names[idx]:
        email_groups[email].append(idx)

for indices in email_groups.values():
    if len(indices) < 2:
        continue

    exact_name_groups = defaultdict(list)
    for idx in indices:
        exact_name_groups[normalized_names[idx]].append(idx)

    for same_name_indices in exact_name_groups.values():
        if len(same_name_indices) > 1:
            anchor = same_name_indices[0]
            for idx in same_name_indices[1:]:
                union(anchor, idx)

    for pos_a in range(len(indices)):
        idx_a = indices[pos_a]
        name_a = normalized_names[idx_a]
        for pos_b in range(pos_a + 1, len(indices)):
            idx_b = indices[pos_b]
            if find(idx_a) == find(idx_b):
                continue
            if names_compatible(name_a, normalized_names[idx_b]):
                union(idx_a, idx_b)

def customer_id_key(value, position):
    if pd.isna(value):
        return (2, "", position)
    try:
        numeric_value = float(value)
        if np.isfinite(numeric_value):
            return (0, numeric_value, position)
    except (TypeError, ValueError):
        pass
    return (1, str(value), position)

components = defaultdict(list)
customer_ids = df["customer_id"].tolist()

for idx in range(n):
    components[find(idx)].append(idx)

keep_indices = []
for component_indices in components.values():
    keep_indices.append(min(
        component_indices,
        key=lambda idx: customer_id_key(customer_ids[idx], idx)
    ))

keep_indices.sort(key=lambda idx: customer_id_key(customer_ids[idx], idx))
result = df.iloc[keep_indices].copy()

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)