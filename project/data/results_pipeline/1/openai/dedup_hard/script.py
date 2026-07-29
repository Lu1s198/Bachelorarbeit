import os
import re
import unicodedata
from difflib import SequenceMatcher

import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/dedup_hard/output.parquet"

df = pd.read_parquet(input_path).copy()

required_columns = ["customer_id", "full_name", "email", "country", "registered_at"]
for column in required_columns:
    if column not in df.columns:
        df[column] = pd.NA

df = df.reset_index(drop=True)
n = len(df)


def is_present(value):
    if pd.isna(value):
        return False
    return str(value).strip() != ""


def normalize_text(value):
    if not is_present(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower().strip()
    return text


def normalize_email(value):
    if not is_present(value):
        return ""
    email = normalize_text(value).replace(" ", "")
    if email.count("@") != 1:
        return ""
    local_part, domain = email.split("@", 1)
    if not local_part or not domain:
        return ""
    local_part = local_part.replace(".", "")
    return f"{local_part}@{domain}"


def name_tokens(value):
    text = normalize_text(value)
    if not text:
        return []
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = [token for token in text.split() if token]
    return tokens


def meaningful_name_tokens(value):
    tokens = name_tokens(value)
    return [token for token in tokens if len(token) > 1]


def name_key(value):
    tokens = meaningful_name_tokens(value)
    return " ".join(tokens)


def sorted_name_key(value):
    tokens = meaningful_name_tokens(value)
    return " ".join(sorted(tokens))


def safe_ratio(left, right):
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, node):
        while self.parent[node] != node:
            self.parent[node] = self.parent[self.parent[node]]
            node = self.parent[node]
        return node

    def union(self, left, right):
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        if self.rank[root_left] < self.rank[root_right]:
            self.parent[root_left] = root_right
        elif self.rank[root_left] > self.rank[root_right]:
            self.parent[root_right] = root_left
        else:
            self.parent[root_right] = root_left
            self.rank[root_left] += 1


uf = UnionFind(n)

emails = df["email"].map(normalize_email).tolist()
name_keys = df["full_name"].map(name_key).tolist()
sorted_name_keys = df["full_name"].map(sorted_name_key).tolist()
token_lists = df["full_name"].map(meaningful_name_tokens).tolist()

email_groups = {}
for idx, email in enumerate(emails):
    if email:
        if email in email_groups:
            uf.union(idx, email_groups[email])
        else:
            email_groups[email] = idx

name_groups = {}
for idx, key in enumerate(name_keys):
    if key and len(key) >= 3:
        if key in name_groups:
            uf.union(idx, name_groups[key])
        else:
            name_groups[key] = idx

sorted_name_groups = {}
for idx, key in enumerate(sorted_name_keys):
    if key and len(key) >= 3:
        if key in sorted_name_groups:
            uf.union(idx, sorted_name_groups[key])
        else:
            sorted_name_groups[key] = idx

blocks = {}
for idx, tokens in enumerate(token_lists):
    if len(tokens) < 2:
        continue

    first_name = tokens[0]
    last_name = tokens[-1]

    block_keys = {
        ("last_prefix", last_name[:3]),
        ("first_prefix", first_name[:3]),
        ("last_first", last_name[:2], first_name[:1]),
        ("first_last_initial", first_name[:1], last_name[:1]),
    }

    for block_key in block_keys:
        if all(part for part in block_key[1:]):
            blocks.setdefault(block_key, []).append(idx)


def likely_same_name(left_idx, right_idx):
    left_tokens = token_lists[left_idx]
    right_tokens = token_lists[right_idx]

    if len(left_tokens) < 2 or len(right_tokens) < 2:
        return False

    left_first, left_last = left_tokens[0], left_tokens[-1]
    right_first, right_last = right_tokens[0], right_tokens[-1]

    first_similarity = safe_ratio(left_first, right_first)
    last_similarity = safe_ratio(left_last, right_last)
    full_similarity = safe_ratio(name_keys[left_idx], name_keys[right_idx])
    sorted_similarity = safe_ratio(sorted_name_keys[left_idx], sorted_name_keys[right_idx])

    if left_first == right_first and last_similarity >= 0.82 and full_similarity >= 0.82:
        return True

    if left_last == right_last and first_similarity >= 0.82 and full_similarity >= 0.82:
        return True

    if first_similarity >= 0.80 and last_similarity >= 0.80 and max(full_similarity, sorted_similarity) >= 0.84:
        return True

    if first_similarity >= 0.90 and last_similarity >= 0.72 and max(full_similarity, sorted_similarity) >= 0.88:
        return True

    if last_similarity >= 0.90 and first_similarity >= 0.72 and max(full_similarity, sorted_similarity) >= 0.88:
        return True

    return False


checked_pairs = set()

for _, indices in blocks.items():
    if len(indices) < 2:
        continue

    if len(indices) > 750:
        continue

    for position, left_idx in enumerate(indices[:-1]):
        for right_idx in indices[position + 1:]:
            pair = (left_idx, right_idx) if left_idx < right_idx else (right_idx, left_idx)
            if pair in checked_pairs:
                continue
            checked_pairs.add(pair)

            if likely_same_name(left_idx, right_idx):
                uf.union(left_idx, right_idx)

groups = {}
for idx in range(n):
    root = uf.find(idx)
    groups.setdefault(root, []).append(idx)

nonempty = df.notna() & df.astype("string").apply(lambda col: col.str.strip().ne(""))
completeness = nonempty.sum(axis=1).astype(int)

if "registered_at" in df.columns:
    registered_present = df["registered_at"].notna().astype(int)
else:
    registered_present = pd.Series(0, index=df.index)

keep_indices = []
for indices in groups.values():
    candidates = pd.DataFrame(
        {
            "idx": indices,
            "completeness": completeness.iloc[indices].to_numpy(),
            "registered_present": registered_present.iloc[indices].to_numpy(),
        }
    )
    candidates = candidates.sort_values(
        ["completeness", "registered_present", "idx"],
        ascending=[False, False, True],
        kind="stable",
    )
    keep_indices.append(int(candidates.iloc[0]["idx"]))

result = df.iloc[sorted(keep_indices)].copy()

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)