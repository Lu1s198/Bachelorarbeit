import os
import re
from difflib import SequenceMatcher
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r3/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r3/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

TITLES = {
    'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'doctor', 'professor', 'sir',
    'madam', 'phd', 'md', 'rev', 'hon', 'ing', 'dipl'
}

def normalize_email(email):
    if not isinstance(email, str) or '@' not in email:
        return ''
    parts = email.lower().strip().split('@', 1)
    user = parts[0].replace('.', '')
    if '+' in user:
        user = user.split('+')[0]
    domain = parts[1]
    return f"{user}@{domain}"

def normalize_name(name):
    if not isinstance(name, str):
        return ''
    name = name.lower()
    name = re.sub(r'[^a-z\s]', ' ', name)
    tokens = name.split()
    tokens = [t for t in tokens if t not in TITLES]
    filtered = []
    for t in tokens:
        if len(t) == 1 and len(tokens) > 1:
            continue
        filtered.append(t)
    return ' '.join(filtered)

df['clean_email'] = df['email'].apply(normalize_email)
df['clean_name'] = df['full_name'].apply(normalize_name)

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

candidate_pairs = set()

email_map = {}
for idx, em in enumerate(df['clean_email']):
    if em:
        email_map.setdefault(em, []).append(idx)

for idxs in email_map.values():
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            candidate_pairs.add((idxs[i], idxs[j]))

token_map = {}
for idx, name in enumerate(df['clean_name']):
    for token in set(name.split()):
        if len(token) >= 3:
            token_map.setdefault(token, []).append(idx)

for idxs in token_map.values():
    if len(idxs) <= 50:
        for i in range(len(idxs)):
            for j in range(i + 1, len(idxs)):
                pair = (min(idxs[i], idxs[j]), max(idxs[i], idxs[j]))
                candidate_pairs.add(pair)

clean_emails = df['clean_email'].tolist()
clean_names = df['clean_name'].tolist()

for i, j in candidate_pairs:
    e1, e2 = clean_emails[i], clean_emails[j]
    n1, n2 = clean_names[i], clean_names[j]

    if not e1 or not e2 or not n1 or not n2:
        continue

    e_exact = (e1 == e2)
    e_sim = 1.0 if e_exact else SequenceMatcher(None, e1, e2).ratio()

    n_exact = (n1 == n2)
    n_sim = 1.0 if n_exact else SequenceMatcher(None, n1, n2).ratio()

    t1 = set(n1.split())
    t2 = set(n2.split())
    common_tokens = t1 & t2

    e_match = e_exact or (e_sim >= 0.85)
    n_match = n_exact or (n_sim >= 0.75) or (n_sim >= 0.65 and len(common_tokens) >= 1)

    if e_match and n_match:
        union(i, j)

df['cluster'] = [find(i) for i in range(n)]

idx_to_keep = df.groupby('cluster')['customer_id'].idxmin()
result_df = df.loc[idx_to_keep, ['customer_id', 'full_name', 'email', 'country', 'registered_at']].sort_values('customer_id')

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result_df.to_parquet(output_path, index=False)