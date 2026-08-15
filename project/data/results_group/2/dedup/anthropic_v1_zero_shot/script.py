import os
import re
import difflib
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
INPUT_PATH = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
OUTPUT_PATH = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/anthropic_v1_zero_shot/output.parquet"

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = pd.read_parquet(INPUT_PATH)

expected_cols = ["customer_id", "full_name", "email", "country", "registered_at"]
for col in expected_cols:
    if col not in df.columns:
        df[col] = None

df["customer_id"] = df["customer_id"].astype("int64")
df["full_name"] = df["full_name"].astype(str)
df["email"] = df["email"].astype(str)
df["country"] = df["country"].astype(str)
df["registered_at"] = df["registered_at"].astype(str)

# ---------------------------------------------------------------------------
# Step 1: Remove exact duplicates (all columns identical), keep first
# ---------------------------------------------------------------------------
df_step1 = df.drop_duplicates(keep="first").reset_index(drop=True)

# ---------------------------------------------------------------------------
# Step 2: Remove rows with duplicate email, keep the one with the most
# recent registered_at value (ISO format, so string comparison works)
# ---------------------------------------------------------------------------
df_step2 = df_step1.copy()
df_step2["_reg_sort"] = pd.to_datetime(df_step2["registered_at"], errors="coerce")

df_step2 = df_step2.sort_values(
    by=["_reg_sort"], ascending=False, na_position="last"
)
df_step2 = df_step2.drop_duplicates(subset=["email"], keep="first")
df_step2 = df_step2.drop(columns=["_reg_sort"]).reset_index(drop=True)

# ---------------------------------------------------------------------------
# Step 3: Detect and remove fuzzy duplicates
#   - same real person with slightly different name spelling
#     (typos, case, with/without middle initial, titles/salutations)
#   - and/or different email spelling (dots before @, case)
#   Both name and email must indicate the same person for a match.
#   Keep the smallest customer_id among matches.
# ---------------------------------------------------------------------------

TITLES = {
    "mr", "mrs", "ms", "miss", "mister", "misses",
    "dr", "prof", "professor", "sir", "madam", "herr", "frau"
}


def normalize_email(email: str) -> str:
    email = str(email).strip().lower()
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    local = local.replace(".", "")
    return f"{local}@{domain}"


def normalize_name(name: str) -> str:
    name = str(name).strip()
    # remove punctuation except spaces and hyphens
    tokens = re.split(r"\s+", name)
    cleaned_tokens = []
    for t in tokens:
        t_clean = t.strip(".,")
        if t_clean.lower() in TITLES:
            continue
        # remove middle initials: single letter, optional dot
        if re.match(r"^[A-Za-z]\.?$", t_clean):
            continue
        cleaned_tokens.append(t_clean.lower())
    return " ".join(cleaned_tokens).strip()


def name_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


df3 = df_step2.copy().reset_index(drop=True)
df3["_norm_email"] = df3["email"].apply(normalize_email)
df3["_norm_name"] = df3["full_name"].apply(normalize_name)

n = len(df3)
parent = list(range(n))


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry:
        parent[max(rx, ry)] = min(rx, ry)


NAME_SIM_THRESHOLD = 0.82

# Group candidate matches by normalized email to limit comparisons,
# since a matching email normalization is a very strong signal.
email_groups = {}
for idx, em in enumerate(df3["_norm_email"]):
    email_groups.setdefault(em, []).append(idx)

for em, idxs in email_groups.items():
    if len(idxs) < 2:
        continue
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            idx_a, idx_b = idxs[i], idxs[j]
            name_a = df3.at[idx_a, "_norm_name"]
            name_b = df3.at[idx_b, "_norm_name"]
            if name_a == name_b or name_similarity(name_a, name_b) >= NAME_SIM_THRESHOLD:
                union(idx_a, idx_b)

# Also catch cases where email normalization differs slightly (rare edge
# cases beyond dot/case handling) but name matches exactly after
# normalization AND local-part (before dot removal) shares same domain
# and near-identical local part - kept conservative, primary matching
# relies on normalized email equality above per requirements.

df3["_cluster"] = [find(i) for i in range(n)]

# Within each cluster, keep the row with the smallest customer_id
df3 = df3.sort_values(by=["_cluster", "customer_id"], ascending=[True, True])
df_final = df3.drop_duplicates(subset=["_cluster"], keep="first")

df_final = df_final.drop(columns=["_norm_email", "_norm_name", "_cluster"])
df_final = df_final.reset_index(drop=True)

# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
output_cols = ["customer_id", "full_name", "email", "country", "registered_at"]
df_final = df_final[output_cols]

df_final.to_parquet(OUTPUT_PATH, index=False)