import os
import re
import difflib
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
if not os.path.exists(input_path):
    input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/output.parquet"

output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/google_v2_few_shot_r2/output.parquet"

df = pd.read_parquet(input_path)

# 1. Entferne exakte Duplikate
df = df.drop_duplicates(keep="first")

# 2. Entferne Zeilen mit mehrfach vorkommender email (behalte jüngsten registered_at-Wert)
df = df.sort_values("registered_at", ascending=False).drop_duplicates("email", keep="first")

# 3. Erkenne und entferne unscharfe Duplikate
def clean_name(s):
    if not isinstance(s, str):
        return ""
    s = re.sub(
        r"\b(dr|prof|mr|mrs|ms|miss|herr|frau|dipl|ing|doktor|professor|phd|msc|bsc)\b\.?",
        "",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(r"\b[a-zA-Z]\b\.?", "", s)
    s = re.sub(r"[^a-zA-Z0-9\s]", "", s)
    return " ".join(s.lower().split())

def clean_email(s):
    if not isinstance(s, str):
        return ""
    s = s.lower().strip()
    if "@" in s:
        parts = s.split("@")
        return parts[0].replace(".", "") + "@" + "@".join(parts[1:])
    return s

def is_similar(r1, r2):
    n1, n2 = r1["_c_name"], r2["_c_name"]
    e1, e2 = r1["_c_email"], r2["_c_email"]
    
    e_ratio = difflib.SequenceMatcher(None, e1, e2).ratio()
    e_match = (e1 == e2) or (e_ratio >= 0.85)
    
    n_ratio = difflib.SequenceMatcher(None, n1, n2).ratio()
    n1_tokens, n2_tokens = set(n1.split()), set(n2.split())
    jaccard = len(n1_tokens & n2_tokens) / len(n1_tokens | n2_tokens) if (n1_tokens or n2_tokens) else 0
    
    n_match = (n1 == n2) or (n_ratio >= 0.75) or (jaccard >= 0.5 and n_ratio > 0.6)
    
    return e_match and n_match

df["_c_name"] = df["full_name"].apply(clean_name)
df["_c_email"] = df["email"].apply(clean_email)

rows = df.to_dict("records")
n = len(rows)
parent = list(range(n))

def find(i):
    if parent[i] == i:
        return i
    parent[i] = find(parent[i])
    return parent[i]

def union(i, j):
    root_i, root_j = find(i), find(j)
    if root_i != root_j:
        parent[root_i] = root_j

for i in range(n):
    for j in range(i + 1, n):
        if is_similar(rows[i], rows[j]):
            union(i, j)

groups = {}
for i in range(n):
    root = find(i)
    if root not in groups:
        groups[root] = []
    groups[root].append(rows[i])

kept_rows = [min(group, key=lambda r: r["customer_id"]) for group in groups.values()]
res_df = pd.DataFrame(kept_rows).drop(columns=["_c_name", "_c_email"])

os.makedirs(os.path.dirname(output_path), exist_ok=True)
res_df.to_parquet(output_path, index=False)