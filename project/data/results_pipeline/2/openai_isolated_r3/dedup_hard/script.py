import os
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher

import numpy as np
import pandas as pd


INPUT_PATH = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
OUTPUT_PATH = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r3/dedup_hard/output.parquet"

TITLE_TOKENS = {
    "dr", "prof", "professor", "mr", "mrs", "ms", "miss", "mx",
    "herr", "frau", "sir", "madam", "madame", "dame", "lord",
    "lady", "dipl", "ing", "phd", "md", "dds", "dvm", "mba",
    "bsc", "msc", "ba", "ma", "jr", "sr", "junior", "senior",
}


def normalize_text(value):
    if pd.isna(value):
        return ""
    value = unicodedata.normalize("NFKD", str(value)).casefold()
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value


def parse_name(value):
    text = normalize_text(value)
    tokens = re.findall(r"[a-z0-9]+", text)
    tokens = [token for token in tokens if token not in TITLE_TOKENS]

    if not tokens:
        return "", "", (), ""

    if len(tokens) == 1:
        return tokens[0], tokens[0], (), tokens[0]

    first = tokens[0]
    last = tokens[-1]
    middle = tuple(tokens[1:-1])
    return first, last, middle, first + last


def normalize_email(value):
    if pd.isna(value):
        return "", "", ""
    value = unicodedata.normalize("NFKC", str(value)).strip().casefold()
    if value.count("@") != 1:
        return "", "", ""
    local, domain = value.rsplit("@", 1)
    local = local.replace(".", "").replace(" ", "")
    domain = domain.strip()
    if not local or not domain:
        return "", "", ""
    return local + "@" + domain, local, domain


def similarity(left, right):
    if left == right:
        return 1.0
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right, autojunk=False).ratio()


def middle_names_compatible(left_middle, right_middle):
    if not left_middle or not right_middle:
        return True

    shared_count = min(len(left_middle), len(right_middle))
    for idx in range(shared_count):
        left = left_middle[idx]
        right = right_middle[idx]

        if left == right:
            continue
        if len(left) == 1 and right.startswith(left):
            continue
        if len(right) == 1 and left.startswith(right):
            continue
        if len(left) > 1 and len(right) > 1:
            return False

    return True


def names_match(left_name, right_name):
    left_first, left_last, left_middle, left_compact = left_name
    right_first, right_last, right_middle, right_compact = right_name

    if not left_compact or not right_compact:
        return False

    if not middle_names_compatible(left_middle, right_middle):
        return False

    if left_first == left_last or right_first == right_last:
        return left_compact == right_compact

    if left_first == right_first and left_last == right_last:
        return True

    first_similarity = similarity(left_first, right_first)
    last_similarity = similarity(left_last, right_last)
    whole_similarity = similarity(left_compact, right_compact)

    first_exact = left_first == right_first
    last_exact = left_last == right_last

    if first_exact and last_similarity >= 0.72 and whole_similarity >= 0.84:
        return True
    if last_exact and first_similarity >= 0.72 and whole_similarity >= 0.84:
        return True

    return (
        first_similarity >= 0.80
        and last_similarity >= 0.80
        and whole_similarity >= 0.86
    )


def damerau_levenshtein_with_limit(left, right, limit):
    if abs(len(left) - len(right)) > limit:
        return limit + 1

    previous_previous = None
    previous = list(range(len(right) + 1))

    for i, left_char in enumerate(left, start=1):
        current = [i]
        row_min = i

        for j, right_char in enumerate(right, start=1):
            cost = 0 if left_char == right_char else 1
            value = min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + cost,
            )

            if (
                previous_previous is not None
                and i > 1
                and j > 1
                and left_char == right[j - 2]
                and left[i - 2] == right_char
            ):
                value = min(value, previous_previous[j - 2] + 1)

            current.append(value)
            if value < row_min:
                row_min = value

        if row_min > limit:
            return limit + 1

        previous_previous, previous = previous, current

    return previous[-1]


