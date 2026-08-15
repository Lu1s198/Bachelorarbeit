import pandas as pd
import numpy as np
import re
import difflib
from collections import defaultdict

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/anthropic/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/anthropic/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df['customer_id'] = df['customer_id'].astype('int64')
df['full_name'] = df['full_name'].astype(str)
df['email'] = df['email'].astype(str)
df['country'] = df['country'].astype(str)
df['registered_at'] = df['registered_at'].astype(str)

def normalize_email(email):
    e = str(email).strip().lower()
    if '@' in e:
        local, domain = e.split('@', 1)
        local = local.replace('.', '')
        return local + '@' + domain
    return e

titles = {
    'mr', 'mrs', 'ms', 'miss', 'mister', 'mister.', 'dr', 'dr.', 'prof', 'prof.',
    'professor', 'herr', 'frau', 'fraeulein', 'sir', 'madam', 'madame', 'monsieur',
    'mme', 'mlle'
}

def normalize_name(name):
    n = str(name).strip().lower()
    n = re.sub(r'[^a-zA-Zäöüßàâçéèêëîïôûùüÿñ\s]', ' ', n)
    n = re.sub(r'\s+', ' ', n).strip()
    tokens = n.split(' ')
    tokens = [t for t in tokens if t not in titles]
    tokens = [t for t in tokens if len(t) > 1]
    return ' '.join(tokens)

df['email_norm'] = df['email'].apply(normalize_email)
df['name_norm'] = df['full_name'].apply(normalize_name)

df = df.reset_index(drop=True)

parent = {i: i for i in df.index}

def find(x):
    while parent[x] != x:
        x = parent[x]
    return x

def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry:
        parent[rx] = ry

groups_by_email = defaultdict(list)
for idx, key in zip(df.index, df['email_norm']):
    groups_by_email[key].append(idx)

for key, idxs in groups_by_email.items():
    if len(idxs) < 2:
        continue
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            a, b = idxs[i], idxs[j]
            name_a = df.at[a, 'name_norm']
            name_b = df.at[b, 'name_norm']
            if name_a == '' or name_b == '':
                ratio = 0.0
            else:
                ratio = difflib.SequenceMatcher(None, name_a, name_b).ratio()
            if ratio >= 0.6:
                union(a, b)

df['group'] = [find(i) for i in df.index]

min_ids = df.groupby('group')['customer_id'].idxmin()
result = df.loc[min_ids]

result = result[['customer_id', 'full_name', 'email', 'country', 'registered_at']]
result = result.sort_values('customer_id').reset_index(drop=True)

result.to_parquet(output_path, index=False)