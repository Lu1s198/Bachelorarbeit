import os
from pathlib import Path
import re
import difflib
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r5/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r5/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)
df['customer_id'] = df['customer_id'].astype('int64')

TITLES = {'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'herr', 'frau', 'sir', 'lady', 'mx', 'doctor', 'professor'}

def clean_name(name):
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = re.sub(r'[^a-z0-9\s]', ' ', name)
    words = name.split()
    if words and words[0] in TITLES:
        words = words[1:]
    if len(words) > 1:
        non_initials = [w for w in words if len(w) > 1]
        if non_initials:
            words = non_initials
    return " ".join(words)

def clean_email(email):
    if not isinstance(email, str) or '@' not in email:
        return ""
    email = email.lower().strip()
    parts = email.rsplit('@', 1)
    local = parts[0].replace('.', '')
    if '+' in local:
        local = local.split('+')[0]
    return f"{local}@{parts[1]}"

df['c_name'] = df['full_name'].apply(clean_name)
df['c_email'] = df['email'].apply(clean_email)

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

email_groups = {}
for idx, c_em in enumerate(df['c_email']):
    if c_em:
        email_groups.setdefault(c_em, []).append(idx)

for c_em, indices in email_groups.items():
    for i in range(len(indices)):
        for j in range(i + 1, len(indices)):
            idx1, idx2 = indices[i], indices[j]
            n1, n2 = df['c_name'].iloc[idx1], df['c_name'].iloc[idx2]
            if not n1 or not n2 or n1 == n2 or difflib.SequenceMatcher(None, n1, n2).ratio() >= 0.7:
                union(idx1, idx2)

domain_groups = {}
for idx, (c_em, c_nm) in enumerate(zip(df['c_email'], df['c_name'])):
    dom = c_em.split('@')[-1] if '@' in c_em else ''
    first_char = c_nm[0] if c_nm else ''
    key = (dom, first_char)
    domain_groups.setdefault(key, []).append(idx)

for key, indices in domain_groups.items():
    if 1 < len(indices) < 200:
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                idx1, idx2 = indices[i], indices[j]
                if find(idx1) == find(idx2):
                    continue
                e1, e2 = df['c_email'].iloc[idx1], df['c_email'].iloc[idx2]
                n1, n2 = df['c_name'].iloc[idx1], df['c_name'].iloc[idx2]
                if e1 and e2 and n1 and n2:
                    e_sim = difflib.SequenceMatcher(None, e1, e2).ratio()
                    n_sim = difflib.SequenceMatcher(None, n1, n2).ratio()
                    if e_sim >= 0.85 and n_sim >= 0.75:
                        union(idx1, idx2)

df['group'] = [find(i) for i in range(n)]
res_df = df.sort_values('customer_id').groupby('group', as_index=False).first()

cols = ['customer_id', 'full_name', 'email', 'country', 'registered_at']
res_df = res_df[cols]

os.makedirs(os.path.dirname(output_path), exist_ok=True)
res_df.to_parquet(output_path, index=False)