import os
import re
from difflib import SequenceMatcher
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
if not os.path.exists(input_path):
    input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/output.parquet"

df = pd.read_parquet(input_path)

# Step 1: Remove exact duplicates
df = df.drop_duplicates(keep="first")

# Step 2: Remove rows with duplicate email, keeping the most recent registered_at
df = df.sort_values(
    by=["registered_at", "customer_id"], ascending=[False, True]
)
df["_email_clean_step2"] = df["email"].astype(str).str.lower().str.strip()
df = df.drop_duplicates(subset=["_email_clean_step2"], keep="first").drop(
    columns=["_email_clean_step2"]
)

# Step 3: Remove fuzzy duplicates, keeping smallest customer_id
df = df.sort_values(by="customer_id", ascending=True).reset_index(drop=True)

TITLES = {
    "mr",
    "mrs",
    "ms",
    "dr",
    "prof",
    "dipl",
    "ing",
    "herr",
    "frau",
    "sir",
    "madam",
    "doktor",
    "professor",
}


def normalize_email(email):
    if not isinstance(email, str):
        return ""
    email = email.lower().strip()
    if "@" in email:
        local, domain = email.rsplit("@", 1)
        local = local.replace(".", "")
        if "+" in local:
            local = local.split("+")[0]
        return f"{local}@{domain}"
    return email


def normalize_name(name):
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = re.sub(r"[^\w\s]", " ", name)
    tokens = name.split()
    cleaned = [
        t for t in tokens if t not in TITLES and (len(t) > 1 or len(tokens) <= 2)
    ]
    return " ".join(cleaned)


def similarity(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


norm_emails = [normalize_email(e) for e in df["email"]]
norm_names = [normalize_name(n) for n in df["full_name"]]
sorted_names = [" ".join(sorted(n.split())) for n in norm_names]

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


def is_match(i, j):
    e1, e2 = norm_emails[i], norm_emails[j]
    n1, n2 = norm_names[i], norm_names[j]

    if e1 and e1 == e2:
        return True

    s_email = similarity(e1, e2)
    s_name = max(
        similarity(n1, n2), similarity(sorted_names[i], sorted_names[j])
    )

    if s_email >= 0.85 and s_name >= 0.75:
        return True
    if s_name >= 0.85 and s_email >= 0.75:
        return True

    return False


if n <= 2000:
    for i in range(n):
        for j in range(i + 1, n):
            if is_match(i, j):
                union(i, j)
else:
    blocks = {}
    for i in range(n):
        keys = set()
        em = norm_emails[i]
        nm = norm_names[i]
        if "@" in em:
            keys.add("dom_" + em.split("@")[1])
            keys.add("loc_" + em.split("@")[0][:3])
        if nm:
            keys.add("nm_" + nm[:3])
        for k in keys:
            blocks.setdefault(k, []).append(i)

    for candidates in blocks.values():
        c_len = len(candidates)
        if c_len > 1:
            for idx1 in range(c_len):
                for idx2 in range(idx1 + 1, c_len):
                    i, j = candidates[idx1], candidates[idx2]
                    if find(i) != find(j) and is_match(i, j):
                        union(i, j)

keep_indices = []
seen_roots = set()
for i in range(n):
    root = find(i)
    if root not in seen_roots:
        seen_roots.add(root)
        keep_indices.append(i)

output_df = (
    df.iloc[keep_indices]
    .sort_values(by="customer_id", ascending=True)
    .reset_index(drop=True)
)
output_df = output_df[
    ["customer_id", "full_name", "email", "country", "registered_at"]
]

output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/google_v1_zero_shot/output.parquet"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
output_df.to_parquet(output_path, index=False)