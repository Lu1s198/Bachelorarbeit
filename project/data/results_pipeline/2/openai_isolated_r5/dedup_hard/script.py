import os
import re
import unicodedata
from collections import defaultdict
from functools import lru_cache

import numpy as np
import pandas as pd


input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r5/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

title_tokens = {
    "herr", "frau", "hr", "fr", "mr", "mrs", "ms", "miss", "mx",
    "dr", "doktor", "doctor", "prof", "professor", "sir", "dame",
    "madam", "madame", "lord", "lady", "rev", "reverend", "fr",
    "father", "schwester", "bruder", "ing", "dipl", "med", "jur",
    "mba", "msc", "bsc", "phd", "ma", "ba", "llm", "dds", "md",
    "drmed", "drphil", "drjur"
}


def as_text(value):
    if value is None or pd.isna(value):
        return ""
    return str(value)


def ascii_normalize(value):
    value = as_text(value).strip().lower().replace("ß", "ss")
    value = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in value if not unicodedata.combining(ch))


@lru_cache(maxsize=500000)
def email_key(value):
    value = ascii_normalize(value).replace(" ", "")
    if value.count("@") != 1:
        return ""
    local, domain = value.split("@", 1)
    if not local or not domain:
        return ""
    local = local.replace(".", "")
    return local + "@" + domain


@lru_cache(maxsize=500000)
def name_features(value):
    normalized = ascii_normalize(value)
    tokens = re.findall(r"[a-z0-9]+", normalized)
    tokens = [token for token in tokens if token not in title_tokens]

    while tokens and tokens[-1] in title_tokens:
        tokens.pop()

    if not tokens:
        return ("", "", "", "", "")

    non_initials = [
        token for i, token in enumerate(tokens)
        if len(token) > 1 or i == 0 or i == len(tokens) - 1
    ]

    if not non_initials:
        non_initials = tokens

    compact = "".join(non_initials)
    first = non_initials[0]
    last = non_initials[-1] if len(non_initials) >= 2 else ""
    core = first + last if last else first
    reversed_core = last + first if last else first

    return (compact, first, last, core, reversed_core)


@lru_cache(maxsize=1000000)
def levenshtein_distance(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    if len(a) > len(b):
        a, b = b, a

    previous = list(range(len(a) + 1))
    for i, char_b in enumerate(b, start=1):
        current = [i]
        for j, char_a in enumerate(a, start=1):
            insertion = current[-1] + 1
            deletion = previous[j] + 1
            substitution = previous[j - 1] + (char_a != char_b)
            current.append(min(insertion, deletion, substitution))
        previous = current
    return previous[-1]


def similar_part(a, b):
    if not a or not b:
        return False
    if a == b:
        return True
    shortest = min(len(a), len(b))
    longest = max(len(a), len(b))
    if shortest < 4:
        return False
    distance = levenshtein_distance(a, b)
    return distance / longest <= 0.25


@lru_cache(maxsize=1000000)
def names_match(name_a, name_b):
    compact_a, first_a, last_a, core_a, rev_core_a = name_features(name_a)
    compact_b, first_b, last_b, core_b, rev_core_b = name_features(name_b)

    if not compact_a or not compact_b:
        return False

    if compact_a == compact_b:
        return True

    if core_a and (core_a == core_b or core_a == rev_core_b or rev_core_a == core_b):
        return True

    if not last_a or not last_b:
        return False

    direct_first = similar_part(first_a, first_b)
    direct_last = similar_part(last_a, last_b)
    reverse_first = similar_part(first_a, last_b)
    reverse_last = similar_part(last_a, first_b)

    if direct_first and direct_last:
        total_distance = levenshtein_distance(core_a, core_b)
        return total_distance / max(len(core_a), len(core_b)) <= 0.30

    if reverse_first and reverse_last:
        total_distance = levenshtein_distance(core_a, rev_core_b)
        return total_distance / max(len(core_a), len(rev_core_b)) <= 0.30

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
        root_a, root_b = root_b, root_a
    parent[root_b] = root_a
    if rank[root_a] == rank[root_b]:
        rank[root_a] += 1


emails = df["email"].tolist()
names = df["full_name"].tolist()
email_groups = defaultdict(list)

for idx, value in enumerate(emails):
    key = email_key(as_text(value))
    if key:
        email_groups[key].append(idx)


def union_exact_name_groups(indices):
    compact_groups = {}
    core_groups = {}

    for idx in indices:
        compact, first, last, core, reversed_core = name_features(as_text(names[idx]))

        if compact:
            if compact in compact_groups:
                union(idx, compact_groups[compact])
            else:
                compact_groups[compact] = idx

        if first and last and core:
            if core in core_groups:
                union(idx, core_groups[core])
            else:
                core_groups[core] = idx


for indices in email_groups.values():
    if len(indices) < 2:
        continue

    union_exact_name_groups(indices)

    if len(indices) <= 300:
        for pos, idx_a in enumerate(indices[:-1]):
            name_a = as_text(names[idx_a])
            for idx_b in indices[pos + 1:]:
                if names_match(name_a, as_text(names[idx_b])):
                    union(idx_a, idx_b)
        continue

    signature_groups = defaultdict(list)

    for idx in indices:
        compact, first, last, core, reversed_core = name_features(as_text(names[idx]))
        signatures = set()

        if compact:
            signatures.add(("compact", compact))
            if len(compact) <= 40:
                for position in range(len(compact)):
                    signatures.add(("compact_del", compact[:position] + compact[position + 1:]))

        if core and first and last:
            signatures.add(("core", core))
            signatures.add(("core", reversed_core))
            if len(core) <= 40:
                for position in range(len(core)):
                    signatures.add(("core_del", core[:position] + core[position + 1:]))
                for position in range(len(reversed_core)):
                    signatures.add(
                        ("core_del", reversed_core[:position] + reversed_core[position + 1:])
                    )

        for signature in signatures:
            signature_groups[signature].append(idx)

    checked_pairs = set()

    for candidate_indices in signature_groups.values():
        group_size = len(candidate_indices)
        if group_size < 2 or group_size > 300:
            continue

        for pos, idx_a in enumerate(candidate_indices[:-1]):
            name_a = as_text(names[idx_a])
            for idx_b in candidate_indices[pos + 1:]:
                pair = (idx_a, idx_b) if idx_a < idx_b else (idx_b, idx_a)
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)
                if names_match(name_a, as_text(names[idx_b])):
                    union(idx_a, idx_b)


customer_ids = pd.to_numeric(df["customer_id"], errors="coerce").to_numpy()
best_index_by_root = {}

for idx in range(n):
    root = find(idx)
    if root not in best_index_by_root:
        best_index_by_root[root] = idx
    else:
        current_best = best_index_by_root[root]
        current_id = customer_ids[current_best]
        candidate_id = customer_ids[idx]

        if pd.isna(current_id) or (not pd.isna(candidate_id) and candidate_id < current_id):
            best_index_by_root[root] = idx

keep_indices = sorted(
    best_index_by_root.values(),
    key=lambda i: (pd.isna(customer_ids[i]), customer_ids[i] if not pd.isna(customer_ids[i]) else np.inf, i)
)

result = df.iloc[keep_indices].copy()

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)