import pandas as pd
import numpy as np
import re
from difflib import SequenceMatcher

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df['customer_id'] = df['customer_id'].astype(str)

TITLES = {
    'mr', 'mrs', 'ms', 'miss', 'mx', 'dr', 'prof', 'professor',
    'herr', 'frau', 'fr', 'hr', 'mag', 'ing', 'sir', 'madam',
    'dr.', 'prof.', 'mr.', 'mrs.', 'ms.'
}

def normalize_name(name):
    if pd.isna(name):
        return ""
    s = str(name).strip().lower()
    s = re.sub(r'[.,]', ' ', s)
    tokens = s.split()
    tokens = [t for t in tokens if t not in TITLES]
    tokens = [t for t in tokens if len(t) > 1]
    return " ".join(tokens)

def normalize_email(email):
    if pd.isna(email):
        return ""
    s = str(email).strip().lower()
    if '@' not in s:
        return s
    local, domain = s.split('@', 1)
    local = local.replace('.', '')
    return f"{local}@{domain}"

df['_norm_name'] = df['full_name'].apply(normalize_name)
df['_norm_email'] = df['email'].apply(normalize_email)

def name_similarity(a, b):
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()

n = len(df)
parent = list(range(n))

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry:
        parent[rx] = ry

groups = {}
for idx, email in enumerate(df['_norm_email']):
    groups.setdefault(email, []).append(idx)

for email, idxs in groups.items():
    if len(idxs) < 2:
        continue
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            a_idx, b_idx = idxs[i], idxs[j]
            name_a = df.at[a_idx, '_norm_name']
            name_b = df.at[b_idx, '_norm_name']
            if name_a == name_b:
                union(a_idx, b_idx)
            elif name_a and name_b:
                sim = name_similarity(name_a, name_b)
                if sim >= 0.82:
                    union(a_idx, b_idx)

df['_cluster'] = [find(i) for i in range(n)]

def sort_key(cid):
    try:
        return (0, int(cid))
    except (ValueError, TypeError):
        return (1, str(cid))

df['_sort_key'] = df['customer_id'].apply(sort_key)

df_sorted = df.sort_values('_sort_key')
result = df_sorted.drop_duplicates(subset='_cluster', keep='first')

result = result.drop(columns=['_norm_name', '_norm_email', '_cluster', '_sort_key'])

result = result.reset_index(drop=True)

result.to_parquet(output_path, index=False)