import os
import re
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/dedup_hard/output.parquet"

TITLES = {
    "mr",
    "mrs",
    "ms",
    "miss",
    "dr",
    "prof",
    "professor",
    "doctor",
    "herr",
    "frau",
    "sir",
    "madam",
    "dipl",
    "ing",
    "phd",
    "md",
    "rev",
    "hon",
}


def normalize_email(email):
    if not isinstance(email, str):
        return ""
    email = email.strip().lower()
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    local = local.replace(".", "").split("+")[0]
    return f"{local}@{domain}"


def clean_name(name):
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    tokens = name.split()
    filtered = [t for t in tokens if t not in TITLES]
    tokens_no_initials = [t for t in filtered if len(t) > 1]
    if tokens_no_initials:
        return " ".join(tokens_no_initials)
    return " ".join(filtered)


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


def email_similar(e1, e2):
    if not e1 or not e2:
        return False
    if e1 == e2:
        return True
    p1 = e1.split("@")
    p2 = e2.split("@")
    if len(p1) != 2 or len(p2) != 2:
        return False
    l1, d1 = p1
    l2, d2 = p2

    l_dist = levenshtein_distance(l1, l2)
    l_max = max(len(l1), len(l2))
    l_sim = (
        (l_dist <= 2 or (l_dist / l_max <= 0.25)) if l_max > 0 else False
    ) or l1 == l2

    d_dist = levenshtein_distance(d1, d2)
    d_sim = d1 == d2 or (d_dist <= 1 and len(d1) > 4)

    return l_sim and d_sim


def name_similar(n1, n2):
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True

    t1 = [t for t in n1.split() if len(t) > 1]
    t2 = [t for t in n2.split() if len(t) > 1]

    if not t1 or not t2:
        return levenshtein_distance(n1, n2) <= 2

    if set(t1) == set(t2):
        return True

    matches = 0
    used_t2 = set()
    for tok1 in t1:
        best_dist = 999
        best_j = -1
        for j, tok2 in enumerate(t2):
            if j in used_t2:
                continue
            d = levenshtein_distance(tok1, tok2)
            if d < best_dist:
                best_dist = d
                best_j = j
        if best_j != -1 and (
            best_dist <= 1
            or (best_dist <= 2 and max(len(tok1), len(t2[best_j])) >= 5)
        ):
            matches += 1
            used_t2.add(best_j)

    min_tokens = min(len(t1), len(t2))
    return matches >= min_tokens


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


df = pd.read_parquet(input_path)

norm_e = [normalize_email(e) for e in df["email"]]
clean_n = [clean_name(n) for n in df["full_name"]]

n_rows = len(df)
candidate_pairs = set()

blocks = {}
for i in range(n_rows):
    e = norm_e[i]
    cn = clean_n[i]

    keys = set()
    if "@" in e:
        local, domain = e.split("@", 1)
        if len(local) >= 3:
            keys.add(f"e_loc:{local[:3]}")
        keys.add(f"e_full:{local}")
    for tok in cn.split():
        if len(tok) >= 3:
            keys.add(f"n_tok:{tok[:3]}")

    for k in keys:
        if k not in blocks:
            blocks[k] = []
        blocks[k].append(i)

for k, indices in blocks.items():
    if len(indices) < 2 or len(indices) > 500:
        continue
    for i in range(len(indices)):
        for j in range(i + 1, len(indices)):
            idx1, idx2 = indices[i], indices[j]
            if idx1 > idx2:
                idx1, idx2 = idx2, idx1
            candidate_pairs.add((idx1, idx2))

uf = UnionFind(n_rows)

for i, j in candidate_pairs:
    if email_similar(norm_e[i], norm_e[j]) and name_similar(
        clean_n[i], clean_n[j]
    ):
        uf.union(i, j)

df["_cluster_group"] = [uf.find(i) for i in range(n_rows)]

res_df = (
    df.sort_values(by=["_cluster_group", "customer_id"])
    .groupby("_cluster_group", as_index=False)
    .first()
)
res_df = res_df.drop(columns=["_cluster_group"])

os.makedirs(os.path.dirname(output_path), exist_ok=True)
res_df.to_parquet(output_path, index=False)