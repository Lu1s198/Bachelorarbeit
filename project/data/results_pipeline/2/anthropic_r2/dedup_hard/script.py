import pandas as pd
import numpy as np
import re
import difflib

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r2/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r2/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df['customer_id'] = df['customer_id'].astype('int64')
df['full_name'] = df['full_name'].astype(str)
df['email'] = df['email'].astype(str)
df['country'] = df['country'].astype(str)
df['registered_at'] = df['registered_at'].astype(str)

titles = {
    'mr', 'mrs', 'ms', 'miss', 'mx', 'dr', 'prof', 'herr', 'frau',
    'mag', 'ing', 'sir', 'madam', 'jr', 'sr', 'dipl', 'phd'
}

def normalize_name(name):
    if name is None:
        return ''
    s = str(name).lower()
    s = re.sub(r'[^a-z\s]', ' ', s)
    tokens = [t for t in s.split() if t]
    tokens = [t for t in tokens if t not in titles]
    tokens = [t for t in tokens if len(t) > 1]
    return ' '.join(sorted(tokens))

def normalize_email(email):
    if email is None:
        return ''
    s = str(email).strip().lower()
    if '@' in s:
        local, domain = s.split('@', 1)
        local = local.replace('.', '')
        return local + '@' + domain
    return s

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

groups = df.groupby('norm_email').indices

for email_key, idxs in groups.items():
    idxs = list(idxs)
    if len(idxs) < 2:
        continue
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            a, b = idxs[i], idxs[j]
            name_a = df.iloc[a]['norm_name']
            name_b = df.iloc[b]['norm_name']
            if name_a == name_b:
                union(a, b)
            else:
                ratio = difflib.SequenceMatcher(None, name_a, name_b).ratio()
                if ratio >= 0.75:
                    union(a, b)

df['cluster'] = [find(i) for i in range(n)]

idx_min = df.groupby('cluster')['customer_id'].idxmin()
result = df.loc[idx_min]

result = result[['customer_id', 'full_name', 'email', 'country', 'registered_at']]
result = result.sort_values('customer_id').reset_index(drop=True)

result.to_parquet(output_path, index=False)