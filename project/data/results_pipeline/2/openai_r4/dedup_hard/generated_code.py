import os
import re
import unicodedata
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r4/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r4/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

TITLE_WORDS = {
    "mr", "mrs", "ms", "miss", "mx", "dr", "doctor", "prof", "professor",
    "sir", "madam", "madame", "herr", "frau", "fr", "hr", "ing",
    "dipl", "diplom", "mag", "mba", "msc", "bsc", "phd", "md",
    "jr", "sr", "junior", "senior"
}

def ascii_normalize(value):
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = text.replace("ß", "ss").replace("æ", "ae").replace("œ", "oe")
    text = text.replace("ø", "o").replace("ł", "l").replace("đ", "d")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text

def normalize_email(value):
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    if "@" not in text:
        return ""
    local, domain = text.rsplit("@", 1)
    local = re.sub(r"[\s.]+", "", local)
    domain = re.sub(r"\s+", "", domain)
    if not local or not domain:
        return ""
    return local + "@" + domain

def normalize_name(value):
    text = ascii_normalize(value)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [t for t in text.split() if t]
    while tokens and tokens[0] in TITLE_WORDS:
        tokens.pop(0)
    return tokens

def name_core(tokens):
    if not tokens:
        return ""
    filtered = []
    for i, token in enumerate(tokens):
        if len(token) == 1 and len(tokens) > 1:
            continue
        filtered.append(token)
    return " ".join(filtered)

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
            current.append(min(
                current[-1] + 1,
                previous[j] + 1,
                previous[j - 1] + (ca != cb)
            ))
        previous = current
    return previous[-1]

def close_word(a, b):
    if a == b:
        return True
    if not a or not b:
        return False
    max_len = max(len(a), len(b))
    if max_len <= 3:
        allowed = 1
    elif max_len <= 6:
        allowed = 1
    else:
        allowed = max(1, int(max_len * 0.18))
    return levenshtein(a, b) <= allowed

def names_match(tokens_a, tokens_b, core_a, core_b):
    if not core_a or not core_b:
        return False
    if core_a == core_b:
        return True

    words_a = core_a.split()
    words_b = core_b.split()

    if len(words_a) < 2 or len(words_b) < 2:
        return False

    first_a, last_a = words_a[0], words_a[-1]
    first_b, last_b = words_b[0], words_b[-1]

    if close_word(first_a, first_b) and close_word(last_a, last_b):
        return True

    if len(words_a) == len(words_b):
        equalish = sum(close_word(x, y) for x, y in zip(words_a, words_b))
        if equalish == len(words_a):
            return True

    joined_a = "".join(words_a)
    joined_b = "".join(words_b)
    max_len = max(len(joined_a), len(joined_b))
    allowed = 1 if max_len <= 8 else max(1, int(max_len * 0.12))
    return levenshtein(joined_a, joined_b) <= allowed

emails = df["email"].map(normalize_email).tolist()
name_tokens = df["full_name"].map(normalize_name).tolist()
name_cores = [name_core(tokens) for tokens in name_tokens]

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

email_groups = {}
for idx, email in enumerate(emails):
    if email:
        email_groups.setdefault(email, []).append(idx)

for indices in email_groups.values():
    if len(indices) < 2:
        continue

    exact_name_groups = {}
    for idx in indices:
        core = name_cores[idx]
        if core:
            exact_name_groups.setdefault(core, []).append(idx)

    for same_name_indices in exact_name_groups.values():
        if len(same_name_indices) > 1:
            base = same_name_indices[0]
            for other in same_name_indices[1:]:
                union(base, other)

    group_size = len(indices)
    if group_size <= 1000:
        for pos, idx_a in enumerate(indices):
            if not name_cores[idx_a]:
                continue
            for idx_b in indices[pos + 1:]:
                if not name_cores[idx_b]:
                    continue
                if names_match(
                    name_tokens[idx_a], name_tokens[idx_b],
                    name_cores[idx_a], name_cores[idx_b]
                ):
                    union(idx_a, idx_b)
    else:
        buckets = {}
        for idx in indices:
            core_words = name_cores[idx].split()
            if len(core_words) >= 2:
                key = (core_words[0][:2], core_words[-1][:2])
                buckets.setdefault(key, []).append(idx)

        for bucket_indices in buckets.values():
            if len(bucket_indices) > 1000:
                continue
            for pos, idx_a in enumerate(bucket_indices):
                for idx_b in bucket_indices[pos + 1:]:
                    if names_match(
                        name_tokens[idx_a], name_tokens[idx_b],
                        name_cores[idx_a], name_cores[idx_b]
                    ):
                        union(idx_a, idx_b)

df["_component"] = [find(i) for i in range(n)]
df["_customer_id_numeric"] = pd.to_numeric(df["customer_id"], errors="coerce")
df = df.sort_values(
    ["_component", "_customer_id_numeric"],
    kind="stable",
    na_position="last"
)
result = df.drop_duplicates(subset="_component", keep="first")
result = result.drop(columns=["_component", "_customer_id_numeric"])

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)