import os
import re
import unicodedata
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r2/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r2/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

for column in ["full_name", "email", "country", "registered_at"]:
    if column in df.columns:
        df[column] = df[column].astype("string")

df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")

titles = {
    "mr", "mister", "mrs", "ms", "miss", "mx",
    "dr", "doctor", "prof", "professor",
    "herr", "frau", "frl", "doktor",
    "ing", "dipl", "diplom", "mag", "msc", "mba",
    "sir", "madam", "madame", "monsieur", "senor", "senora", "senorita"
}

def ascii_normalize(value):
    if value is None or pd.isna(value):
        return ""
    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return value

def normalize_email(value):
    text = ascii_normalize(value).replace(" ", "")
    if text.count("@") != 1:
        return ""
    local, domain = text.split("@", 1)
    local = local.replace(".", "")
    domain = domain.strip(".")
    if not local or not domain:
        return ""
    return local + "@" + domain

def normalize_name(value):
    text = ascii_normalize(value)
    text = re.sub(r"[^a-z0-9\s'-]", " ", text)
    text = re.sub(r"[-']", " ", text)
    tokens = [token for token in text.split() if token]
    while tokens and tokens[0] in titles:
        tokens.pop(0)
    if len(tokens) >= 3:
        tokens = [
            token for index, token in enumerate(tokens)
            if not (0 < index < len(tokens) - 1 and len(token) == 1)
        ]
    return " ".join(tokens)

def levenshtein_distance(left, right):
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    if len(left) > len(right):
        left, right = right, left
    previous = list(range(len(left) + 1))
    for i, right_char in enumerate(right, start=1):
        current = [i]
        for j, left_char in enumerate(left, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (left_char != right_char)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]

def names_match(left, right):
    if not left or not right:
        return False
    if left == right:
        return True

    left_tokens = left.split()
    right_tokens = right.split()

    if len(left_tokens) >= 2 and len(right_tokens) >= 2:
        left_first, left_last = left_tokens[0], left_tokens[-1]
        right_first, right_last = right_tokens[0], right_tokens[-1]

        first_distance = levenshtein_distance(left_first, right_first)
        last_distance = levenshtein_distance(left_last, right_last)

        first_limit = max(1, int(max(len(left_first), len(right_first)) * 0.25))
        last_limit = max(1, int(max(len(left_last), len(right_last)) * 0.25))

        if first_distance <= first_limit and last_distance <= last_limit:
            return True

        if (
            levenshtein_distance(left_first, right_last) <= first_limit
            and levenshtein_distance(left_last, right_first) <= last_limit
        ):
            return True

    compact_left = left.replace(" ", "")
    compact_right = right.replace(" ", "")
    max_length = max(len(compact_left), len(compact_right))
    allowed_distance = max(1, int(max_length * 0.18))

    return levenshtein_distance(compact_left, compact_right) <= allowed_distance

df["_email_key"] = df["email"].map(normalize_email).astype("string")
df["_name_key"] = df["full_name"].map(normalize_name).astype("string")

n = len(df)
parent = list(range(n))
rank = [0] * n

def find(node):
    while parent[node] != node:
        parent[node] = parent[parent[node]]
        node = parent[node]
    return node

def union(left, right):
    left_root = find(left)
    right_root = find(right)
    if left_root == right_root:
        return
    if rank[left_root] < rank[right_root]:
        parent[left_root] = right_root
    elif rank[left_root] > rank[right_root]:
        parent[right_root] = left_root
    else:
        parent[right_root] = left_root
        rank[left_root] += 1

valid_email_mask = df["_email_key"].notna() & df["_email_key"].ne("")
valid_indices = df.index[valid_email_mask].tolist()

email_groups = {}
for index in valid_indices:
    key = df.at[index, "_email_key"]
    email_groups.setdefault(key, []).append(index)

for indices in email_groups.values():
    if len(indices) < 2:
        continue

    name_buckets = {}
    for index in indices:
        name = df.at[index, "_name_key"]
        if not name:
            continue
        tokens = name.split()
        first_char = tokens[0][0] if tokens and tokens[0] else ""
        last_char = tokens[-1][0] if tokens and tokens[-1] else ""
        bucket_keys = {
            (first_char, last_char),
            ("", last_char),
            (first_char, ""),
        }
        for bucket_key in bucket_keys:
            name_buckets.setdefault(bucket_key, []).append(index)

    compared_pairs = set()
    for bucket_indices in name_buckets.values():
        for position, left_index in enumerate(bucket_indices):
            left_name = df.at[left_index, "_name_key"]
            for right_index in bucket_indices[position + 1:]:
                pair = (min(left_index, right_index), max(left_index, right_index))
                if pair in compared_pairs:
                    continue
                compared_pairs.add(pair)
                right_name = df.at[right_index, "_name_key"]
                if names_match(left_name, right_name):
                    union(left_index, right_index)

representatives = {}
for index in range(n):
    root = find(index)
    customer_id = df.at[index, "customer_id"]
    customer_sort = int(customer_id) if pd.notna(customer_id) else np.iinfo(np.int64).max
    if root not in representatives:
        representatives[root] = index
    else:
        current_index = representatives[root]
        current_id = df.at[current_index, "customer_id"]
        current_sort = int(current_id) if pd.notna(current_id) else np.iinfo(np.int64).max
        if customer_sort < current_sort or (customer_sort == current_sort and index < current_index):
            representatives[root] = index

keep_indices = sorted(representatives.values())
result = df.loc[keep_indices, ["customer_id", "full_name", "email", "country", "registered_at"]].copy()
result = result.sort_values("customer_id", kind="stable").reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)