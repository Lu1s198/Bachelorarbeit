import os
import re
from difflib import SequenceMatcher
from collections import defaultdict
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google_isolated/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

def clean_email(e):
    if not isinstance(e, str):
        return ""
    e = e.lower().strip()
    if "@" not in e:
        return e
    local, domain = e.rsplit("@", 1)
    local = local.replace(".", "")
    return f"{local}@{domain}"

def clean_name(n):
    if not isinstance(n, str):
        return ""
    n = n.lower()
    titles = r'\b(mr|mrs|ms|miss|dr|prof|sir|lady|herr|frau|dipl|ing|phd|md)\b'
    n = re.sub(titles, ' ', n)
    n = re.sub(r'[^a-z\s]', ' ', n)
    words = [w for w in n.split() if len(w) > 1]
    words.sort()
    return " ".join(words)

df['c_email'] = df['email'].apply(clean_email)
df['c_name'] = df['full_name'].apply(clean_name)

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

blocks = defaultdict(list)
for idx, row in enumerate(df.itertuples()):
    e = row.c_email
    if "@" in e:
        domain = e.split("@")[1]
    else:
        domain = e
    blocks[domain].append(idx)

for domain, indices in blocks.items():
    m = len(indices)
    for i in range(m):
        idx_i = indices[i]
        e1, n1 = df.at[idx_i, 'c_email'], df.at[idx_i, 'c_name']
        for j in range(i + 1, m):
            idx_j = indices[j]
            e2, n2 = df.at[idx_j, 'c_email'], df.at[idx_j, 'c_name']
            
            if e1 == e2:
                email_match = True
            else:
                email_match = SequenceMatcher(None, e1, e2).ratio() >= 0.85
                
            if not email_match:
                continue
                
            if not n1 or not n2 or n1 == n2:
                name_match = True
            else:
                name_match = SequenceMatcher(None, n1, n2).ratio() >= 0.70
                
            if name_match:
                union(idx_i, idx_j)

df['group'] = [find(i) for i in range(n)]

df_res = df.sort_values('customer_id').groupby('group', as_index=False).first()
out_cols = ['customer_id', 'full_name', 'email', 'country', 'registered_at']
df_res = df_res[out_cols]

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_res.to_parquet(output_path, index=False)