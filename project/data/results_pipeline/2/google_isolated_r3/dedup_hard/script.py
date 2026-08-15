import os
import re
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r3/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

TITLES = {'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'sir', 'madam', 'herr', 'frau', 'doktor', 'professor', 'ing', 'dipl'}

def normalize_name(val):
    if not val or pd.isna(val):
        return ""
    s = str(val).lower()
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    tokens = s.split()
    tokens = [t for t in tokens if t not in TITLES]
    multi = [t for t in tokens if len(t) > 1]
    if len(multi) >= 2:
        tokens = multi
    return " ".join(tokens)

def normalize_email(val):
    if not val or pd.isna(val):
        return ""
    s = str(val).lower().strip()
    if '@' in s:
        local, domain = s.rsplit('@', 1)
        if '+' in local:
            local = local.split('+')[0]
        local = local.replace('.', '')
        return local + '@' + domain
    return s.replace('.', '')

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def is_name_similar(n1, n2):
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True
    dist = levenshtein_distance(n1, n2)
    max_len = max(len(n1), len(n2))
    return dist <= 2 and (dist / max_len <= 0.25)

def is_email_similar(e1, e2):
    if not e1 or not e2:
        return False
    if e1 == e2:
        return True
    dist = levenshtein_distance(e1, e2)
    max_len = max(len(e1), len(e2))
    return dist <= 2 and (dist / max_len <= 0.20)

norm_names = [normalize_name(n) for n in df['full_name']]
norm_emails = [normalize_email(e) for e in df['email']]

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

for i in range(n):
    for j in range(i + 1, n):
        if is_name_similar(norm_names[i], norm_names[j]) and is_email_similar(norm_emails[i], norm_emails[j]):
            union(i, j)

df['_comp'] = [find(i) for i in range(n)]

df_result = df.sort_values('customer_id').groupby('_comp', as_index=False).first()
df_result = df_result.drop(columns=['_comp'])

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_result.to_parquet(output_path, index=False)