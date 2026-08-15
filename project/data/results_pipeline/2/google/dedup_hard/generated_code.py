import os
import re
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

def clean_name(name):
    if not isinstance(name, str):
        return ""
    s = name.lower()
    titles = {'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'sir', 'lady', 'lord', 'herr', 'frau', 'dipl', 'ing', 'phd', 'md'}
    s = re.sub(r'[^\w\s]', ' ', s)
    words = s.split()
    words = [w for w in words if w not in titles]
    words = [w for w in words if len(w) > 1]
    return " ".join(words)

def clean_email(email):
    if not isinstance(email, str):
        return ""
    s = email.lower().strip()
    if '@' not in s:
        return s
    local, domain = s.split('@', 1)
    local = local.split('+')[0]
    local = local.replace('.', '')
    domain_fixes = {
        'googlemail.com': 'gmail.com',
        'gmial.com': 'gmail.com',
        'gmai.com': 'gmail.com',
        'yaho.com': 'yahoo.com',
        'yahoo.co.uk': 'yahoo.com',
        'hotmial.com': 'hotmail.com',
        'outlok.com': 'outlook.com'
    }
    domain = domain_fixes.get(domain, domain)
    return f"{local}@{domain}"

def levenshtein(s1, s2):
    if s1 == s2:
        return 0
    len1, len2 = len(s1), len(s2)
    if abs(len1 - len2) > 3:
        return 999
    if len1 < len2:
        s1, s2 = s2, s1
        len1, len2 = len2, len1
    if len2 == 0:
        return len1
    previous_row = list(range(len2 + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1] + [0] * len2
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row[j + 1] = min(insertions, deletions, substitutions)
        previous_row = current_row
    return previous_row[-1]

def is_match(n1, e1, n2, e2):
    if e1 == e2:
        email_ok = True
    else:
        e_dist = levenshtein(e1, e2)
        email_ok = e_dist <= 2

    if not email_ok:
        return False

    if n1 == n2:
        name_ok = True
    else:
        n_dist = levenshtein(n1, n2)
        max_len = max(len(n1), len(n2), 1)
        name_ok = (n_dist <= 2) or (n_dist / max_len <= 0.25)

    return name_ok

df['norm_name'] = df['full_name'].apply(clean_name)
df['norm_email'] = df['email'].apply(clean_email)

df = df.sort_values('customer_id').reset_index(drop=True)
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
        if root_i < root_j:
            parent[root_j] = root_i
        else:
            parent[root_i] = root_j

norm_names = df['norm_name'].tolist()
norm_emails = df['norm_email'].tolist()

for i in range(n):
    n1, e1 = norm_names[i], norm_emails[i]
    for j in range(i + 1, n):
        n2, e2 = norm_names[j], norm_emails[j]
        if is_match(n1, e1, n2, e2):
            union(i, j)

df['component'] = [find(i) for i in range(n)]

res = df.groupby('component', as_index=False).first()
res = res[['customer_id', 'full_name', 'email', 'country', 'registered_at']]

os.makedirs(os.path.dirname(output_path), exist_ok=True)
res.to_parquet(output_path, index=False)