import pandas as pd
import numpy as np
import re
import difflib

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic_isolated/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df['customer_id'] = df['customer_id'].astype('int64')
df['full_name'] = df['full_name'].astype(str)
df['email'] = df['email'].astype(str)
df['country'] = df['country'].astype(str)
df['registered_at'] = df['registered_at'].astype(str)

TITLES = {
    'dr', 'mr', 'mrs', 'ms', 'miss', 'mx', 'prof', 'professor',
    'herr', 'frau', 'sir', 'madam', 'madame', 'mme', 'mlle', 'monsieur'
}

def normalize_email(email):
    if email is None:
        return ''
    e = str(email).strip().lower()
    if '@' in e:
        local, domain = e.split('@', 1)
        local = local.replace('.', '')
        return local + '@' + domain
    return e

def normalize_name(name):
    if name is None:
        return ''
    n = str(name).strip().lower()
    n = n.replace('.', ' ')
    tokens = n.split()
    cleaned_tokens = []
    for t in tokens:
        t_clean = re.sub(r'[^a-z]', '', t)
        if not t_clean:
            continue
        if t_clean in TITLES:
            continue
        if len(t_clean) == 1:
            # likely a middle initial, skip
            continue
        cleaned_tokens.append(t_clean)
    return ' '.join(cleaned_tokens)

def name_similarity(a, b):
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()

df['norm_email'] = df['email'].apply(normalize_email)
df['norm_name'] = df['full_name'].apply(normalize_name)

n = len(df)
parent = list(range(n))

def find(x):
    while parent[x] != x:
        x = parent[x]
    return x

def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry:
        if rx < ry:
            parent[ry] = rx
        else:
            parent[rx] = ry

groups = {}
for idx, email in enumerate(df['norm_email'].values):
    groups.setdefault(email, []).append(idx)

NAME_THRESHOLD = 0.82

for email, indices in groups.items():
    if len(indices) < 2:
        continue
    for i in range(len(indices)):
        for j in range(i + 1, len(indices)):
            idx_i = indices[i]
            idx_j = indices[j]
            name_i = df.at[idx_i, 'norm_name']
            name_j = df.at[idx_j, 'norm_name']
            sim = name_similarity(name_i, name_j)
            if sim >= NAME_THRESHOLD:
                union(idx_i, idx_j)

df['root'] = [find(i) for i in range(n)]

idx_min = df.groupby('root')['customer_id'].idxmin()
result = df.loc[idx_min].copy()

result = result[['customer_id', 'full_name', 'email', 'country', 'registered_at']]
result = result.sort_values('customer_id').reset_index(drop=True)

result.to_parquet(output_path, index=False)