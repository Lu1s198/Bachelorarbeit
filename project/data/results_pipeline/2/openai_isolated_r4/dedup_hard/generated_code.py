import os
import re
import unicodedata
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r4/dedup_hard/output.parquet"

df = pd.read_parquet(input_path).copy()

title_tokens = {
    "mr", "mrs", "ms", "miss", "mx", "sir", "madam",
    "herr", "frau", "frl",
    "dr", "prof", "professor", "doktor", "doctor",
    "med", "phil", "jur", "rer", "nat", "ing", "msc",
    "mba", "bsc", "ba", "ma", "phd", "dphil", "jd",
    "llm", "dipl", "mag", "rev", "fr", "sr", "jr"
}

def safe_text(value):
    if value is None or pd.isna(value):
        return ""
    return str(value)

def normalize_unicode(text):
    text = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in text if not unicodedata.combining(ch))

def normalize_name(value):
    text = normalize_unicode(safe_text(value))
    tokens = re.findall(r"[a-z0-9]+", text)
    tokens = [token for token in tokens if token not in title_tokens]
    tokens_without_initials = [token for token in tokens if len(token) > 1]
    if not tokens_without_initials:
        tokens_without_initials = tokens
    return tokens_without_initials

def normalize_email(value):
    text = safe_text(value).strip().casefold()
    if not text or "@" not in text:
        return ""
    local, domain = text.rsplit("@", 1)
    local = local.strip().replace(".", "")
    domain = domain.strip()
    if not local or not domain:
        return ""
    return local + "@" + domain

def levenshtein_similarity(a, b):
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            insertion = current[-1] + 1
            deletion = previous[j] + 1
            substitution = previous[j - 1] + (char_a != char_b)
            current.append(min(insertion, deletion, substitution))
        previous = current
    return 1.0 - (previous[-1] / max(len(a), len(b)))

def names_match(tokens_a, tokens_b):
    if not tokens_a or not tokens_b:
        return False

    base_a = "".join(tokens_a)
    base_b = "".join(tokens_b)

    if base_a == base_b:
        return True

    if len(tokens_a) == 1 or len(tokens_b) == 1:
        return levenshtein_similarity(base_a, base_b) >= 0.88

    first_similarity = levenshtein_similarity(tokens_a[0], tokens_b[0])
    last_similarity = levenshtein_similarity(tokens_a[-1], tokens_b[-1])
    full_similarity = levenshtein_similarity(base_a, base_b)

    if full_similarity >= 0.84 and first_similarity >= 0.70 and last_similarity >= 0.70:
        return True

    return False

n = len(df)
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

name_tokens = [normalize_name(value) for value in df["full_name"].tolist()]
email_keys = [normalize_email(value) for value in df["email"].tolist()]

email_groups = {}
for idx, key in enumerate(email_keys):
    if key:
        email_groups.setdefault(key, []).append(idx)

for indices in email_groups.values():
    group_size = len(indices)
    if group_size < 2:
        continue

    for left_pos in range(group_size - 1):
        i = indices[left_pos]
        tokens_i = name_tokens[i]
        if not tokens_i:
            continue

        for right_pos in range(left_pos + 1, group_size):
            j = indices[right_pos]
            if names_match(tokens_i, name_tokens[j]):
                union(i, j)

customer_ids = pd.to_numeric(df["customer_id"], errors="coerce")
representative_by_root = {}

for idx in range(n):
    root = find(idx)
    current_id = customer_ids.iloc[idx]
    if root not in representative_by_root:
        representative_by_root[root] = idx
    else:
        existing_idx = representative_by_root[root]
        existing_id = customer_ids.iloc[existing_idx]
        if pd.isna(existing_id) or (not pd.isna(current_id) and current_id < existing_id):
            representative_by_root[root] = idx

selected_indices = sorted(representative_by_root.values(), key=lambda i: (pd.isna(customer_ids.iloc[i]), customer_ids.iloc[i] if not pd.isna(customer_ids.iloc[i]) else np.inf))
result = df.iloc[selected_indices].copy()

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)