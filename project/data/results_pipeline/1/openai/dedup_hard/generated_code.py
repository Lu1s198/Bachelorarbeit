import os
import re
import math
import unicodedata
from collections import defaultdict
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

df["customer_id"] = df["customer_id"].astype("string")
df["full_name"] = df["full_name"].astype("string")
df["email"] = df["email"].astype("string")


titles = {
    "mr", "mister", "mrs", "ms", "miss", "mx",
    "dr", "doctor", "prof", "professor",
    "sir", "madam", "madame", "mme", "mlle",
    "herr", "frau", "fr", "hr", "drmed", "drphil",
    "ing", "dipl", "dipling", "mag", "mba", "phd",
    "phd", "md", "dds", "dvm", "rev", "fr",
    "lord", "lady", "hon", "judge"
}


def ascii_normalize(value):
    if value is None or pd.isna(value):
        return ""
    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("ß", "ss").replace("æ", "ae").replace("œ", "oe")
    return value


def normalize_email(value):
    value = ascii_normalize(value)
    if not value or "@" not in value:
        return ""
    local, domain = value.rsplit("@", 1)
    local = re.sub(r"\s+", "", local)
    domain = re.sub(r"\s+", "", domain)
    local = local.replace(".", "")
    if not local or not domain:
        return ""
    return f"{local}@{domain}"


def normalize_name(value):
    value = ascii_normalize(value)
    if not value:
        return "", [], "", ""

    if "," in value:
        parts = [part.strip() for part in value.split(",") if part.strip()]
        if len(parts) >= 2:
            value = " ".join(parts[1:] + [parts[0]])

    value = re.sub(r"[^a-z0-9\s]", " ", value)
    tokens = [token for token in value.split() if token]

    while tokens and tokens[0] in titles:
        tokens.pop(0)

    while tokens and tokens[-1] in {"jr", "sr", "ii", "iii", "iv"}:
        tokens.pop()

    if not tokens:
        return "", [], "", ""

    name_without_initials = [token for token in tokens if len(token) > 1]
    comparison_tokens = name_without_initials if len(name_without_initials) >= 2 else tokens

    normalized = "".join(comparison_tokens)
    first = comparison_tokens[0] if comparison_tokens else ""
    last = comparison_tokens[-1] if len(comparison_tokens) >= 2 else ""
    return normalized, comparison_tokens, first, last


def soundex(value):
    if not value:
        return ""
    value = re.sub(r"[^a-z]", "", value.lower())
    if not value:
        return ""

    mapping = {
        "b": "1", "f": "1", "p": "1", "v": "1",
        "c": "2", "g": "2", "j": "2", "k": "2", "q": "2", "s": "2", "x": "2", "z": "2",
        "d": "3", "t": "3",
        "l": "4",
        "m": "5", "n": "5",
        "r": "6"
    }

    first_letter = value[0].upper()
    previous = mapping.get(value[0], "")
    digits = []

    for char in value[1:]:
        digit = mapping.get(char, "")
        if digit and digit != previous:
            digits.append(digit)
        previous = digit

    return (first_letter + "".join(digits) + "000")[:4]


n = len(df)
name_norm = []
name_tokens = []
first_names = []
last_names = []
email_norm = []

for full_name, email in zip(df["full_name"], df["email"]):
    normalized, tokens, first, last = normalize_name(full_name)
    name_norm.append(normalized)
    name_tokens.append(tokens)
    first_names.append(first)
    last_names.append(last)
    email_norm.append(normalize_email(email))

df["_name_norm"] = name_norm
df["_first_name"] = first_names
df["_last_name"] = last_names
df["_email_norm"] = email_norm


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


email_groups = defaultdict(list)
name_groups = defaultdict(list)
first_last_groups = defaultdict(list)

for i, (email, name, first, last) in enumerate(
    zip(df["_email_norm"], df["_name_norm"], df["_first_name"], df["_last_name"])
):
    if email:
        email_groups[email].append(i)
    if name:
        name_groups[name].append(i)
    if first and last:
        first_last_groups[(first, last)].append(i)

for group in email_groups.values():
    if len(group) > 1:
        anchor = group[0]
        for idx in group[1:]:
            union(anchor, idx)

for group in name_groups.values():
    if len(group) > 1:
        anchor = group[0]
        for idx in group[1:]:
            union(anchor, idx)

for group in first_last_groups.values():
    if len(group) > 1:
        anchor = group[0]
        for idx in group[1:]:
            union(anchor, idx)


def similarity(left, right):
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    return SequenceMatcher(None, left, right, autojunk=False).ratio()


blocks = defaultdict(list)

for i, (first, last) in enumerate(zip(first_names, last_names)):
    if not first or not last:
        continue

    keys = {
        ("p1", first[:3], last[:3]),
        ("p2", first[:2], last[:4]),
        ("p3", first[:4], last[:2]),
        ("sx", soundex(first), soundex(last)),
    }

    for key in keys:
        if key[1] and key[2]:
            blocks[key].append(i)


candidate_pairs = set()
max_block_size = 400

for group in blocks.values():
    if len(group) < 2 or len(group) > max_block_size:
        continue
    group = sorted(set(group))
    for position, left_idx in enumerate(group[:-1]):
        for right_idx in group[position + 1:]:
            candidate_pairs.add((left_idx, right_idx))


for left_idx, right_idx in candidate_pairs:
    left_first = first_names[left_idx]
    left_last = last_names[left_idx]
    right_first = first_names[right_idx]
    right_last = last_names[right_idx]

    first_score = similarity(left_first, right_first)
    last_score = similarity(left_last, right_last)
    full_score = similarity(name_norm[left_idx], name_norm[right_idx])

    first_exact = left_first == right_first
    last_exact = left_last == right_last

    is_match = False

    if first_exact and last_score >= 0.80 and len(left_last) >= 3 and len(right_last) >= 3:
        is_match = True
    elif last_exact and first_score >= 0.80 and len(left_first) >= 3 and len(right_first) >= 3:
        is_match = True
    elif (
        first_score >= 0.80
        and last_score >= 0.80
        and full_score >= 0.84
        and len(left_first) >= 3
        and len(left_last) >= 3
        and len(right_first) >= 3
        and len(right_last) >= 3
    ):
        is_match = True
    elif (
        first_score >= 0.90
        and last_score >= 0.90
        and full_score >= 0.90
    ):
        is_match = True

    if is_match:
        union(left_idx, right_idx)


roots = np.array([find(i) for i in range(n)], dtype=np.int64)
df["_root"] = roots

customer_id_numeric = pd.to_numeric(df["customer_id"], errors="coerce")
df["_customer_id_numeric"] = customer_id_numeric
df["_customer_id_text"] = df["customer_id"].fillna("").astype("string")

df["_numeric_missing"] = df["_customer_id_numeric"].isna().astype(np.int8)
df_sorted = df.sort_values(
    by=["_root", "_numeric_missing", "_customer_id_numeric", "_customer_id_text"],
    kind="stable",
    na_position="last",
)

result = df_sorted.drop_duplicates(subset="_root", keep="first").copy()
result = result.drop(
    columns=[
        "_name_norm",
        "_first_name",
        "_last_name",
        "_email_norm",
        "_root",
        "_customer_id_numeric",
        "_customer_id_text",
        "_numeric_missing",
    ],
    errors="ignore",
)

result = result.sort_values(
    by=["customer_id"],
    key=lambda series: pd.to_numeric(series, errors="coerce"),
    kind="stable",
    na_position="last",
).reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)