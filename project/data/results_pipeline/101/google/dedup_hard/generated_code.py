import os
import re
from difflib import SequenceMatcher
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

TITLES = {
    "mr", "mrs", "ms", "miss", "dr", "prof", "sir", "madam",
    "herr", "frau", "doktor", "ing", "dipl", "phd", "md", "rev", "hon"
}

def clean_name_tokens(name):
    if not isinstance(name, str):
        return []
    name = name.lower()
    name = re.sub(r"[^\w\s]", " ", name)
    tokens = name.split()
    return [t for t in tokens if t not in TITLES]

def normalize_email(email):
    if not isinstance(email, str):
        return ""
    email = email.strip().lower()
    if "@" in email:
        local, domain = email.rsplit("@", 1)
        local = local.replace(".", "")
        if "+" in local:
            local = local.split("+")[0]
        return f"{local}@{domain}"
    return email

cleaned_names = []
core_str_names = []
sorted_str_names = []
norm_emails = []

for idx, row in df.iterrows():
    tokens = clean_name_tokens(row["full_name"])
    core = [t for t in tokens if len(t) > 1]
    cleaned_names.append(tokens)
    core_str_names.append(" ".join(core) if core else " ".join(tokens))
    sorted_str_names.append(" ".join(sorted(core if core else tokens)))
    norm_emails.append(normalize_email(row["email"]))

n = len(df)
parent = list(range(n))

def find(i):
    path = []
    while parent[i] != i:
        path.append(i)
        i = parent[i]
    for node in path:
        parent[node] = i
    return i

def union(i, j):
    root_i = find(i)
    root_j = find(j)
    if root_i != root_j:
        parent[root_i] = root_j

blocks = {}

def add_to_block(key, idx):
    if key not in blocks:
        blocks[key] = []
    blocks[key].append(idx)

for i in range(n):
    e = norm_emails[i]
    if e:
        add_to_block(f"e:{e}", i)
        if "@" in e:
            loc, dom = e.split("@", 1)
            add_to_block(f"el:{loc[:3]}@{dom}", i)

    c_str = core_str_names[i]
    if c_str:
        add_to_block(f"n:{c_str[:4]}", i)
        tokens = c_str.split()
        if len(tokens) > 1:
            add_to_block(f"nl:{tokens[-1][:4]}", i)

pairs = set()
for b_indices in blocks.values():
    if len(b_indices) > 1 and len(b_indices) < 500:
        for x in range(len(b_indices)):
            for y in range(x + 1, len(b_indices)):
                i, j = b_indices[x], b_indices[y]
                if i > j:
                    i, j = j, i
                pairs.add((i, j))

if n <= 1500:
    for i in range(n):
        for j in range(i + 1, n):
            pairs.add((i, j))

for i, j in pairs:
    e1, e2 = norm_emails[i], norm_emails[j]
    n1, n2 = core_str_names[i], core_str_names[j]
    sn1, sn2 = sorted_str_names[i], sorted_str_names[j]

    if n1 == n2 or sn1 == sn2:
        n_sim = 1.0
    elif not n1 or not n2:
        n_sim = 0.0
    else:
        n_sim = max(
            SequenceMatcher(None, n1, n2).ratio(),
            SequenceMatcher(None, sn1, sn2).ratio()
        )

    if e1 == e2 and e1 != "":
        e_sim = 1.0
    elif not e1 or not e2:
        e_sim = 0.0
    else:
        e_sim = SequenceMatcher(None, e1, e2).ratio()

    is_match = False
    if e1 == e2 and e1 != "":
        if n_sim >= 0.65:
            is_match = True
    elif e_sim >= 0.85 and n_sim >= 0.75:
        is_match = True

    if is_match:
        union(i, j)

groups = {}
for i in range(n):
    root = find(i)
    if root not in groups:
        groups[root] = []
    groups[root].append(i)

keep_indices = []
for group in groups.values():
    best_idx = min(group, key=lambda idx: df.iloc[idx]["customer_id"])
    keep_indices.append(best_idx)

res_df = df.iloc[keep_indices].copy()
res_df = res_df.sort_values(by="customer_id").reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
res_df.to_parquet(output_path, index=False)