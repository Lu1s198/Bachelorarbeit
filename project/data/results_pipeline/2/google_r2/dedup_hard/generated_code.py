import os
import re
import pandas as pd


def normalize_email(email):
    if not isinstance(email, str) or "@" not in email:
        return ""
    parts = email.lower().strip().split("@")
    local_part = parts[0].replace(".", "")
    domain = "@".join(parts[1:])
    return f"{local_part}@{domain}"


def clean_name_str(name):
    if not isinstance(name, str):
        return ""
    name = name.lower()
    titles = [
        r"\bdr\.?\b",
        r"\bprof\.?\b",
        r"\bmr\.?\b",
        r"\bmrs\.?\b",
        r"\bms\.?\b",
        r"\bherr\b",
        r"\bfrau\b",
        r"\bsir\b",
        r"\bmadam\b",
    ]
    for t in titles:
        name = re.sub(t, " ", name)
    name = re.sub(r"[^\w\s]", "", name)
    tokens = name.split()
    tokens = [t for t in tokens if len(t) > 1]
    return " ".join(tokens)


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


def levenshtein_ratio(s1, s2):
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    max_len = max(len(s1), len(s2))
    return 1.0 - (levenshtein_distance(s1, s2) / max_len)


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


def is_same_person(r1, r2):
    n1, e1 = r1["clean_name"], r1["norm_email"]
    n2, e2 = r2["clean_name"], r2["norm_email"]

    exact_email = e1 == e2 and e1 != ""
    exact_name = n1 == n2 and n1 != ""

    e_ratio = levenshtein_ratio(e1, e2) if (e1 and e2) else 0.0
    n_ratio = levenshtein_ratio(n1, n2) if (n1 and n2) else 0.0

    t1 = set(n1.split())
    t2 = set(n2.split())
    token_overlap = len(t1.intersection(t2)) > 0 if (t1 and t2) else False

    if exact_email and (exact_name or n_ratio >= 0.6 or token_overlap):
        return True
    if exact_name and (exact_email or e_ratio >= 0.75):
        return True
    if e_ratio >= 0.85 and (n_ratio >= 0.65 or token_overlap):
        return True
    if n_ratio >= 0.85 and e_ratio >= 0.7:
        return True

    return False


def main():
    input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r2/dedup_medium/output.parquet"
    output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r2/dedup_hard/output.parquet"

    df = pd.read_parquet(input_path)

    df["norm_email"] = df["email"].apply(normalize_email)
    df["clean_name"] = df["full_name"].apply(clean_name_str)

    n = len(df)
    uf = UnionFind(n)

    blocks = {}
    for idx, row in df.iterrows():
        keys = set()
        if row["norm_email"]:
            keys.add(("email", row["norm_email"]))
        tokens = row["clean_name"].split()
        for tok in tokens:
            if len(tok) >= 3:
                keys.add(("token", tok))

        for k in keys:
            if k not in blocks:
                blocks[k] = []
            blocks[k].append(idx)

    pairs_to_check = set()
    for k, indices in blocks.items():
        if len(indices) < 2:
            continue
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                idx1, idx2 = indices[i], indices[j]
                if idx1 > idx2:
                    idx1, idx2 = idx2, idx1
                pairs_to_check.add((idx1, idx2))

    records = df[["clean_name", "norm_email"]].to_dict("records")

    for i, j in pairs_to_check:
        if uf.find(i) == uf.find(j):
            continue
        if is_same_person(records[i], records[j]):
            uf.union(i, j)

    df["group_id"] = [uf.find(i) for i in range(n)]

    df_sorted = df.sort_values(by="customer_id", ascending=True)
    df_dedup = df_sorted.drop_duplicates(subset=["group_id"], keep="first")

    result_cols = ["customer_id", "full_name", "email", "country", "registered_at"]
    out_df = df_dedup[result_cols]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out_df.to_parquet(output_path, index=False)


if __name__ == "__main__":
    main()