import os
import re
import difflib
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r4/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r4/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
    def find(self, i):
        path = []
        while self.parent[i] != i:
            path.append(i)
            i = self.parent[i]
        for node in path:
            self.parent[node] = i
        return i
    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j

TITLES = {'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'herr', 'frau', 'sir', 'madam', 'doktor', 'dipl', 'ing', 'phd'}

def clean_email(email):
    if not isinstance(email, str) or '@' not in email:
        return ""
    email = email.lower().strip()
    parts = email.split('@', 1)
    local = parts[0].replace('.', '')
    return f"{local}@{parts[1]}"

def clean_name(name):
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = re.sub(r'[^a-zäöüß\s]', ' ', name)
    tokens = name.split()
    filtered = [t for t in tokens if t not in TITLES]
    no_initials = [t for t in filtered if len(t) > 1]
    tokens = no_initials if no_initials else filtered
    return " ".join(tokens)

emails_clean = [clean_email(e) for e in df['email']]
names_clean = [clean_name(n) for n in df['full_name']]

n_rows = len(df)
uf = UnionFind(n_rows)

blocks = {}

for idx in range(n_rows):
    e = emails_clean[idx]
    n = names_clean[idx]
    
    keys = set()
    if e:
        keys.add(('e_full', e))
        e_parts = e.split('@', 1)
        keys.add(('e_prefix', e_parts[0][:4], e_parts[1]))
    if n:
        keys.add(('n_full', n))
        words = n.split()
        if len(words) >= 2:
            keys.add(('n_prefix', words[0][:3], words[-1][:3]))
        elif len(words) == 1:
            keys.add(('n_prefix', words[0][:3]))
            
    for k in keys:
        blocks.setdefault(k, []).append(idx)

candidate_pairs = set()
for k, idxs in blocks.items():
    if len(idxs) > 1 and len(idxs) < 500:
        for i in range(len(idxs)):
            for j in range(i + 1, len(idxs)):
                id1, id2 = idxs[i], idxs[j]
                if id1 > id2:
                    id1, id2 = id2, id1
                candidate_pairs.add((id1, id2))

for i, j in candidate_pairs:
    e1, e2 = emails_clean[i], emails_clean[j]
    n1, n2 = names_clean[i], names_clean[j]
    
    if e1 and e2:
        e_sim = 1.0 if e1 == e2 else difflib.SequenceMatcher(None, e1, e2).ratio()
    else:
        e_sim = 0.0
        
    if n1 and n2:
        n_sim = 1.0 if n1 == n2 else difflib.SequenceMatcher(None, n1, n2).ratio()
    else:
        n_sim = 0.0
        
    is_dup = False
    if e_sim == 1.0 and (n_sim >= 0.65 or n1 in n2 or n2 in n1):
        is_dup = True
    elif n_sim == 1.0 and e_sim >= 0.70:
        is_dup = True
    elif e_sim >= 0.80 and n_sim >= 0.80:
        is_dup = True
    elif e_sim >= 0.85 and n_sim >= 0.70:
        is_dup = True
    elif n_sim >= 0.85 and e_sim >= 0.70:
        is_dup = True

    if is_dup:
        uf.union(i, j)

df['_cluster'] = [uf.find(i) for i in range(n_rows)]

df = df.sort_values('customer_id').groupby('_cluster', as_index=False).first()
df = df.drop(columns=['_cluster'])

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)