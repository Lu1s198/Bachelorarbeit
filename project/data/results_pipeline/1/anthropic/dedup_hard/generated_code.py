import pandas as pd
import numpy as np
import re
from difflib import SequenceMatcher

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df['customer_id'] = df['customer_id'].astype('int64')
df['full_name'] = df['full_name'].astype(str)
df['email'] = df['email'].astype(str)
df['country'] = df['country'].astype(str)
df['registered_at'] = df['registered_at'].astype(str)

TITLES = {
    'dr', 'dr.', 'mr', 'mr.', 'mrs', 'mrs.', 'ms', 'ms.', 'prof', 'prof.',
    'herr', 'frau', 'miss', 'mx', 'mx.', 'sir', 'madam', 'sr', 'sr.', 'jr', 'jr.'
}

def strip_titles(name):
    tokens = name.split()
    cleaned = [t for t in tokens if t.lower().strip('.') not in {ti.strip('.') for ti in TITLES}]
    return ' '.join(cleaned)

def remove_middle_initials(name):
    tokens = name.split()
    cleaned = [t for t in tokens if len(t.strip('.')) > 1]
    return ' '.join(cleaned)

def normalize_name(name):
    name = strip_titles(name)
    name = remove_middle_initials(name)
    name = name.lower().strip()
    name = re.sub(r'[^a-z\s]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

def normalize_email(email):
    email = email.strip().lower()
    if '@' not in email:
        return email
    local, domain = email.split('@', 1)
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
        parent[rb] = ra

names = df['norm_name'].tolist()
emails = df['norm_email'].tolist()

NAME_SIM_THRESHOLD = 0.82

for i in range(n):
    for j in range(i + 1, n):
        if find(i) == find(j):
            continue
        if emails[i] != emails[j]:
            continue
        if names[i] == names[j]:
            union(i, j)
            continue
        ratio = SequenceMatcher(None, names[i], names[j]).ratio()
        if ratio >= NAME_SIM_THRESHOLD:
            union(i, j)

df['cluster'] = [find(i) for i in range(n)]

df_sorted = df.sort_values('customer_id')
keep_idx = df_sorted.groupby('cluster')['customer_id'].idxmin()

result = df.loc[keep_idx, ['customer_id', 'full_name', 'email', 'country', 'registered_at']].copy()
result = result.sort_values('customer_id').reset_index(drop=True)

result.to_parquet(output_path, index=False)