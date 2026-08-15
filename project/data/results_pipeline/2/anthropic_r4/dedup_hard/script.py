import pandas as pd
import numpy as np
import re
from difflib import SequenceMatcher

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r4/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r4/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df['customer_id'] = df['customer_id'].astype('int64')
df['full_name'] = df['full_name'].astype(str)
df['email'] = df['email'].astype(str)
df['country'] = df['country'].astype(str)
df['registered_at'] = df['registered_at'].astype(str)

TITLES = {
    'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'herr', 'frau',
    'sir', 'madam', 'mx', 'monsieur', 'madame', 'mademoiselle'
}

def strip_titles(name):
    tokens = name.strip().split()
    cleaned = []
    for t in tokens:
        t_clean = t.lower().strip('.').strip(',')
        if t_clean not in TITLES:
            cleaned.append(t)
    return cleaned

def normalize_name(name):
    tokens = strip_titles(name)
    tokens = [re.sub(r'[^a-zA-Z]', '', t) for t in tokens]
    tokens = [t for t in tokens if t]
    if len(tokens) > 2:
        first = tokens[0]
        last = tokens[-1]
        middle_kept = [t for t in tokens[1:-1] if len(t) > 1]
        tokens = [first] + middle_kept + [last]
    tokens = [t.lower() for t in tokens]
    tokens = sorted(tokens)
    return ' '.join(tokens)

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

def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry:
        if rx < ry:
            parent[ry] = rx
        else:
            parent[rx] = ry

def name_similar(n1, n2):
    if n1 == n2:
        return True
    if not n1 or not n2:
        return False
    return SequenceMatcher(None, n1, n2).ratio() > 0.85

def email_local_similar(e1, e2):
    if e1 == e2:
        return True
    if '@' not in e1 or '@' not in e2:
        return False
    l1, d1 = e1.split('@', 1)
    l2, d2 = e2.split('@', 1)
    if d1 != d2:
        return False
    if not l1 or not l2:
        return False
    return SequenceMatcher(None, l1, l2).ratio() > 0.85

names = df['norm_name'].tolist()
emails = df['norm_email'].tolist()

for i in range(n):
    for j in range(i + 1, n):
        if name_similar(names[i], names[j]) and email_local_similar(emails[i], emails[j]):
            union(i, j)

df['group'] = [find(i) for i in range(n)]

result_idx = df.groupby('group')['customer_id'].idxmin()
result = df.loc[result_idx]
result = result[['customer_id', 'full_name', 'email', 'country', 'registered_at']].sort_values('customer_id').reset_index(drop=True)

result.to_parquet(output_path, index=False)