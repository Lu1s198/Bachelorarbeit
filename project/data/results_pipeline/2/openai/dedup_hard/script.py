import os
import re
import unicodedata
from difflib import SequenceMatcher

import pandas as pd
import numpy as np

INPUT_PATH = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai/dedup_medium/output.parquet"
OUTPUT_PATH = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai/dedup_hard/output.parquet"

TITLE_TOKENS = {
    "mr", "mrs", "ms", "miss", "mx",
    "dr", "doctor", "prof", "professor",
    "sir", "madam", "dame", "lord", "lady",
    "herr", "frau", "frl",
    "med", "medizin", "dipl", "ing",
    "phd", "md", "dds", "dvm", "jd",
    "rev", "fr", "sr", "br",
}

SUFFIX_TOKENS = {
    "jr", "sr", "ii", "iii", "iv", "v",
    "phd", "md", "dds", "dvm", "jd",
}

def to_ascii_text(value):
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().casefold()
    text = (
        text.replace("ß", "ss")
        .replace("æ", "ae")
        .replace("œ", "oe")
        .replace("ø", "o")
        .replace("đ", "d")
        .replace("ł", "l")
    )
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

def normalize_name(value):
    text = to_ascii_text(value)
    tokens = re.findall(r"[a-z]+", text)

    while tokens and tokens[0] in TITLE_TOKENS:
        tokens.pop(0)
    while tokens and tokens[-1] in SUFFIX_TOKENS:
        tokens.pop()

    tokens = [token for token in tokens if token not in TITLE_TOKENS]
    meaningful_tokens = [token for token in tokens if len(token) > 1]

    if not meaningful_tokens:
        return "", "", "", ""

    full_key = "".join(meaningful_tokens)
    first = meaningful_tokens[0]
    last = meaningful_tokens[-1] if len(meaningful_tokens) > 1 else ""
    first_last_key = first + last if last else first

    return full_key, first, last, first_last_key

def normalize_email(value):
    if value is None or pd.isna(value):
        return None

    text = str(value).strip().casefold()
    if text.count("@") != 1:
        return None

    local, domain = text.split("@", 1)
    local = local.strip()
    domain = domain.strip()

    if not local or not domain:
        return None

    return local.replace(".", "") + "@" + domain

def similarity(left, right):
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    return SequenceMatcher(None, left, right).ratio()

def names_match(name_a, name_b):
    full_a, first_a, last_a, first_last_a = name_a
    full_b, first_b, last_b, first_last_b = name_b

    if not full_a or not full_b:
        return False

    if full_a == full_b:
        return True

    full_score = similarity(full_a, full_b)
    if full_score >= 0.84:
        return True

    if first_a and first_b and last_a and last_b:
        first_score = similarity(first_a, first_b)
        last_score = similarity(last_a, last_b)
        first_last_score = similarity(first_last_a, first_last_b)

        if first_a == first_b and last_a == last_b:
            return True

        if first_score >= 0.75 and last_score >= 0.75 and first_last_score >= 0.78:
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

if df.empty:
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)
else:
    df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")

    normalized_names = [normalize_name(value) for value in df["full_name"].tolist()]
    normalized_emails = [normalize_email(value) for value in df["email"].tolist()]

    email_groups = {}
    for idx, email_key in enumerate(normalized_emails):
        if email_key is not None:
            email_groups.setdefault(email_key, []).append(idx)

    union_find = UnionFind(len(df))

    for indices in email_groups.values():
        if len(indices) < 2:
            continue

        exact_name_groups = {}
        for idx in indices:
            name_key = normalized_names[idx][0]
            if name_key:
                exact_name_groups.setdefault(name_key, []).append(idx)

        for same_name_indices in exact_name_groups.values():
            if len(same_name_indices) > 1:
                first_idx = same_name_indices[0]
                for other_idx in same_name_indices[1:]:
                    union_find.union(first_idx, other_idx)

        for position, left_idx in enumerate(indices):
            left_name = normalized_names[left_idx]
            if not left_name[0]:
                continue

            for right_idx in indices[position + 1:]:
                right_name = normalized_names[right_idx]
                if not right_name[0]:
                    continue

                if names_match(left_name, right_name):
                    union_find.union(left_idx, right_idx)

    component_best = {}
    customer_ids = df["customer_id"].tolist()

    for idx in range(len(df)):
        root = union_find.find(idx)
        current_best = component_best.get(root)

        if current_best is None:
            component_best[root] = idx
        else:
            current_id = customer_ids[idx]
            best_id = customer_ids[current_best]

            if pd.isna(best_id) or (not pd.isna(current_id) and current_id < best_id):
                component_best[root] = idx

    selected_indices = sorted(component_best.values())
    result = df.iloc[selected_indices].copy()

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_parquet(OUTPUT_PATH, index=False)