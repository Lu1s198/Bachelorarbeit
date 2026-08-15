import os
import re
import unicodedata
from functools import lru_cache

import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r3/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r3/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

required_columns = ["customer_id", "full_name", "email", "country", "registered_at"]
for column in required_columns:
    if column not in df.columns:
        df[column] = pd.NA

df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")


def is_missing(value):
    return value is None or pd.isna(value)


def normalize_text(value):
    if is_missing(value):
        return ""
    text = str(value).strip().lower()
    text = text.replace("ß", "ss").replace("æ", "ae").replace("œ", "oe").replace("ø", "o")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text


title_tokens = {
    "mr", "mrs", "ms", "miss", "mx",
    "dr", "doctor", "prof", "professor",
    "herr", "frau", "fr", "hr",
    "dipl", "ing", "med", "phil", "rer", "nat",
    "mba", "msc", "bsc", "ma", "ba",
    "sir", "dame", "lord", "lady",
    "rev", "reverend", "hon", "honorable",
}

suffix_tokens = {
    "jr", "sr", "junior", "senior",
    "ii", "iii", "iv", "v",
    "phd", "md", "dds", "esq",
}


def normalize_name(value):
    text = normalize_text(value)
    if not text:
        return []
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = [token for token in text.split() if token]
    while tokens and tokens[0] in title_tokens:
        tokens.pop(0)
    while tokens and tokens[-1] in suffix_tokens:
        tokens.pop()
    return tokens


def canonical_email(value):
    if is_missing(value):
        return ""
    email = normalize_text(value)
    email = re.sub(r"\s+", "", email)
    if email.count("@") != 1:
        return ""
    local, domain = email.split("@", 1)
    local = local.replace(".", "")
    if not local or not domain or "." not in domain:
        return ""
    return f"{local}@{domain}"


def name_signature(tokens):
    if not tokens:
        return ""
    return " ".join(tokens)


def core_name_tokens(tokens):
    return [token for token in tokens if len(token) > 1]


@lru_cache(maxsize=200000)
def levenshtein_distance(left, right):
    if left == right:
        return 0
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for i, char_left in enumerate(left, start=1):
        current = [i]
        for j, char_right in enumerate(right, start=1):
            insertion = current[j - 1] + 1
            deletion = previous[j] + 1
            substitution = previous[j - 1] + (char_left != char_right)
            current.append(min(insertion, deletion, substitution))
        previous = current
    return previous[-1]


def similar_token(left, right):
    if left == right:
        return True
    if not left or not right:
        return False
    shortest = min(len(left), len(right))
    if shortest < 4:
        return False
    distance = levenshtein_distance(left, right)
    if shortest >= 9:
        return distance <= 2
    return distance <= 1


def names_match(tokens_a, tokens_b):
    if not tokens_a or not tokens_b:
        return False

    signature_a = name_signature(tokens_a)
    signature_b = name_signature(tokens_b)
    if signature_a == signature_b:
        return True

    core_a = core_name_tokens(tokens_a)
    core_b = core_name_tokens(tokens_b)

    if not core_a:
        core_a = tokens_a
    if not core_b:
        core_b = tokens_b

    if core_a == core_b:
        return True

    if len(core_a) < 2 or len(core_b) < 2:
        return False

    first_a, last_a = core_a[0], core_a[-1]
    first_b, last_b = core_b[0], core_b[-1]

    first_match = similar_token(first_a, first_b)
    last_match = similar_token(last_a, last_b)

    if not (first_match and last_match):
        return False

    if first_a == first_b or last_a == last_b:
        return True

    return min(len(first_a), len(first_b)) >= 5 and min(len(last_a), len(last_b)) >= 5


n = len(df)
parent = list(range(n))
rank = [0] * n


def find(item):
    while parent[item] != item:
        parent[item] = parent[parent[item]]
        item = parent[item]
    return item


def union(left, right):
    root_left = find(left)
    root_right = find(right)
    if root_left == root_right:
        return
    if rank[root_left] < rank[root_right]:
        parent[root_left] = root_right
    elif rank[root_left] > rank[root_right]:
        parent[root_right] = root_left
    else:
        parent[root_right] = root_left
        rank[root_left] += 1


name_tokens = [normalize_name(value) for value in df["full_name"].tolist()]
email_keys = [canonical_email(value) for value in df["email"].tolist()]

email_groups = {}
for index, email_key in enumerate(email_keys):
    if email_key:
        email_groups.setdefault(email_key, []).append(index)

for indices in email_groups.values():
    group_size = len(indices)
    if group_size < 2:
        continue

    if group_size <= 300:
        candidate_pairs = (
            (indices[left_position], indices[right_position])
            for left_position in range(group_size - 1)
            for right_position in range(left_position + 1, group_size)
        )
    else:
        blocks = {}
        for index in indices:
            tokens = core_name_tokens(name_tokens[index]) or name_tokens[index]
            if len(tokens) >= 2:
                block_key = (tokens[0][:1], tokens[-1][:1])
            elif tokens:
                block_key = (tokens[0][:2], "")
            else:
                continue
            blocks.setdefault(block_key, []).append(index)

        candidate_pairs = (
            (block[left_position], block[right_position])
            for block in blocks.values()
            for left_position in range(len(block) - 1)
            for right_position in range(left_position + 1, len(block))
        )

    for left, right in candidate_pairs:
        if names_match(name_tokens[left], name_tokens[right]):
            union(left, right)

component_rows = {}
customer_ids = df["customer_id"].tolist()

for index in range(n):
    root = find(index)
    current_best = component_rows.get(root)

    if current_best is None:
        component_rows[root] = index
        continue

    current_id = customer_ids[current_best]
    candidate_id = customer_ids[index]

    if pd.isna(current_id) and not pd.isna(candidate_id):
        component_rows[root] = index
    elif not pd.isna(current_id) and not pd.isna(candidate_id) and candidate_id < current_id:
        component_rows[root] = index

keep_indices = sorted(
    component_rows.values(),
    key=lambda index: (
        pd.isna(customer_ids[index]),
        customer_ids[index] if not pd.isna(customer_ids[index]) else np.inf,
        index,
    ),
)

result = df.iloc[keep_indices].copy()
result = result.sort_values(["customer_id"], kind="stable", na_position="last").reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)