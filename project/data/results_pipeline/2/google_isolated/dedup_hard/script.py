import os
import re
from collections import defaultdict
from difflib import SequenceMatcher
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

TITLES = {
    'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'sir', 'lady', 'herr', 'frau',
    'doktor', 'professor', 'ing', 'dipl', 'mag', 'phd', 'md'
}

def clean_name(name):
    if not isinstance(name, str):
        return ""
    s = name.lower()
    s = re.sub(r'[^a-z\s]', ' ', s)
    tokens = s.split()
    tokens = [t for t in tokens if t not in TITLES]
    if len(tokens) >= 2:
        tokens_filtered = [t for t in tokens if len(t) > 1]
        if len(tokens_filtered) >= 2:
            tokens = tokens_filtered
    return " ".join(tokens)

def clean_email(email):
    if not isinstance(email, str) or '@' not in email:
        return ""
    email = email.strip().lower()
    parts = email.split('@', 1)
    local = parts[0].replace('.', '')
    domain = parts[1]
    return f"{local}@{domain}"

records = []
for idx, row in df.iterrows():
    c_name = clean_name(row.get('full_name', ''))
    c_email = clean_email(row.get('email', ''))
    records.append({
        'c_name': c_name,
        'c_email': c_email
    })

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

blocks = defaultdict(set)
for idx, rec in enumerate(records):
    if rec['c_email']:
        blocks[('email', rec['c_email'])].add(idx)
    tokens = rec['c_name'].split()
    if tokens:
        first_t = tokens[0]
        last_t = tokens[-1]
        blocks[('name_fl', first_t[0], last_t)].add(idx)
        if len(first_t) >= 3:
            blocks[('name_3l', first_t[:3], last_t)].add(idx)

candidate_pairs = set()
for indices in blocks.values():
    if 1 < len(indices) < 1000:
        idx_list = list(indices)
        for i in range(len(idx_list)):
            for j in range(i + 1, len(idx_list)):
                candidate_pairs.add((min(idx_list[i], idx_list[j]), max(idx_list[i], idx_list[j])))

for i, j in candidate_pairs:
    r1 = records[i]
    r2 = records[j]

    email_exact = (r1['c_email'] == r2['c_email']) and bool(r1['c_email'])
    email_sim = SequenceMatcher(None, r1['c_email'], r2['c_email']).ratio() if (r1['c_email'] and r2['c_email']) else 0.0

    name_exact = (r1['c_name'] == r2['c_name']) and bool(r1['c_name'])
    name_sim = SequenceMatcher(None, r1['c_name'], r2['c_name']).ratio() if (r1['c_name'] and r2['c_name']) else 0.0

    is_match = False
    if email_exact:
        if name_exact or name_sim >= 0.65:
            is_match = True
        else:
            t1 = set(r1['c_name'].split())
            t2 = set(r2['c_name'].split())
            if t1 and t2 and (t1.issubset(t2) or t2.issubset(t1) or len(t1 & t2) / min(len(t1), len(t2)) >= 0.5):
                is_match = True
    elif email_sim >= 0.85:
        if name_exact or name_sim >= 0.75:
            is_match = True

    if is_match:
        union(i, j)

group_map = defaultdict(list)
for i in range(n):
    root = find(i)
    group_map[root].append(i)

keep_indices = []
for root, indices in group_map.items():
    best_idx = min(indices, key=lambda idx: df.iloc[idx]['customer_id'])
    keep_indices.append(best_idx)

result_df = df.iloc[sorted(keep_indices)].copy()

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result_df.to_parquet(output_path, index=False)