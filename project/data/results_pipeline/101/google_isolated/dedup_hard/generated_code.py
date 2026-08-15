import os
import re
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/_reference/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google_isolated/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)
df['customer_id'] = df['customer_id'].astype('int64')

TITLES = {
    'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'sir', 'lady', 'herr', 'frau', 
    'doktor', 'professor', 'ing', 'dipl', 'mme', 'mlle', 'madam'
}

def normalize_email(email):
    if not isinstance(email, str) or '@' not in email:
        return ""
    parts = email.strip().lower().split('@')
    user = parts[0].replace('.', '')
    domain = '@'.join(parts[1:])
    return f"{user}@{domain}"

def clean_name(name):
    if not isinstance(name, str):
        return ""
    text = re.sub(r'[^a-zA-Z\u00C0-\u024F]', ' ', name.lower())
    tokens = text.split()
    tokens = [t for t in tokens if t not in TITLES]
    tokens_no_initials = [t for t in tokens if len(t) > 1]
    if tokens_no_initials:
        tokens = tokens_no_initials
    return " ".join(tokens)

def get_sorted_name(cname):
    tokens = cname.split()
    tokens.sort()
    return " ".join(tokens)

def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def names_are_similar(n1, n2):
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True
    
    sn1 = get_sorted_name(n1)
    sn2 = get_sorted_name(n2)
    if sn1 == sn2:
        return True
        
    dist = min(levenshtein(n1, n2), levenshtein(sn1, sn2))
    max_len = max(len(n1), len(n2))
    if max_len == 0:
        return False
        
    if dist <= 2 or (dist / max_len) <= 0.25:
        return True
    return False

def emails_are_similar(e1, e2):
    if not e1 or not e2:
        return False
    if e1 == e2:
        return True
    dist = levenshtein(e1, e2)
    return dist <= 2

df['norm_email'] = df['email'].apply(normalize_email)
df['clean_name'] = df['full_name'].apply(clean_name)
df['sorted_name'] = df['clean_name'].apply(get_sorted_name)

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

blocks = {}
for idx, row in df.iterrows():
    keys = set()
    if row['norm_email']:
        keys.add(('email', row['norm_email']))
    if row['clean_name']:
        keys.add(('name', row['clean_name']))
    if row['sorted_name']:
        keys.add(('sname', row['sorted_name']))
    
    for key in keys:
        blocks.setdefault(key, []).append(idx)

compared_pairs = set()

for key, indices in blocks.items():
    if len(indices) < 2:
        continue
    for i_idx in range(len(indices)):
        for j_idx in range(i_idx + 1, len(indices)):
            u = indices[i_idx]
            v = indices[j_idx]
            pair = (min(u, v), max(u, v))
            if pair in compared_pairs:
                continue
            compared_pairs.add(pair)
            
            row_u = df.iloc[u]
            row_v = df.iloc[v]
            
            e_match = emails_are_similar(row_u['norm_email'], row_v['norm_email'])
            n_match = names_are_similar(row_u['clean_name'], row_v['clean_name'])
            
            if e_match and n_match:
                union(u, v)

df['cluster'] = [find(i) for i in range(n)]

result_df = (
    df.sort_values('customer_id')
    .groupby('cluster', as_index=False)
    .first()
)

output_cols = ['customer_id', 'full_name', 'email', 'country', 'registered_at']
result_df = result_df[output_cols]

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result_df.to_parquet(output_path, index=False)