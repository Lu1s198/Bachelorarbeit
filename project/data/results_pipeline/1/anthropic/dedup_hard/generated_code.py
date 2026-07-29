import pandas as pd
import numpy as np
from difflib import SequenceMatcher

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)
df = df.reset_index(drop=True)

# Ensure customer_id is a consistent type (string) to avoid mismatches later
if 'customer_id' in df.columns:
    df['customer_id'] = df['customer_id'].astype(str)

def normalize_email(email):
    if pd.isna(email):
        return None
    e = str(email).strip().lower()
    if '@' in e:
        local, domain = e.split('@', 1)
        local = local.replace('.', '')
        return local + '@' + domain
    return e

def normalize_name(name):
    if pd.isna(name):
        return None
    n = str(name).strip().lower()
    n = n.replace('.', '')
    n = ' '.join(n.split())
    parts = n.split(' ')
    # Remove single-letter middle initials when there are more than 2 parts
    if len(parts) > 2:
        parts = [p for p in parts if len(p) > 1]
    return ' '.join(parts)

df['norm_email'] = df['email'].apply(normalize_email) if 'email' in df.columns else None
df['norm_name'] = df['full_name'].apply(normalize_name) if 'full_name' in df.columns else None

n = len(df)

class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self.parent[rx] = ry

uf = UnionFind(n)

# 1) Union rows with identical normalized email
email_groups = {}
for idx, key in enumerate(df['norm_email']):
    if key is None or (isinstance(key, float) and np.isnan(key)):
        continue
    email_groups.setdefault(key, []).append(idx)

for idxs in email_groups.values():
    if len(idxs) > 1:
        first = idxs[0]
        for other in idxs[1:]:
            uf.union(first, other)

# 2) Union rows with highly similar normalized name (fuzzy match for typos, casing, initials)
name_values = df['norm_name'].tolist()

# Group by first letter + length bucket to reduce comparisons
buckets = {}
for idx, name in enumerate(name_values):
    if not name:
        continue
    key = (name[0], len(name) // 3)
    buckets.setdefault(key, []).append(idx)

SIMILARITY_THRESHOLD = 0.88

compared = set()
for key, idxs in buckets.items():
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            a, b = idxs[i], idxs[j]
            if uf.find(a) == uf.find(b):
                continue
            pair_key = (min(a, b), max(a, b))
            if pair_key in compared:
                continue
            compared.add(pair_key)
            na, nb = name_values[a], name_values[b]
            if na and nb:
                ratio = SequenceMatcher(None, na, nb).ratio()
                if ratio >= SIMILARITY_THRESHOLD:
                    uf.union(a, b)

# Also compare across adjacent length buckets to catch off-by-one bucket boundary issues
bucket_keys = list(buckets.keys())
for k1 in bucket_keys:
    letter, bucket_num = k1
    neighbor_key = (letter, bucket_num + 1)
    if neighbor_key in buckets:
        idxs1 = buckets[k1]
        idxs2 = buckets[neighbor_key]
        for a in idxs1:
            for b in idxs2:
                if uf.find(a) == uf.find(b):
                    continue
                pair_key = (min(a, b), max(a, b))
                if pair_key in compared:
                    continue
                compared.add(pair_key)
                na, nb = name_values[a], name_values[b]
                if na and nb:
                    ratio = SequenceMatcher(None, na, nb).ratio()
                    if ratio >= SIMILARITY_THRESHOLD:
                        uf.union(a, b)

df['cluster'] = [uf.find(i) for i in range(n)]

# Determine completeness (non-null count across original columns)
original_cols = [c for c in df.columns if c not in ('norm_email', 'norm_name', 'cluster')]
df['completeness'] = df[original_cols].notna().sum(axis=1)

df_sorted = df.sort_values('completeness', ascending=False)
result = df_sorted.groupby('cluster', as_index=False).first()

result = result[original_cols]

required_cols = ['customer_id', 'full_name', 'email', 'country', 'registered_at']
other_cols = [c for c in result.columns if c not in required_cols]
final_cols = [c for c in required_cols if c in result.columns] + other_cols
result = result[final_cols]

result.to_parquet(output_path, index=False)