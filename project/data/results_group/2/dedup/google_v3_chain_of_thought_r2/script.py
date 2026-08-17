# Step 1: Import required libraries for data processing, regex, fuzzy matching, and graph components.
import difflib
import os
import re
import pandas as pd

# Define input and output paths
primary_input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
fallback_input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/google_v3_chain_of_thought_r2/output.parquet"

# Load the dataset from primary path or fallback if primary does not exist
if os.path.exists(primary_input_path):
  df = pd.read_parquet(primary_input_path)
else:
  df = pd.read_parquet(fallback_input_path)

# -----------------------------------------------------------------------------
# Step 1: Entferne exakte Duplikate (Zeilen, in denen alle Spaltenwerte identisch sind)
# Behalte jeweils das erste Vorkommen.
# -----------------------------------------------------------------------------
df = df.drop_duplicates(keep="first")

# -----------------------------------------------------------------------------
# Step 2: Entferne Zeilen mit mehrfach vorkommender `email`.
# Behalte bei gleicher E-Mail die Zeile mit dem jüngsten `registered_at`-Wert.
# (Werte liegen bereits im ISO-Format YYYY-MM-DD vor, daher lexikographisch sortierbar).
# -----------------------------------------------------------------------------
# Sort by registered_at descending to have latest dates first
df = df.sort_values(
    by=["registered_at", "customer_id"], ascending=[False, True]
)
df = df.drop_duplicates(subset=["email"], keep="first")


# -----------------------------------------------------------------------------
# Step 3: Erkenne und entferne unscharfe Duplikate:
# - Dieselbe reale Person mit abweichender Schreibweise des Namens (Tippfehler, Groß-/Kleinschreibung, mit/ohne Mittelinitial)
# - Abweichende E-Mail-Schreibweise (Punkte vor dem @, Groß-/Kleinschreibung)
# - Namen können Anreden/Titel enthalten (Dr., Prof., Mr., Mrs., etc.), diese entfernen
# - Für Übereinstimmungen müssen Name und E-Mail auf dieselbe Person hindeuten
# - Behalte bei Übereinstimmungen die kleinste customer_id
# -----------------------------------------------------------------------------


def normalize_email(email_str):
  if not isinstance(email_str, str):
    return ""
  email_str = email_str.strip().lower()
  if "@" in email_str:
    user, domain = email_str.split("@", 1)
    # Remove dots from username part
    user = user.replace(".", "")
    return f"{user}@{domain}"
  return email_str.replace(".", "")


def normalize_name(name_str):
  if not isinstance(name_str, str):
    return ""
  # Lowercase
  text = name_str.lower()
  # Remove titles/salutations
  titles_pattern = r"\b(mr|mrs|ms|miss|dr|prof|herr|frau|sir|lady)\b\.?"
  text = re.sub(titles_pattern, "", text)
  # Replace non-alphanumeric chars with space
  text = re.sub(r"[^a-z0-9\s]", " ", text)
  # Tokenize
  tokens = text.split()
  # Remove single letter middle initials
  tokens = [t for t in tokens if len(t) > 1]
  return " ".join(tokens)


def names_are_similar(name1, name2):
  if not name1 or not name2:
    return False
  if name1 == name2:
    return True
  # Calculate fuzzy similarity ratio
  ratio = difflib.SequenceMatcher(None, name1, name2).ratio()
  if ratio >= 0.8:
    return True
  # Substring / token containment check for variations
  t1 = set(name1.split())
  t2 = set(name2.split())
  if t1 and t2 and (t1.issubset(t2) or t2.issubset(t1)):
    return True
  return False


def emails_are_similar(norm_e1, norm_e2):
  if not norm_e1 or not norm_e2:
    return False
  if norm_e1 == norm_e2:
    return True
  # High threshold fuzzy match for email typos
  return difflib.SequenceMatcher(None, norm_e1, norm_e2).ratio() >= 0.92


# Reset index to iterate cleanly
df = df.reset_index(drop=True)
norm_emails = [normalize_email(e) for e in df["email"]]
norm_names = [normalize_name(n) for n in df["full_name"]]

# Find connected components of fuzzy duplicate rows
n = len(df)
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


# Compare candidate pairs to group fuzzy duplicates
for i in range(n):
  for j in range(i + 1, n):
    # Check if emails match/are similar AND names match/are similar
    e_match = emails_are_similar(norm_emails[i], norm_emails[j])
    if e_match:
      n_match = names_are_similar(norm_names[i], norm_names[j])
      if n_match:
        union(i, j)

# Group rows by component root and select the row with minimum customer_id
df["_cluster"] = [find(i) for i in range(n)]
df = (
    df.sort_values(by=["customer_id"])
    .groupby("_cluster", as_index=False)
    .first()
)
df = df.drop(columns=["_cluster"])

# Sort final output by customer_id for clean presentation
df = df.sort_values(by="customer_id").reset_index(drop=True)

# Save result to target parquet file
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)