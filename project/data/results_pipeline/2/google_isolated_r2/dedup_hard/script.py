import os
from collections import defaultdict
import re
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r2/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

TITLES = {
    "mr",
    "mrs",
    "ms",
    "miss",
    "dr",
    "prof",
    "herr",
    "frau",
    "doktor",
    "professor",
    "sir",
    "madam",
    "lady",
    "lord",
    "ing",
    "dipl",
    "phd",
}


def clean_name(name):
    if not isinstance(name, str):
        return ""
    s = name.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    tokens = s.split()
    filtered = [t for t in tokens if t not in TITLES and len(t) > 1]
    return " ".join(filtered)


def clean_email(email):
    if not isinstance(email, str):
        return ""
    email = email.lower().strip()
    if "@" in email:
        local, domain = email.rsplit("@", 1)
        local = local.replace(".", "")
        return f"{local}@{domain}"
    return email


def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
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


def similarity_ratio(s1, s2):
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    max_len = max(len(s1), len(s2))
    return 1.0 - (levenshtein_distance(s1, s2) / max_len)


class UnionFind:

    def __init__(self, size):
        self.parent = list(range(size))

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


cleaned_emails = [clean_email(e) for e in df["email"]]
cleaned_names = [clean_name(n) for n in df["full_name"]]

n_records = len(df)
uf = UnionFind(n_records)

blocks = defaultdict(set)
for idx in range(n_records):
    c_email = cleaned_emails[idx]
    c_name = cleaned_names[idx]

    if c_email:
        blocks[f"e:{c_email}"].add(idx)
        if "@" in c_email:
            local = c_email.split("@")[0]
            if len(local) >= 3:
                blocks[f"eprefix:{local[:4]}"].add(idx)

    if c_name:
        blocks[f"n:{c_name}"].add(idx)
        tokens = c_name.split()
        if tokens:
            first = tokens[0][:3]
            last = tokens[-1][:3]
            blocks[f"nprefix:{first}_{last}"].add(idx)

candidate_pairs = set()
for indices in blocks.values():
    indices_list = list(indices)
    for i in range(len(indices_list)):
        for j in range(i + 1, len(indices_list)):
            idx1, idx2 = indices_list[i], indices_list[j]
            if idx1 > idx2:
                idx1, idx2 = idx2, idx1
            candidate_pairs.add((idx1, idx2))


def is_dup(i, j):
    e1, e2 = cleaned_emails[i], cleaned_emails[j]
    n1, n2 = cleaned_names[i], cleaned_names[j]

    e_sim = similarity_ratio(e1, e2)
    n_sim = similarity_ratio(n1, n2)

    if e1 and e1 == e2:
        if n1 == n2 or n_sim >= 0.65:
            return True
        t1, t2 = set(n1.split()), set(n2.split())
        if t1 and t2 and (t1.issubset(t2) or t2.issubset(t1)):
            return True

    if n1 and n1 == n2:
        if e_sim >= 0.70:
            return True

    if e_sim >= 0.85 and n_sim >= 0.75:
        return True

    return False


for i, j in candidate_pairs:
    if uf.find(i) != uf.find(j):
        if is_dup(i, j):
            uf.union(i, j)

df["_cluster"] = [uf.find(i) for i in range(n_records)]

df_sorted = df.sort_values(by="customer_id", ascending=True)
df_dedup = df_sorted.drop_duplicates(subset=["_cluster"], keep="first").drop(
    columns=["_cluster"]
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_dedup.to_parquet(output_path, index=False)