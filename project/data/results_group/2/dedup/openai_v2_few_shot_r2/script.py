import os
import re
import unicodedata
from difflib import SequenceMatcher

import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
synthetic_dir = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/openai_v2_few_shot_r2/output.parquet"

if not os.path.isfile(input_path):
    candidates = []
    for root, _, files in os.walk(synthetic_dir):
        for file in files:
            if file.lower().endswith(".parquet"):
                candidates.append(os.path.join(root, file))
    preferred = [path for path in candidates if os.path.basename(path).lower() == "input.parquet"]
    if preferred:
        input_path = preferred[0]
    elif candidates:
        input_path = candidates[0]
    else:
        raise FileNotFoundError("No input Parquet file found.")

df = pd.read_parquet(input_path)

df = df.drop_duplicates(keep="first").copy()
df["_original_order"] = range(len(df))

df["_registered_at_sort"] = pd.to_datetime(df["registered_at"], errors="coerce")
df = df.sort_values(
    ["email", "_registered_at_sort", "_original_order"],
    ascending=[True, False, True],
    na_position="last",
    kind="stable",
)
df = df.drop_duplicates(subset=["email"], keep="first").copy()
df = df.sort_values("_original_order", kind="stable").reset_index(drop=True)

titles = {
    "dr", "prof", "professor", "herr", "frau", "mr", "mrs", "ms",
    "miss", "sir", "madam", "mme", "mlle", "ing", "dipl", "phd",
    "md", "jr", "sr"
}

def normalize_text(value):
    value = "" if pd.isna(value) else str(value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return value.casefold()

def normalize_name(value):
    text = normalize_text(value)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [token for token in text.split() if token not in titles and len(token) > 1]
    return tokens

def normalize_email(value):
    value = "" if pd.isna(value) else str(value)
    value = value.strip().casefold()
    if "@" not in value:
        return value
    local, domain = value.rsplit("@", 1)
    return local.replace(".", "") + "@" + domain

def names_match(tokens_a, tokens_b):
    if not tokens_a or not tokens_b:
        return False

    name_a = " ".join(tokens_a)
    name_b = " ".join(tokens_b)

    if name_a == name_b:
        return True

    sorted_a = " ".join(sorted(tokens_a))
    sorted_b = " ".join(sorted(tokens_b))

    direct_ratio = SequenceMatcher(None, name_a, name_b).ratio()
    sorted_ratio = SequenceMatcher(None, sorted_a, sorted_b).ratio()

    if max(direct_ratio, sorted_ratio) >= 0.84:
        return True

    if len(tokens_a) >= 2 and len(tokens_b) >= 2:
        first_ratio = SequenceMatcher(None, tokens_a[0], tokens_b[0]).ratio()
        last_ratio = SequenceMatcher(None, tokens_a[-1], tokens_b[-1]).ratio()
        if first_ratio >= 0.75 and last_ratio >= 0.80:
            return True

    return False

df["_name_tokens"] = df["full_name"].map(normalize_name)
df["_normalized_email"] = df["email"].map(normalize_email)

parent = list(range(len(df)))

def find(index):
    while parent[index] != index:
        parent[index] = parent[parent[index]]
        index = parent[index]
    return index

def union(left, right):
    left_root = find(left)
    right_root = find(right)
    if left_root != right_root:
        parent[right_root] = left_root

for _, group in df.groupby("_normalized_email", dropna=False, sort=False):
    indices = group.index.tolist()
    for position, left_index in enumerate(indices):
        for right_index in indices[position + 1:]:
            if names_match(
                df.at[left_index, "_name_tokens"],
                df.at[right_index, "_name_tokens"],
            ):
                union(left_index, right_index)

components = {}
for index in df.index:
    root = find(index)
    components.setdefault(root, []).append(index)

keep_indices = []
for indices in components.values():
    keep_index = min(
        indices,
        key=lambda index: (df.at[index, "customer_id"], df.at[index, "_original_order"]),
    )
    keep_indices.append(keep_index)

result = (
    df.loc[keep_indices]
    .sort_values("_original_order", kind="stable")
    .drop(columns=["_original_order", "_registered_at_sort", "_name_tokens", "_normalized_email"])
    .reset_index(drop=True)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)