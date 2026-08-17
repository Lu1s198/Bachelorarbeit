# ============================================================
# ETL Task: Deduplication of customer records
# ============================================================
# Sub-steps:
# 1. Remove exact duplicate rows (all columns identical), keep first occurrence.
# 2. Remove rows with duplicate `email`, keep the row with the most recent
#    `registered_at` value.
# 3. Detect and remove "fuzzy" duplicates:
#    - Normalize email (lowercase, remove dots in local part before @)
#    - Normalize full_name (lowercase, strip titles/salutations, remove
#      middle initials, strip punctuation)
#    - Group by normalized email (exact match after normalization, since
#      email variation is limited to case/dots)
#    - Within each group, compare normalized names with a fuzzy similarity
#      measure (handles typos, case differences, middle initials)
#    - If name similarity indicates same person, keep the row with the
#      smallest customer_id, drop the rest.
# ============================================================

import pandas as pd
import re
from difflib import SequenceMatcher

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/anthropic_v3_chain_of_thought_r2/output.parquet"

# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------
df = pd.read_parquet(input_path)

# ------------------------------------------------------------
# Step 1: Remove exact duplicate rows, keep first occurrence
# ------------------------------------------------------------
df = df.drop_duplicates(keep='first').reset_index(drop=True)

# ------------------------------------------------------------
# Step 2: Remove rows with duplicate email, keep most recent registered_at
# ------------------------------------------------------------
# Convert to datetime for correct sorting (ISO format already, but ensure dtype)
df['_registered_at_dt'] = pd.to_datetime(df['registered_at'])

# Sort so that the most recent registration comes first, then drop dupes on email
df = df.sort_values('_registered_at_dt', ascending=False)
df = df.drop_duplicates(subset='email', keep='first')

# Drop helper column (keep original string format of registered_at)
df = df.drop(columns=['_registered_at_dt']).reset_index(drop=True)

# ------------------------------------------------------------
# Step 3: Detect and remove fuzzy duplicates (same person, different spelling)
# ------------------------------------------------------------

# Common salutations/titles to strip from names (not part of the actual name)
TITLES = {
    'dr', 'dr.', 'mr', 'mr.', 'mrs', 'mrs.', 'ms', 'ms.', 'miss',
    'herr', 'frau', 'prof', 'prof.', 'mx', 'mx.'
}

def normalize_email(email: str) -> str:
    """Lowercase email and remove dots in the local part (before @)."""
    email = str(email).strip().lower()
    if '@' not in email:
        return email
    local, domain = email.split('@', 1)
    local = local.replace('.', '')
    return f"{local}@{domain}"

def normalize_name(name: str) -> str:
    """Lowercase name, strip titles, remove punctuation and middle initials."""
    name = str(name).lower()
    # Remove punctuation (dots, commas, etc.)
    name = re.sub(r'[^\w\s]', '', name)
    tokens = name.split()
    # Remove titles/salutations
    tokens = [t for t in tokens if t not in TITLES]
    # Remove middle initials (single-character tokens, e.g. "j" in "John J Smith")
    tokens = [t for t in tokens if len(t) > 1]
    return ' '.join(tokens)

df['_email_norm'] = df['email'].apply(normalize_email)
df['_name_norm'] = df['full_name'].apply(normalize_name)

# Sort by customer_id ascending so that when we find a fuzzy duplicate group,
# the first-seen (smallest customer_id) is naturally the one we keep.
df = df.sort_values('customer_id').reset_index(drop=True)

to_drop = set()

# Group candidates by normalized email (exact match required here, since
# email spelling variation is restricted to case/dots which is already
# normalized away).
for email_norm, group in df.groupby('_email_norm'):
    if len(group) < 2:
        continue
    idxs = group.index.tolist()
    names = group['_name_norm'].tolist()

    for i in range(len(idxs)):
        if idxs[i] in to_drop:
            continue
        for j in range(i + 1, len(idxs)):
            if idxs[j] in to_drop:
                continue
            # Fuzzy similarity on normalized names to confirm same person
            ratio = SequenceMatcher(None, names[i], names[j]).ratio()
            if ratio > 0.8:  # threshold tuned to catch typos/case/middle-initial diffs
                # idxs[i] has smaller customer_id (due to sort), keep it, drop idxs[j]
                to_drop.add(idxs[j])

df = df.drop(index=to_drop)

# Clean up helper columns
df = df.drop(columns=['_email_norm', '_name_norm']).reset_index(drop=True)

# ------------------------------------------------------------
# Write result (only the last step's output is persisted)
# ------------------------------------------------------------
df.to_parquet(output_path, index=False)