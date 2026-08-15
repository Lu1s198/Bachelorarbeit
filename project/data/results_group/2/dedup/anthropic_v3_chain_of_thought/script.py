# ============================================================
# ETL Task: Deduplication Pipeline (3 steps)
# ============================================================
# Step 1: Remove exact duplicate rows (all columns identical), keep first occurrence
# Step 2: Remove rows with duplicate email, keep the one with the most recent registered_at
# Step 3: Detect and remove "fuzzy" duplicates:
#         - same person despite name variations (typos, case, middle initial, titles)
#         - and/or email variations (dots before @, case)
#         Both name AND email must point to the same person to merge.
#         Keep the row with the smallest customer_id among matches.
# ============================================================

import pandas as pd
import re
import difflib
from itertools import combinations

# ------------------------------------------------------------
# Load input data
# ------------------------------------------------------------
input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/anthropic_v3_chain_of_thought/output.parquet"

df = pd.read_parquet(input_path)

# ============================================================
# STEP 1: Remove exact duplicates (all columns identical)
# ============================================================
df_step1 = df.drop_duplicates(keep="first").reset_index(drop=True)

# ============================================================
# STEP 2: Remove rows with duplicate email, keep most recent registered_at
# ============================================================
# registered_at is already ISO format (YYYY-MM-DD), so string sort == chronological sort
df_step2 = (
    df_step1.sort_values("registered_at", ascending=False)
    .drop_duplicates(subset="email", keep="first")
    .reset_index(drop=True)
)

# ============================================================
# STEP 3: Fuzzy duplicate detection
# ============================================================

# --- Helper: normalize email (lowercase, remove dots in local part before @) ---
def normalize_email(email):
    if pd.isna(email):
        return ""
    email = email.strip().lower()
    if "@" in email:
        local, domain = email.split("@", 1)
        local = local.replace(".", "")
        return f"{local}@{domain}"
    return email

# --- Helper: normalize name (remove titles/honorifics, remove middle initials, lowercase) ---
TITLES = [
    "dr", "mr", "mrs", "ms", "miss", "prof", "professor",
    "herr", "frau", "sir", "madam", "dr.", "mr.", "mrs.", "ms.", "prof."
]

def normalize_name(name):
    if pd.isna(name):
        return ""
    name = name.strip().lower()
    # remove punctuation except spaces and letters
    name = re.sub(r"[.,]", " ", name)
    tokens = name.split()
    # remove titles/honorifics
    tokens = [t for t in tokens if t not in TITLES]
    # remove middle initials (single-letter tokens, e.g. "j" from "John J Smith")
    tokens = [t for t in tokens if len(t) > 1]
    # collapse whitespace
    return " ".join(tokens).strip()

# Apply normalization
df_step2["email_norm"] = df_step2["email"].apply(normalize_email)
df_step2["name_norm"] = df_step2["full_name"].apply(normalize_name)

# --- Helper: fuzzy string similarity ratio ---
def similarity(a, b):
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()

# --- Union-Find (Disjoint Set) implementation for grouping matches ---
parent = {idx: idx for idx in df_step2.index}

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry:
        # keep smaller root index for determinism (not strictly needed)
        parent[max(rx, ry)] = min(rx, ry)

# --- Thresholds for fuzzy matching ---
NAME_SIM_THRESHOLD = 0.82   # tolerate small typos in names
EMAIL_SIM_THRESHOLD = 0.90  # tolerate minor email variations beyond dot-removal

indices = df_step2.index.tolist()
emails_norm = df_step2["email_norm"].to_dict()
names_norm = df_step2["name_norm"].to_dict()

# Compare all pairs (assuming dataset size is manageable for pairwise comparison)
for i, j in combinations(indices, 2):
    email_i, email_j = emails_norm[i], emails_norm[j]
    name_i, name_j = names_norm[i], names_norm[j]

    # Exact match after normalization counts as match
    email_match = (email_i == email_j) or (similarity(email_i, email_j) >= EMAIL_SIM_THRESHOLD)
    name_match = (name_i == name_j) or (similarity(name_i, name_j) >= NAME_SIM_THRESHOLD)

    # Require BOTH name and email to indicate the same person
    if email_match and name_match and name_i != "" and email_i != "":
        union(i, j)

# Assign group ids based on union-find roots
df_step2["group_id"] = df_step2.index.map(find)

# --- Keep the row with smallest customer_id per group ---
df_step3 = (
    df_step2.sort_values("customer_id", ascending=True)
    .drop_duplicates(subset="group_id", keep="first")
    .reset_index(drop=True)
)

# Drop helper columns before final output
df_final = df_step3.drop(columns=["email_norm", "name_norm", "group_id"])

# ============================================================
# Write result of the LAST step only
# ============================================================
df_final.to_parquet(output_path, index=False)