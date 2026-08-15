import os
import re
from difflib import SequenceMatcher
import pandas as pd

# Define input and output file paths
input_path = (
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/"
    "_reference/cleaning_hard/output.parquet"
)
output_path = (
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/"
    "dedup/google_v3_chain_of_thought/output.parquet"
)

# Step 1: Read input data and remove exact duplicates
# -----------------------------------------------------------------------------
# Read input parquet file
df = pd.read_parquet(input_path)

# Step 1: Remove exact duplicates (identical in all columns), keeping the first occurrence
df = df.drop_duplicates(keep="first")


# Step 2: Handle duplicate emails based on registered_at
# -----------------------------------------------------------------------------
# Sort by registered_at descending (latest date first) and customer_id ascending (deterministic tie-breaker)
df = df.sort_values(
    by=["registered_at", "customer_id"], ascending=[False, True]
)

# Keep the row with the most recent registered_at value for each email
df = df.drop_duplicates(subset=["email"], keep="first")


# Step 3: Identify and remove fuzzy duplicates
# -----------------------------------------------------------------------------
# Helper function to normalize email (strip, lowercase, ignore dots before @)
def normalize_email(email):
    if not isinstance(email, str) or "@" not in email:
        return ""
    parts = email.strip().lower().split("@")
    prefix = parts[0].replace(".", "")
    domain = "@".join(parts[1:])
    return f"{prefix}@{domain}"


# Helper function to normalize name (lowercase, strip titles, remove middle initials, clean punctuation)
def normalize_name(name):
    if not isinstance(name, str):
        return ""
    name = name.lower()

    # Common titles/salutations to remove
    titles = [
        "dr. med.",
        "dr.",
        "prof. dr.",
        "prof.",
        "mr.",
        "mrs.",
        "ms.",
        "miss",
        "herr",
        "frau",
        "dipl.-ing.",
        "dipl. ing.",
        "ing.",
        "sir",
        "lady",
        "doktor",
        "professor",
    ]
    for title in sorted(titles, key=len, reverse=True):
        name = re.sub(r"\b" + re.escape(title) + r"\b", "", name)

    # Remove non-alphanumeric characters except spaces
    name = re.sub(r"[^\w\s]", " ", name)

    # Remove single-letter middle initials
    words = [w for w in name.split() if len(w) > 1]
    return " ".join(words)


# Helper function to measure similarity ratio between two strings
def similarity(s1, s2):
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1, s2).ratio()


# Reset index to allow positional index manipulation for Union-Find algorithm
df_reset = df.reset_index(drop=True)
n = len(df_reset)

# Prepare normalized representations for comparison
norm_emails = [normalize_email(e) for e in df_reset["email"]]
norm_names = [normalize_name(n) for n in df_reset["full_name"]]

# Union-Find (Disjoint Set Union) data structure to group duplicates
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
        # Keep the record with the smaller customer_id as the cluster root
        cid_i = df_reset.iloc[root_i]["customer_id"]
        cid_j = df_reset.iloc[root_j]["customer_id"]
        if cid_i <= cid_j:
            parent[root_j] = root_i
        else:
            parent[root_i] = root_j


# Compare pairs to identify duplicates
for i in range(n):
    for j in range(i + 1, n):
        e1, e2 = norm_emails[i], norm_emails[j]
        n1, n2 = norm_names[i], norm_names[j]

        e_sim = similarity(e1, e2)
        n_sim = similarity(n1, n2)

        # Condition for matching the same person:
        # 1) Exact match on normalized email and high name similarity / overlap
        # 2) High email similarity AND high name similarity
        is_same_email = (e1 == e2) or (e_sim >= 0.88)
        is_same_name = (
            (n1 == n2)
            or (n_sim >= 0.75)
            or (set(n1.split()) == set(n2.split()))
        )

        if is_same_email and is_same_name:
            union(i, j)

# Keep only representative rows (cluster roots with smallest customer_id)
keep_indices = [i for i in range(n) if find(i) == i]
df_cleaned = df_reset.iloc[keep_indices].copy()

# Sort final dataframe by customer_id
df_cleaned = df_cleaned.sort_values(by="customer_id").reset_index(drop=True)

# Step 4: Write output parquet file
# -----------------------------------------------------------------------------
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_cleaned.to_parquet(output_path, index=False)