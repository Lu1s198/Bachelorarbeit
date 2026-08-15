import os
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd

preferred_input = Path(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
)
synthetic_dir = Path(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
)
output_path = Path(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/openai_v2_few_shot/output.parquet"
)

if preferred_input.exists():
    input_path = preferred_input
else:
    preferred_synthetic_files = [
        synthetic_dir / "output.parquet",
        synthetic_dir / "input.parquet",
    ]
    input_path = next((p for p in preferred_synthetic_files if p.exists()), None)

    if input_path is None:
        parquet_files = sorted(synthetic_dir.rglob("*.parquet"))
        if not parquet_files:
            raise FileNotFoundError("No input Parquet file found.")
        input_path = parquet_files[0]

df = pd.read_parquet(input_path)

df = df.drop_duplicates(keep="first").copy()

df["_original_order"] = range(len(df))
df = df.sort_values(
    ["registered_at", "_original_order"],
    ascending=[False, True],
    kind="mergesort",
)
df = df.drop_duplicates(subset=["email"], keep="first").copy()
df = df.sort_values("_original_order", kind="mergesort").reset_index(drop=True)


def normalize_text(value):
    if pd.isna(value):
        return ""
    value = str(value).strip().lower().replace("ß", "ss")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return value


def name_tokens(value):
    text = normalize_text(value)
    tokens = re.findall(r"[a-z0-9]+", text)

    titles = {
        "dr", "prof", "professor", "herr", "frau", "mr", "mrs", "ms",
        "miss", "sir", "madam", "mme", "monsieur", "senor", "senora",
        "senorita", "dipl", "ing", "med", "phd", "mba"
    }

    tokens = [token for token in tokens if token not in titles]
    tokens = [token for token in tokens if len(token) > 1]
    return tokens


def email_key(value):
    if pd.isna(value):
        return None

    email = str(value).strip().lower()
    if not email or "@" not in email:
        return None

    local, domain = email.rsplit("@", 1)
    if not local or not domain:
        return None

    return f"{local.replace('.', '')}@{domain}"


def names_match(tokens_a, tokens_b):
    if not tokens_a or not tokens_b:
        return False

    if tokens_a == tokens_b:
        return True

    name_a = " ".join(tokens_a)
    name_b = " ".join(tokens_b)

    if SequenceMatcher(None, name_a, name_b).ratio() >= 0.84:
        return True

    if len(tokens_a) >= 2 and len(tokens_b) >= 2:
        first_similarity = SequenceMatcher(
            None, tokens_a[0], tokens_b[0]
        ).ratio()
        last_similarity = SequenceMatcher(
            None, tokens_a[-1], tokens_b[-1]
        ).ratio()

        if first_similarity >= 0.75 and last_similarity >= 0.75:
            if (first_similarity + last_similarity) / 2 >= 0.86:
                return True

    return False


tokens_by_row = [name_tokens(value) for value in df["full_name"]]
email_keys = [email_key(value) for value in df["email"]]

parent = list(range(len(df)))


def find(node):
    while parent[node] != node:
        parent[node] = parent[parent[node]]
        node = parent[node]
    return node


def union(left, right):
    left_root = find(left)
    right_root = find(right)

    if left_root != right_root:
        parent[right_root] = left_root


email_groups = {}
for row_index, key in enumerate(email_keys):
    if key is not None:
        email_groups.setdefault(key, []).append(row_index)

for indices in email_groups.values():
    if len(indices) < 2:
        continue

    for left_position in range(len(indices)):
        for right_position in range(left_position + 1, len(indices)):
            left_index = indices[left_position]
            right_index = indices[right_position]

            if names_match(tokens_by_row[left_index], tokens_by_row[right_index]):
                union(left_index, right_index)

groups = {}
for row_index in range(len(df)):
    groups.setdefault(find(row_index), []).append(row_index)

rows_to_keep = set()
for indices in groups.values():
    selected_index = min(
        indices,
        key=lambda index: (df.iloc[index]["customer_id"], index),
    )
    rows_to_keep.add(selected_index)

df = df.iloc[sorted(rows_to_keep)].drop(columns=["_original_order"])

output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(output_path, index=False)