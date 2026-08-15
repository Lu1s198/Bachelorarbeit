import os
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd

input_path = Path(
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
)
output_path = Path(
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/openai_v1_zero_shot/output.parquet"
)

if not input_path.exists():
    synthetic_dir = Path(
        r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
    )
    parquet_files = sorted(synthetic_dir.rglob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No input parquet file found at {input_path} or in {synthetic_dir}")
    input_path = parquet_files[0]

df = pd.read_parquet(input_path)

required_columns = ["customer_id", "full_name", "email", "country", "registered_at"]
missing_columns = [column for column in required_columns if column not in df.columns]
if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

df = df.drop_duplicates(keep="first").reset_index(drop=True)

df["_registered_at_sort"] = pd.to_datetime(df["registered_at"], errors="coerce")
df["_original_order"] = range(len(df))

email_present = df["email"].notna() & df["email"].astype("string").str.strip().ne("")
with_email = df.loc[email_present].sort_values(
    ["email", "_registered_at_sort", "_original_order"],
    ascending=[True, False, True],
    kind="mergesort",
)
with_email = with_email.drop_duplicates(subset=["email"], keep="first")
without_email = df.loc[~email_present]

df = pd.concat([with_email, without_email], ignore_index=True)
df = df.sort_values("_original_order", kind="mergesort").reset_index(drop=True)

titles = {
    "mr", "mrs", "ms", "miss", "mx", "dr", "doctor", "prof", "professor",
    "sir", "madam", "mme", "mlle", "herr", "frau", "fr", "hr",
    "ing", "dipl", "diplom", "rev", "reverend", "hon", "judge",
}


def normalize_text(value):
    if pd.isna(value):
        return ""
    value = str(value).strip().casefold().replace("ß", "ss")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return value


def normalize_name(value):
    text = normalize_text(value)
    tokens = re.findall(r"[a-z0-9]+", text)

    while tokens and tokens[0] in titles:
        tokens.pop(0)

    if len(tokens) > 2:
        tokens = [
            token
            for position, token in enumerate(tokens)
            if not (0 < position < len(tokens) - 1 and len(token) == 1)
        ]

    return " ".join(tokens)


def normalize_email(value):
    if pd.isna(value):
        return ""
    text = normalize_text(value).replace(" ", "")
    if "@" not in text:
        return ""
    local_part, domain = text.rsplit("@", 1)
    if not local_part or not domain:
        return ""
    return f"{local_part.replace('.', '')}@{domain}"


def names_match(name_a, name_b):
    if not name_a or not name_b:
        return False

    if name_a == name_b:
        return True

    tokens_a = name_a.split()
    tokens_b = name_b.split()

    if len(tokens_a) < 2 or len(tokens_b) < 2:
        return False

    first_a, last_a = tokens_a[0], tokens_a[-1]
    first_b, last_b = tokens_b[0], tokens_b[-1]

    first_similarity = SequenceMatcher(None, first_a, first_b).ratio()
    last_similarity = SequenceMatcher(None, last_a, last_b).ratio()
    full_similarity = SequenceMatcher(None, name_a, name_b).ratio()

    if first_a == first_b and last_similarity >= 0.80 and full_similarity >= 0.84:
        return True

    if last_a == last_b and first_similarity >= 0.80 and full_similarity >= 0.84:
        return True

    if first_similarity >= 0.84 and last_similarity >= 0.84 and full_similarity >= 0.84:
        return True

    return False


df["_normalized_name"] = df["full_name"].map(normalize_name)
df["_normalized_email"] = df["email"].map(normalize_email)

parent = list(range(len(df)))


def find(node):
    while parent[node] != node:
        parent[node] = parent[parent[node]]
        node = parent[node]
    return node


def union(node_a, node_b):
    root_a = find(node_a)
    root_b = find(node_b)
    if root_a != root_b:
        parent[root_b] = root_a


valid_fuzzy_rows = df[
    df["_normalized_email"].ne("") & df["_normalized_name"].ne("")
]

for _, group in valid_fuzzy_rows.groupby("_normalized_email", sort=False):
    indices = group.index.tolist()
    names = group["_normalized_name"].to_dict()

    for left_position in range(len(indices)):
        left_index = indices[left_position]
        for right_position in range(left_position + 1, len(indices)):
            right_index = indices[right_position]
            if names_match(names[left_index], names[right_index]):
                union(left_index, right_index)

components = {}
for index in range(len(df)):
    root = find(index)
    components.setdefault(root, []).append(index)

keep_indices = []
for indices in components.values():
    component = df.loc[indices]
    smallest_customer_id_index = component["customer_id"].idxmin()
    keep_indices.append(smallest_customer_id_index)

df = df.loc[keep_indices].copy()
df = df.sort_values("customer_id", kind="mergesort").reset_index(drop=True)

df = df.drop(
    columns=[
        "_registered_at_sort",
        "_original_order",
        "_normalized_name",
        "_normalized_email",
    ],
    errors="ignore",
)

os.makedirs(output_path.parent, exist_ok=True)
df.to_parquet(output_path, index=False)