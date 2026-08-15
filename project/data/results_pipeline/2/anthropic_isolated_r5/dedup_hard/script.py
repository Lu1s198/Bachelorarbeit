import pandas as pd
import numpy as np
import re
import os

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r5/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df['customer_id'] = df['customer_id'].astype('int64')
df['full_name'] = df['full_name'].astype(str)
df['email'] = df['email'].astype(str)
df['country'] = df['country'].astype(str)
df['registered_at'] = df['registered_at'].astype(str)

TITLES = {
    'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'herr', 'frau', 'mx',
    'sir', 'madam', 'mister', 'mistress', 'professor', 'doktor'
}

def normalize_name(name):
    if name is None:
        return ""
    s = str(name).strip()
    s = re.sub(r'[.,]', '', s)
    s = re.sub(r'\s+', ' ', s)
    tokens = s.split(' ')
    tokens = [t for t in tokens if t.lower() not in TITLES]
    if len(tokens) > 2:
        first = tokens[0]
        last = tokens[-1]
        middle = tokens[1:-1]
        middle = [m for m in middle if len(m) > 1]
        tokens = [first] + middle + [last]
    name_key = ' '.join(tokens).lower().strip()
    return name_key

def normalize_email(email):
    if email is None:
        return ""
    e = str(email).strip().lower()
    if '@' in e:
        local, domain = e.split('@', 1)
        local = local.replace('.', '')
        return local + '@' + domain
    return e

def levenshtein(a, b):
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        curr = [i] + [0] * lb
        ca = a[i - 1]
        for j in range(1, lb + 1):
            cb = b[j - 1]
            cost = 0 if ca == cb else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[lb]

df['__email_key__'] = df['email'].apply(normalize_email)
df['__name_key__'] = df['full_name'].apply(normalize_name)

n = len(df)
parent = list(range(n))

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(x, y):
    px, py = find(x), find(y)
    if px != py:
        if px < py:
            parent[py] = px
        else:
            parent[px] = py

email_groups = df.groupby('__email_key__').indices

for key, idxs in email_groups.items():
    idxs = list(idxs)
    m = len(idxs)
    if m < 2:
        continue
    for i in range(m):
        a = idxs[i]
        name_a = df.at[a, '__name_key__']
        for j in range(i + 1, m):
            b = idxs[j]
            if find(a) == find(b):
                continue
            name_b = df.at[b, '__name_key__']
            maxlen = max(len(name_a), len(name_b), 1)
            dist = levenshtein(name_a, name_b)
            threshold = max(2, int(0.2 * maxlen))
            if dist <= threshold:
                union(a, b)

roots = [find(i) for i in range(n)]
df['__group__'] = roots

idx_min = df.groupby('__group__')['customer_id'].idxmin()
result = df.loc[idx_min].copy()

result = result[['customer_id', 'full_name', 'email', 'country', 'registered_at']]
result = result.sort_values('customer_id').reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)