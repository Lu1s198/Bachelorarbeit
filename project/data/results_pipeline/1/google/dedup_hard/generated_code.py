import difflib
import os
import re
from collections import defaultdict
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)


def normalize_email(e):
    if not isinstance(e, str) or not e or pd.isna(e):
        return ""
    e = e.lower().strip()
    if "@" in e:
        local, domain = e.split("@", 1)
        local = local.replace(".", "")
        return f"{local}@{domain}"
    return e


def normalize_name(n):
    if not isinstance(n, str) or not n or pd.isna(n):
        return ""
    n = n.lower().strip()
    n = re.sub(r"[^\w\s]", "", n)
    tokens = n.split()
    tokens = [t for t in tokens if len(t) > 1]
    return " ".join(tokens)


def levenshtein_similarity(s1, s2):
    if not s1 or not s2:
        return 0.0
    return difflib.SequenceMatcher(None, s1, s2).ratio()


norm_emails = [
    normalize_email(e)
    for e in (df["email"] if "email" in df.columns else [None] * len(df))
]
norm_names = [
    normalize_name(n)
    for n in (
        df["full_name"] if "full_name" in df.columns else [None] * len(df)
    )
]
df_countries = [
    str(c).lower().strip() if pd.notna(c) else ""
    for c in (df["country"] if "country" in df.columns else [None] * len(df))
]


class UnionFind:

    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, i):
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j


n = len(df)
uf = UnionFind(n)

email_groups = defaultdict(list)
for idx, em in enumerate(norm_emails):
    if em:
        email_groups[em].append(idx)
for idxs in email_groups.values():
    for i in range(1, len(idxs)):
        uf.union(idxs[0], idxs[i])

name_groups = defaultdict(list)
for idx, nm in enumerate(norm_names):
    if nm:
        name_groups[nm].append(idx)
for idxs in name_groups.values():
    for i in range(1, len(idxs)):
        uf.union(idxs[0], idxs[i])

blocks = defaultdict(list)
for i in range(n):
    nm = norm_names[i]
    em = norm_emails[i]
    if len(nm) >= 2:
        blocks[f"n_{nm[:2]}"].append(i)
    if len(em) >= 2:
        blocks[f"e_{em[:2]}"].append(i)

candidate_pairs = set()
for indices in blocks.values():
    m = len(indices)
    for i in range(m):
        for j in range(i + 1, m):
            idx1, idx2 = indices[i], indices[j]
            if idx1 > idx2:
                idx1, idx2 = idx2, idx1
            candidate_pairs.add((idx1, idx2))

for idx1, idx2 in candidate_pairs:
    if uf.find(idx1) == uf.find(idx2):
        continue

    e1, e2 = norm_emails[idx1], norm_emails[idx2]
    n1, n2 = norm_names[idx1], norm_names[idx2]

    e_sim = levenshtein_similarity(e1, e2) if (e1 and e2) else 0.0
    n_sim = levenshtein_similarity(n1, n2) if (n1 and n2) else 0.0

    c1, c2 = df_countries[idx1], df_countries[idx2]
    same_country = (c1 == c2) if (c1 and c2) else False

    if (e_sim >= 0.85 and n_sim >= 0.70) or (
        n_sim >= 0.80 and (e_sim >= 0.70 or same_country)
    ):
        uf.union(idx1, idx2)

scores = []
for idx in range(n):
    row = df.iloc[idx]
    score = 0
    for col in df.columns:
        val = row[col]
        if pd.notna(val) and val is not None:
            s_val = str(val).strip()
            if s_val and s_val.lower() != "nan":
                score += 100
                score += len(s_val)
    scores.append(score)

clusters = defaultdict(list)
for idx in range(n):
    root = uf.find(idx)
    clusters[root].append(idx)

keep_indices = []
for root, members in clusters.items():
    best_idx = max(members, key=lambda i: (scores[i], -i))
    keep_indices.append(best_idx)

result_df = df.iloc[keep_indices].copy()

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result_df.to_parquet(output_path, index=False)