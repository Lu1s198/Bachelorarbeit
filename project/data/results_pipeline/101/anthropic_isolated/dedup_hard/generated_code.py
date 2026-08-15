import pandas as pd
import numpy as np
import re
from difflib import SequenceMatcher

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/anthropic_isolated/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df['customer_id'] = df['customer_id'].astype('int64')
df['full_name'] = df['full_name'].astype(str)
df['email'] = df['email'].astype(str)
df['country'] = df['country'].astype(str)
df['registered_at'] = df['registered_at'].astype(str)

TITLES = {
    'mr', 'mr.', 'mrs', 'mrs.', 'ms', 'ms.', 'miss', 'dr', 'dr.', 'prof', 'prof.',
    'herr', 'frau', 'sir', 'madam', 'mx', 'mx.', 'dott', 'dott.', 'sig', 'sig.',
    'sig.ra', 'monsieur', 'madame', 'mlle', 'senor', 'senora', 'señor', 'señora',
    'don', 'dona', 'doña'
}

def normalize_name(name):
    if pd.isna(name):
        return ""
    s = str(name).strip().lower()
    s = re.sub(r'[^\w\s]', ' ', s, flags=re.UNICODE)
    s = re.sub(r'\s+', ' ', s).strip()
    tokens = s.split(' ')
    tokens = [t for t in tokens if t not in TITLES and t.rstrip('.') not in TITLES]
    cleaned_tokens = []
    for t in tokens:
        t_stripped = t.rstrip('.')
        if len(t_stripped) <= 1:
            continue
        cleaned_tokens.append(t_stripped)
    return ' '.join(cleaned_tokens)

def normalize_email(email):
    if pd.isna(email):
        return ""
    s = str(email).strip().lower()
    if '@' not in s:
        return s
    local, domain = s.split('@', 1)
    local = local.replace('.', '')
    return f"{local}@{domain}"

df['norm_name'] = df['full_name'].apply(normalize_name)
df['norm_email'] = df['email'].apply(normalize_email)

n = len(df)
parent = list(range(n))

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        if ra < rb:
            parent[rb] = ra
        else:
            parent[ra] = rb

groups = {}
for idx, email in enumerate(df['norm_email'].values):
    groups.setdefault(email, []).append(idx)

def name_similarity(a, b):
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

norm_names = df['norm_name'].values

for email, idxs in groups.items():
    if len(idxs) < 2:
        continue
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            a_idx = idxs[i]
            b_idx = idxs[j]
            a_name = norm_names[a_idx]
            b_name = norm_names[b_idx]
            if a_name == b_name:
                union(a_idx, b_idx)
            else:
                ratio = name_similarity(a_name, b_name)
                if ratio >= 0.82:
                    union(a_idx, b_idx)

df['_cluster'] = [find(i) for i in range(n)]

df_sorted = df.sort_values('customer_id')
kept_indices = df_sorted.groupby('_cluster').head(1).index

result = df.loc[kept_indices, ['customer_id', 'full_name', 'email', 'country', 'registered_at']].copy()
result = result.sort_values('customer_id').reset_index(drop=True)

result.to_parquet(output_path, index=False)