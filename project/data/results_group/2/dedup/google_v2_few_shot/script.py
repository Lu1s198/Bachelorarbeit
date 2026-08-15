from difflib import SequenceMatcher
import os
import re
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
if not os.path.exists(input_path):
    input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/input.parquet"
    if not os.path.exists(input_path):
        input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/output.parquet"

output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/google_v2_few_shot/output.parquet"

df = pd.read_parquet(input_path)

# 1. Exact duplicates
df = df.drop_duplicates(keep="first")

# 2. Duplicate email - keep most recent registered_at
df["registered_at_dt"] = pd.to_datetime(df["registered_at"], errors="coerce")
df = df.sort_values(
    by=["registered_at_dt", "customer_id"], ascending=[False, True]
)
df = df.drop_duplicates(subset=["email"], keep="first")
df = df.drop(columns=["registered_at_dt"])

# 3. Fuzzy duplicates
TITLES = {
    "dr",
    "dr.",
    "prof",
    "prof.",
    "herr",
    "frau",
    "mr",
    "mr.",
    "mrs",
    "mrs.",
    "ms",
    "ms.",
    "dipl.-ing.",
    "ing.",
}


def normalize_email(email):
    if pd.isna(email) or not email:
        return ""
    email = str(email).lower().strip()
    if "@" in email:
        local, domain = email.split("@", 1)
        local = local.replace(".", "")
        return f"{local}@{domain}"
    return email


def clean_name(name):
    if pd.isna(name) or not name:
        return ""
    s = str(name).lower().strip()
    words = re.findall(r"\b\w+\b", s)
    words = [w for w in words if w not in TITLES]
    if len(words) > 2:
        words = [
            w
            for i, w in enumerate(words)
            if not (0 < i < len(words) - 1 and len(w) == 1)
        ]
    return " ".join(words)


def str_sim(s1, s2):
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0
    return SequenceMatcher(None, s1, s2).ratio()


def name_sim(n1, n2):
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0
    r1 = SequenceMatcher(None, n1, n2).ratio()
    t1 = " ".join(sorted(n1.split()))
    t2 = " ".join(sorted(n2.split()))
    r2 = SequenceMatcher(None, t1, t2).ratio()
    return max(r1, r2)


records = []
for idx, row in df.iterrows():
    records.append(
        {
            "row": row,
            "norm_email": normalize_email(row["email"]),
            "clean_name": clean_name(row["full_name"]),
        }
    )

n = len(records)
parent = list(range(n))


def find(i):
    if parent[i] == i:
        return i
    parent[i] = find(parent[i])
    return parent[i]


def union(i, j):
    root_i = find(i)
    root_j = find(j)
    if root_i != root_j:
        parent[root_i] = root_j


def is_match(r1, r2):
    n1, n2 = r1["clean_name"], r2["clean_name"]
    e1, e2 = r1["norm_email"], r2["norm_email"]

    if e1 and e2 and e1 == e2:
        ns = name_sim(n1, n2)
        if ns >= 0.50 or n1 in n2 or n2 in n1 or not n1 or not n2:
            return True

    if n1 and n2 and n1 == n2:
        es = str_sim(e1, e2)
        if es >= 0.50 or e1 in e2 or e2 in e1 or not e1 or not e2:
            return True

    ns = name_sim(n1, n2)
    es = str_sim(e1, e2)
    if ns >= 0.80 and es >= 0.80:
        return True

    return False


for i in range(n):
    for j in range(i + 1, n):
        if is_match(records[i], records[j]):
            union(i, j)

groups = {}
for i in range(n):
    root = find(i)
    if root not in groups:
        groups[root] = []
    groups[root].append(records[i]["row"])

final_rows = []
for root, row_list in groups.items():
    group_df = pd.DataFrame(row_list)
    group_df = group_df.sort_values(by="customer_id", ascending=True)
    final_rows.append(group_df.iloc[0])

result_df = pd.DataFrame(final_rows)
result_df = result_df[
    ["customer_id", "full_name", "email", "country", "registered_at"]
]

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result_df.to_parquet(output_path, index=False)