def emails_match(left_email, right_email):
    left_normalized, left_local, left_domain = left_email
    right_normalized, right_local, right_domain = right_email

    if not left_normalized or not right_normalized:
        return False

    if left_normalized == right_normalized:
        return True

    if left_domain != right_domain:
        return False

    longest = max(len(left_local), len(right_local))
    if longest < 4:
        return False

    allowed_distance = max(1, longest // 10)
    return (
        damerau_levenshtein_with_limit(
            left_local,
            right_local,
            allowed_distance,
        )
        <= allowed_distance
    )


def email_signatures(local):
    if len(local) < 4:
        return set()

    signatures = {local}

    for pos in range(len(local)):
        signatures.add(local[:pos] + local[pos + 1:])

    for pos in range(len(local) - 1):
        if local[pos] != local[pos + 1]:
            signatures.add(
                local[:pos]
                + local[pos + 1]
                + local[pos]
                + local[pos + 2:]
            )

    return signatures


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
        left_root = self.find(left)
        right_root = self.find(right)

        if left_root == right_root:
            return

        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root

        self.parent[right_root] = left_root

        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1


df = pd.read_parquet(INPUT_PATH).copy()

required_columns = ["customer_id", "full_name", "email", "country", "registered_at"]
for column in required_columns:
    if column not in df.columns:
        raise ValueError(f"Required column missing: {column}")

df["customer_id"] = pd.to_numeric(df["customer_id"], errors="raise").astype("int64")

row_count = len(df)
names = [parse_name(value) for value in df["full_name"].tolist()]
emails = [normalize_email(value) for value in df["email"].tolist()]

union_find = UnionFind(row_count)
seen_pairs = set()


def evaluate_pair(left_index, right_index):
    if left_index == right_index:
        return

    if left_index > right_index:
        left_index, right_index = right_index, left_index

    pair = (left_index, right_index)
    if pair in seen_pairs:
        return
    seen_pairs.add(pair)

    if names_match(names[left_index], names[right_index]) and emails_match(
        emails[left_index], emails[right_index]
    ):
        union_find.union(left_index, right_index)


exact_email_groups = defaultdict(list)
for index, (normalized_email, _, _) in enumerate(emails):
    if normalized_email:
        exact_email_groups[normalized_email].append(index)

for group in exact_email_groups.values():
    if len(group) < 2:
        continue
    for left_position in range(len(group) - 1):
        for right_position in range(left_position + 1, len(group)):
            evaluate_pair(group[left_position], group[right_position])

signature_groups = defaultdict(list)
for index, (_, local, domain) in enumerate(emails):
    if not local or not domain:
        continue
    for signature in email_signatures(local):
        signature_groups[(domain, signature)].append(index)

for group in signature_groups.values():
    if len(group) < 2:
        continue

    unique_group = list(dict.fromkeys(group))
    if len(unique_group) < 2:
        continue

    for left_position in range(len(unique_group) - 1):
        for right_position in range(left_position + 1, len(unique_group)):
            left_index = unique_group[left_position]
            right_index = unique_group[right_position]

            if emails[left_index][0] == emails[right_index][0]:
                continue

            evaluate_pair(left_index, right_index)

customer_ids = df["customer_id"].to_numpy(dtype=np.int64)
best_index_by_root = {}

for index in range(row_count):
    root = union_find.find(index)
    current_best = best_index_by_root.get(root)

    if current_best is None:
        best_index_by_root[root] = index
    elif (
        customer_ids[index] < customer_ids[current_best]
        or (
            customer_ids[index] == customer_ids[current_best]
            and index < current_best
        )
    ):
        best_index_by_root[root] = index

keep_indices = sorted(
    best_index_by_root.values(),
    key=lambda idx: (customer_ids[idx], idx),
)

result = df.iloc[keep_indices].copy()
result = result.sort_values("customer_id", kind="stable").reset_index(drop=True)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
result.to_parquet(OUTPUT_PATH, index=False)