import os
import re
import unicodedata
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated/dedup_hard/output.parquet"

df = pd.read_parquet(input_path).copy()

for col in ["customer_id", "full_name", "email", "country", "registered_at"]:
    if col not in df.columns:
        df[col] = pd.NA

df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")
df["full_name"] = df["full_name"].astype("string")
df["email"] = df["email"].astype("string")
df["country"] = df["country"].astype("string")
df["registered_at"] = df["registered_at"].astype("string")

title_tokens = {
    "dr", "prof", "professor", "mr", "mrs", "ms", "miss", "mx",
    "herr", "frau", "fr", "hr", "sir", "madam", "madame",
    "ing", "dipl", "med", "phd", "ph", "d", "mba", "msc", "bsc",
    "doktor", "doctor", "diplom", "mag", "ra", "llm", "ma", "ba"
}
suffix_tokens = {"jr", "sr", "junior", "senior", "ii", "iii", "iv"}

def ascii_fold(value):
    value = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in value if not unicodedata.combining(ch))

def normalize_email(value):
    if value is None or pd.isna(value):
        return None
    value = str(value).strip().casefold()
    if not value or "@" not in value:
        return None
    local, domain = value.rsplit("@", 1)
    local = re.sub(r"\s+", "", local)
    domain = re.sub(r"\s+", "", domain)
    if not local or not domain:
        return None
    local = local.replace(".", "")
    return local + "@" + domain

def normalize_name(value):
    if value is None or pd.isna(value):
        return (), ""
    value = ascii_fold(str(value)).casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    tokens = [x for x in value.split() if x]
    while tokens and tokens[0] in title_tokens:
        tokens.pop(0)
    while tokens and tokens[-1] in suffix_tokens:
        tokens.pop()
    significant = [x for x in tokens if len(x) > 1]
    if significant:
        tokens = significant
    return tuple(tokens), "".join(tokens)

def levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            insert_cost = current[-1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (ca != cb)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]

def token_close(a, b):
    if a == b:
        return True
    shortest = min(len(a), len(b))
    longest = max(len(a), len(b))
    if shortest < 3:
        return False
    distance = levenshtein(a, b)
    if longest <= 4:
        return distance <= 1
    if longest <= 7:
        return distance <= 1
    return distance <= 2

def names_match(name_a, compact_a, name_b, compact_b):
    if not name_a or not name_b:
        return False

    if compact_a == compact_b:
        return True

    if len(name_a) == len(name_b) and tuple(sorted(name_a)) == tuple(sorted(name_b)):
        return True

    if len(name_a) == 1 or len(name_b) == 1:
        a = name_a[0]
        b = name_b[0]
        return len(a) >= 4 and len(b) >= 4 and token_close(a, b)

    first_a, last_a = name_a[0], name_a[-1]
    first_b, last_b = name_b[0], name_b[-1]

    if token_close(first_a, first_b) and token_close(last_a, last_b):
        return True

    if token_close(first_a, last_b) and token_close(last_a, first_b):
        return True

    matches = 0
    used = set()
    for token_a in name_a:
        for j, token_b in enumerate(name_b):
            if j not in used and token_close(token_a, token_b):
                matches += 1
                used.add(j)
                break
    return matches >= 2

normalized_names = [normalize_name(v) for v in df["full_name"].tolist()]
name_tokens = [x[0] for x in normalized_names]
name_compacts = [x[1] for x in normalized_names]
email_keys = [normalize_email(v) for v in df["email"].tolist()]

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
for idx, key in enumerate(email_keys):
    if key is not None:
        email_groups.setdefault(key, []).append(idx)

for indices in email_groups.values():
    if len(indices) < 2:
        continue

    exact_name_groups = {}
    for idx in indices:
        compact = name_compacts[idx]
        if compact:
            exact_name_groups.setdefault(compact, []).append(idx)

    for same_name_indices in exact_name_groups.values():
        if len(same_name_indices) > 1:
            anchor = same_name_indices[0]
            for idx in same_name_indices[1:]:
                union(anchor, idx)

    if len(indices) <= 1500:
        for pos, left_idx in enumerate(indices):
            for right_idx in indices[pos + 1:]:
                if names_match(
                    name_tokens[left_idx],
                    name_compacts[left_idx],
                    name_tokens[right_idx],
                    name_compacts[right_idx],
                ):
                    union(left_idx, right_idx)
    else:
        buckets = {}
        for idx in indices:
            tokens = name_tokens[idx]
            if len(tokens) >= 2:
                keys = {
                    ("f", tokens[0][:2]),
                    ("l", tokens[-1][:3]),
                    ("fl", tokens[0][:1] + tokens[-1][:2]),
                }
                for key in keys:
                    buckets.setdefault(key, []).append(idx)
        seen_pairs = set()
        for bucket_indices in buckets.values():
            for pos, left_idx in enumerate(bucket_indices):
                for right_idx in bucket_indices[pos + 1:]:
                    pair = (left_idx, right_idx) if left_idx < right_idx else (right_idx, left_idx)
                    if pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)
                    if names_match(
                        name_tokens[left_idx],
                        name_compacts[left_idx],
                        name_tokens[right_idx],
                        name_compacts[right_idx],
                    ):
                        union(left_idx, right_idx)

components = {}
for idx in range(n):
    root = find(idx)
    components.setdefault(root, []).append(idx)

keep_indices = []
customer_ids = df["customer_id"].tolist()

for members in components.values():
    def selection_key(idx):
        customer_id = customer_ids[idx]
        if pd.isna(customer_id):
            return (1, np.iinfo(np.int64).max, idx)
        return (0, int(customer_id), idx)

    keep_indices.append(min(members, key=selection_key))

result = df.iloc[sorted(keep_indices)].copy()
result = result.sort_values(
    by=["customer_id"],
    kind="stable",
    na_position="last"
).reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)