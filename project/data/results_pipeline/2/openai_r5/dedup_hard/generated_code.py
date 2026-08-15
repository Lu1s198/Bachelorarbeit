import os
import re
import unicodedata
from difflib import SequenceMatcher

import numpy as np
import pandas as pd


INPUT_PATH = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r5/dedup_medium/output.parquet"
OUTPUT_PATH = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r5/dedup_hard/output.parquet"

TITLE_TOKENS = {
    "mr", "mister", "mrs", "ms", "miss", "mx",
    "dr", "doctor", "prof", "professor",
    "sir", "madam", "madame", "lady", "lord",
    "herr", "frau", "fr", "hr",
    "dipl", "ing", "mba", "msc", "bsc", "phd",
    "ph", "d", "jr", "sr",
    "rev", "rabbi", "imam", "father",
}


def safe_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_name(value):
    text = safe_text(value)
    if not text:
        return []

    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    tokens = re.findall(r"[^\W\d_]+", text, flags=re.UNICODE)

    while tokens and tokens[0] in TITLE_TOKENS:
        tokens.pop(0)

    while tokens and tokens[-1] in {"jr", "sr"}:
        tokens.pop()

    return tokens


def normalize_email(value):
    text = safe_text(value).casefold()
    if not text or text.count("@") != 1:
        return ""

    local, domain = text.split("@", 1)
    local = local.strip().replace(".", "")
    domain = domain.strip()

    if not local or not domain:
        return ""

    return f"{local}@{domain}"


def base_name_tokens(tokens):
    return [token for token in tokens if len(token) > 1]


def similarity(left, right):
    if left == right:
        return 1.0
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def token_matches(left, right):
    if left == right:
        return True

    max_length = max(len(left), len(right))
    if max_length <= 3:
        return False

    score = similarity(left, right)
    if max_length == 4:
        return score >= 0.75
    return score >= 0.80


def names_indicate_same_person(tokens_a, tokens_b):
    base_a = base_name_tokens(tokens_a)
    base_b = base_name_tokens(tokens_b)

    if not base_a or not base_b:
        return False

    if base_a == base_b:
        return True

    if len(base_a) == 1 or len(base_b) == 1:
        if len(base_a) == 1 and len(base_b) == 1:
            return token_matches(base_a[0], base_b[0])
        return False

    first_a, last_a = base_a[0], base_a[-1]
    first_b, last_b = base_b[0], base_b[-1]

    if token_matches(first_a, first_b) and token_matches(last_a, last_b):
        return True

    if len(base_a) == 2 and len(base_b) == 2:
        swapped_first = token_matches(base_a[0], base_b[-1])
        swapped_last = token_matches(base_a[-1], base_b[0])
        if swapped_first and swapped_last:
            return True

    return False


class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, item):
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left, right):
        root_left = self.find(left)
        root_right = self.find(right)

        if root_left == root_right:
            return

        if self.rank[root_left] < self.rank[root_right]:
            root_left, root_right = root_right, root_left

        self.parent[root_right] = root_left

        if self.rank[root_left] == self.rank[root_right]:
            self.rank[root_left] += 1


df = pd.read_parquet(INPUT_PATH)

required_columns = ["customer_id", "full_name", "email", "country", "registered_at"]
for column in required_columns:
    if column not in df.columns:
        raise ValueError(f"Required column missing: {column}")

df = df.copy()
df["customer_id"] = pd.to_numeric(df["customer_id"], errors="raise").astype("int64")

normalized_emails = df["email"].map(normalize_email)
normalized_names = df["full_name"].map(normalize_name)

union_find = UnionFind(len(df))
email_groups = {}

for position, email_key in enumerate(normalized_emails.tolist()):
    if email_key:
        email_groups.setdefault(email_key, []).append(position)

for positions in email_groups.values():
    if len(positions) < 2:
        continue

    for offset, left_position in enumerate(positions[:-1]):
        left_name = normalized_names.iloc[left_position]

        for right_position in positions[offset + 1:]:
            right_name = normalized_names.iloc[right_position]

            if names_indicate_same_person(left_name, right_name):
                union_find.union(left_position, right_position)

component_minimum = {}
customer_ids = df["customer_id"].to_numpy(dtype=np.int64)

for position in range(len(df)):
    root = union_find.find(position)
    current_minimum = component_minimum.get(root)

    if current_minimum is None or customer_ids[position] < customer_ids[current_minimum]:
        component_minimum[root] = position

keep_positions = sorted(component_minimum.values())
result = df.iloc[keep_positions].copy()
result = result.sort_values("customer_id", kind="stable").reset_index(drop=True)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
result.to_parquet(OUTPUT_PATH, index=False)