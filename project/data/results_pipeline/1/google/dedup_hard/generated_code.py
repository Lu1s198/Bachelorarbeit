import os
import re
import difflib
import pandas as pd

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

def clean_name(name):
    if not isinstance(name, str):
        return ""
    s = re.sub(r'[^a-zA-Z0-9\s]', ' ', name.lower())
    words = s.split()
    titles = {'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'herr', 'frau', 'sir', 'lady', 'rev', 'phd', 'ing', 'dipl'}
    words = [w for w in words if w not in titles]
    if len(words) > 2:
        words = [w for w in words if len(w) > 1]
    return " ".join(words)

def normalize_email(email):
    if not isinstance(email, str):
        return ""
    email = email.lower().strip()
    if '@' in email:
        local, domain = email.split('@', 1)
        local = local.replace('.', '').split('+')[0]
        return f"{local}@{domain}"
    return email

def is_duplicate(n1, e1, n2, e2):
    if abs(len(e1) - len(e2)) > 6 or abs(len(n1) - len(n2)) > 6:
        return False

    if e1 == e2:
        email_sim = 1.0
    else:
        email_sim = difflib.SequenceMatcher(None, e1, e2).ratio()

    if email_sim < 0.82:
        return False

    if n1 == n2:
        name_sim = 1.0
    else:
        name_sim = difflib.SequenceMatcher(None, n1, n2).ratio()

    return name_sim >= 0.75

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df['clean_name'] = df['full_name'].apply(clean_name)
df['clean_email'] = df['email'].apply(normalize_email)

n = len(df)
uf = UnionFind(n)

data = list(zip(df['clean_name'].tolist(), df['clean_email'].tolist()))

for i in range(n):
    n1, e1 = data[i]
    for j in range(i + 1, n):
        n2, e2 = data[j]
        if is_duplicate(n1, e1, n2, e2):
            uf.union(i, j)

df['group'] = [uf.find(i) for i in range(n)]

result_df = df.sort_values('customer_id').groupby('group', as_index=False).first()
result_df = result_df[['customer_id', 'full_name', 'email', 'country', 'registered_at']]

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result_df.to_parquet(output_path, index=False)