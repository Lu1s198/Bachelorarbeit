import os
import re
import unicodedata
from difflib import SequenceMatcher

import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

TITLE_TOKENS = {
    "dr", "doctor", "prof", "professor", "mr", "mrs", "ms", "miss", "mx",
    "sir", "dame", "herr", "frau", "fr", "hr", "ing", "dipl", "diplom",
    "mag", "med", "jur", "rev", "frater", "sister"
}
SUFFIX_TOKENS = {
    "jr", "sr", "junior", "senior", "phd", "md", "dds", "esq", "mba",
    "msc", "bsc"
}

def to_ascii_text(value):
    if pd.isna(value):
        return ""
    text = str(value).strip().casefold()
    text = (
        text.replace("ß", "ss")
        .replace("æ", "ae")
        .replace("œ", "oe")
        .replace("ø", "o")
        .replace("ð", "d")
        .replace("þ", "th")
        .replace("ł", "l")
    )
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))

def normalized_email(value):
    if pd.isna(value):
        return ""
    email = to_ascii_text(value).replace(" ", "")
    if email.count("@") != 1:
        return ""
    local, domain = email.split("@", 1)
    if not local or not domain:
        return ""
    return local.replace(".", "") + "@" + domain

def normalized_name_tokens(value):
    text = to_ascii_text(value)
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    tokens = text.split()

    while tokens and tokens[0] in TITLE_TOKENS:
        tokens.pop(0)
    while tokens and tokens[-1] in SUFFIX_TOKENS:
        tokens.pop()

    tokens = [token for token in tokens if len(token) > 1]
    return tokens

def ratio(left, right):
    return SequenceMatcher(None, left, right, autojunk=False).ratio()

def names_match(tokens_a, tokens_b):
    if not tokens_a or not tokens_b:
        return False

    if tokens_a == tokens_b or sorted(tokens_a) == sorted(tokens_b):
        return True

    name_a = "".join(tokens_a)
    name_b = "".join(tokens_b)

    if len(tokens_a) == 1 or len(tokens_b) == 1:
        return ratio(name_a, name_b) >= 0.90

    first_score = ratio(tokens_a[0], tokens_b[0])
    last_score = ratio(tokens_a[-1], tokens_b[-1])
    full_score = ratio(name_a, name_b)

    if first_score >= 0.80 and last_score >= 0.80 and full_score >= 0.84:
        return True

    reversed_first_score = ratio(tokens_a[0], tokens_b[-1])
    reversed_last_score = ratio(tokens_a[-1], tokens_b[0])
    if reversed_first_score >= 0.90 and reversed_last_score >= 0.90 and full_score >= 0.84:
        return True

    return False

n = len(df)
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

email_groups = {}
name_tokens = []

for position, (_, row) in enumerate(df.iterrows()):
    email_key = normalized_email(row["email"])
    tokens = normalized_name_tokens(row["full_name"])
    name_tokens.append(tokens)
    if email_key:
        email_groups.setdefault(email_key, []).append(position)

for positions in email_groups.values():
    group_size = len(positions)
    if group_size < 2:
        continue

    for i in range(group_size - 1):
        left_position = positions[i]
        left_tokens = name_tokens[left_position]
        if not left_tokens:
            continue

        for j in range(i + 1, group_size):
            right_position = positions[j]
            if names_match(left_tokens, name_tokens[right_position]):
                union(left_position, right_position)

customer_ids = pd.to_numeric(df["customer_id"], errors="coerce")
best_position_by_root = {}

for position in range(n):
    root = find(position)
    if root not in best_position_by_root:
        best_position_by_root[root] = position
        continue

    current_best = best_position_by_root[root]
    current_id = customer_ids.iloc[position]
    best_id = customer_ids.iloc[current_best]

    if pd.isna(best_id) or (not pd.isna(current_id) and current_id < best_id):
        best_position_by_root[root] = position

selected_positions = sorted(best_position_by_root.values())
result = df.iloc[selected_positions].copy()
result = result.sort_values("customer_id", kind="stable").reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)