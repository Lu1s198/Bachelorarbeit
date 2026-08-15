import pandas as pd
import numpy as np
import re
from difflib import SequenceMatcher

INPUT_PATH = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r3/dedup_medium/output.parquet"
OUTPUT_PATH = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r3/dedup_hard/output.parquet"

df = pd.read_parquet(INPUT_PATH)

df['customer_id'] = df['customer_id'].astype('int64')
df['full_name'] = df['full_name'].astype(str)
df['email'] = df['email'].astype(str)
df['country'] = df['country'].astype(str)
df['registered_at'] = df['registered_at'].astype(str)

TITLES = {
    'dr', 'dr.', 'mr', 'mr.', 'mrs', 'mrs.', 'ms', 'ms.', 'miss',
    'herr', 'frau', 'prof', 'prof.', 'mag', 'mag.', 'ing', 'ing.',
    'sir', 'madam', 'jr', 'jr.', 'sr', 'sr.'
}


def normalize_name(name):
    if pd.isna(name):
        return ''
    name = str(name).lower().strip()
    name = re.sub(r'[^a-zäöüßàáâãåéèêëíìîïóòôõúùûüñç\s]', ' ', name)
    tokens = name.split()
    tokens = [t for t in tokens if t not in TITLES]
    # remove single-letter tokens (middle initials)
    tokens = [t for t in tokens if len(t) > 1]
    tokens = sorted(tokens)
    return ' '.join(tokens)


def normalize_email(email):
    if pd.isna(email):
        return ''
    email = str(email).lower().strip()
    if '@' in email:
        local, domain = email.split('@', 1)
        local = local.replace('.', '')
        return local + '@' + domain
    return email


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


def name_similarity(a, b):
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


groups = {}
for idx, key in enumerate(df['norm_email'].tolist()):
    groups.setdefault(key, []).append(idx)

NAME_THRESHOLD = 0.82

for key, idxs in groups.items():
    if len(idxs) < 2:
        continue
    names = df['norm_name'].iloc[idxs].tolist()
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            if name_similarity(names[i], names[j]) >= NAME_THRESHOLD:
                union(idxs[i], idxs[j])

name_groups = {}
for idx, key in enumerate(df['norm_name'].tolist()):
    if key == '':
        continue
    name_groups.setdefault(key, []).append(idx)

for key, idxs in name_groups.items():
    if len(idxs) < 2:
        continue
    emails = df['norm_email'].iloc[idxs].tolist()
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            if emails[i] and emails[j] and emails[i] == emails[j]:
                union(idxs[i], idxs[j])

df['group'] = [find(i) for i in range(n)]

df_sorted = df.sort_values(['group', 'customer_id'])
result = df_sorted.drop_duplicates(subset='group', keep='first')

result = result[['customer_id', 'full_name', 'email', 'country', 'registered_at']].sort_values('customer_id').reset_index(drop=True)

result.to_parquet(OUTPUT_PATH, index=False)