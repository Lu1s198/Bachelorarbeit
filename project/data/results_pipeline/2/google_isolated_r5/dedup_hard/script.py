import os
import re
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r5/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

if df.empty:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)
    exit()

def normalize_email(email):
    if not isinstance(email, str) or not email:
        return ""
    email = email.strip().lower()
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    local = local.replace(".", "").split("+")[0]
    return f"{local}@{domain}"

def extract_name_features(full_name):
    if not isinstance(full_name, str) or not full_name:
        return "", "", []
    raw = full_name.lower().strip()
    cleaned = re.sub(r"[^\w\s]", " ", raw)
    tokens = cleaned.split()
    titles = {
        "mr", "mrs", "ms", "miss", "dr", "prof", "herr", "frau",
        "doktor", "professor", "sir", "madam", "ing", "dipl"
    }
    filtered = [t for t in tokens if t not in titles and not t.isdigit()]
    no_initials = [t for t in filtered if len(t) > 1]
    if not no_initials:
        no_initials = filtered
    clean_str = " ".join(no_initials)
    sorted_str = " ".join(sorted(no_initials))
    return clean_str, sorted_str, no_initials

def levenshtein_dist(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_dist(s2, s1)
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

emails_norm = [normalize_email(e) for e in df["email"]]
name_features = [extract_name_features(n) for n in df["full_name"]]
names_clean = [f[0] for f in name_features]
names_sorted = [f[1] for f in name_features]
names_tokens = [f[2] for f in name_features]

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
for i in range(n):
    e = emails_norm[i]
    ns = names_sorted[i]
    toks = names_tokens[i]
    
    keys = set()
    if e:
        keys.add(("e", e))
        local = e.split("@")[0]
        if len(local) >= 3:
            keys.add(("epref", local[:3]))
    if ns:
        keys.add(("ns", ns))
    if len(toks) >= 2:
        keys.add(("fl", (toks[0], toks[-1])))
        keys.add(("lf", (toks[-1], toks[0])))
    
    for k in keys:
        blocks.setdefault(k, []).append(i)

candidate_pairs = set()
for k, idxs in blocks.items():
    if len(idxs) < 2 or len(idxs) > 200:
        continue
    for x in range(len(idxs)):
        for y in range(x + 1, len(idxs)):
            i, j = idxs[x], idxs[y]
            if i > j:
                i, j = j, i
            candidate_pairs.add((i, j))

def is_match(i, j):
    e1, e2 = emails_norm[i], emails_norm[j]
    if e1 == e2:
        email_ok = True
    else:
        if not e1 or not e2:
            email_ok = False
        else:
            dist_e = levenshtein_dist(e1, e2)
            email_ok = (dist_e <= 2) and (min(len(e1), len(e2)) > 5)
            
    if not email_ok:
        return False
        
    nc1, nc2 = names_clean[i], names_clean[j]
    ns1, ns2 = names_sorted[i], names_sorted[j]
    
    if nc1 == nc2 or ns1 == ns2:
        return True
    
    if not nc1 or not nc2:
        return False
        
    dist_nc = levenshtein_dist(nc1, nc2)
    if dist_nc <= 2:
        return True
        
    dist_ns = levenshtein_dist(ns1, ns2)
    if dist_ns <= 2:
        return True
        
    t1, t2 = names_tokens[i], names_tokens[j]
    if t1 and t2:
        s1, s2 = set(t1), set(t2)
        inter = s1.intersection(s2)
        if len(inter) >= 2 or (len(inter) >= 1 and min(len(s1), len(s2)) == 1):
            return True

    return False

for i, j in candidate_pairs:
    if is_match(i, j):
        union(i, j)

clusters = [find(i) for i in range(n)]
df["_cluster"] = clusters

df = df.sort_values(by="customer_id", ascending=True)
df = df.drop_duplicates(subset=["_cluster"], keep="first")
df = df.drop(columns=["_cluster"])

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)