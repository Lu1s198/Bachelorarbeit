import os
import re
import unicodedata
from difflib import SequenceMatcher

import pandas as pd


input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai/dedup_hard/output.parquet"

df = pd.read_parquet(input_path).reset_index(drop=True)

TITLE_TOKENS = {
    "dr", "prof", "professor", "mr", "mrs", "ms", "miss", "mx",
    "herr", "frau", "fr", "sir", "madam", "madame", "mister",
    "doktor", "dipl", "ing", "med", "jur", "phd", "mba", "msc",
    "bsc", "llm", "jr", "sr", "junior", "senior", "ii", "iii",
    "iv", "v", "von", "the"
}


def as_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_email(value):
    text = as_text(value)
    if not text or "@" not in text:
        return ""
    text = unicodedata.normalize("NFKC", text).strip().casefold()
    local, domain = text.rsplit("@", 1)
    local = re.sub(r"\s+", "", local).replace(".", "")
    domain = re.sub(r"\s+", "", domain)
    if not local or not domain:
        return ""
    return f"{local}@{domain}"


def normalize_name(value):
    text = as_text(value)
    if not text:
        return (), ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold()
    tokens = re.findall(r"[a-z0-9]+", text)
    tokens = [token for token in tokens if token not in TITLE_TOKENS]
    meaningful = [token for token in tokens if len(token) > 1]
    if not meaningful:
        meaningful = tokens
    return tuple(meaningful), "".join(meaningful)


def similarity(left, right):
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    return SequenceMatcher(None, left, right, autojunk=False).ratio()


def names_match(name_a, name_b):
    tokens_a, compact_a = name_a
    tokens_b, compact_b = name_b

    if not compact_a or not compact_b:
        return False

    if compact_a == compact_b:
        return True

    if sorted(tokens_a) == sorted(tokens_b):
        return True

    if len(tokens_a) == 1 or len(tokens_b) == 1:
        return similarity(compact_a, compact_b) >= 0.86

    first_score = similarity(tokens_a[0], tokens_b[0])
    last_score = similarity(tokens_a[-1], tokens_b[-1])
    full_score = similarity(compact_a, compact_b)

    if first_score == 1.0 and last_score >= 0.72:
        return True
    if last_score == 1.0 and first_score >= 0.72:
        return True
    if (first_score >= 0.78 and last_score >= 0.72) or (
        last_score >= 0.78 and first_score >= 0.72
    ):
        return True
    if first_score >= 0.83 and last_score >= 0.83:
        return True
    if full_score >= 0.89:
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


normalized_emails = [normalize_email(value) for value in df["email"].tolist()]
normalized_names = [normalize_name(value) for value in df["full_name"].tolist()]

email_groups = {}
for position, email in enumerate(normalized_emails):
    if email:
        email_groups.setdefault(email, []).append(position)

union_find = UnionFind(len(df))

for positions in email_groups.values():
    if len(positions) < 2:
        continue

    exact_name_groups = {}
    for position in positions:
        tokens, compact = normalized_names[position]
        if compact:
            exact_name_groups.setdefault(compact, []).append(position)

    for same_name_positions in exact_name_groups.values():
        if len(same_name_positions) > 1:
            first = same_name_positions[0]
            for other in same_name_positions[1:]:
                union_find.union(first, other)

    for left_offset in range(len(positions)):
        left = positions[left_offset]
        if not normalized_names[left][1]:
            continue
        for right_offset in range(left_offset + 1, len(positions)):
            right = positions[right_offset]
            if not normalized_names[right][1]:
                continue
            if names_match(normalized_names[left], normalized_names[right]):
                union_find.union(left, right)

customer_ids = df["customer_id"].tolist()
best_position_by_root = {}

for position in range(len(df)):
    root = union_find.find(position)
    if root not in best_position_by_root:
        best_position_by_root[root] = position
    else:
        current_best = best_position_by_root[root]
        if customer_ids[position] < customer_ids[current_best]:
            best_position_by_root[root] = position

keep_positions = sorted(best_position_by_root.values(), key=lambda pos: customer_ids[pos])
result = df.iloc[keep_positions].reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)