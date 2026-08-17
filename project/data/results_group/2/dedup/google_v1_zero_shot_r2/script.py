import os
import re
from difflib import SequenceMatcher
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/google_v1_zero_shot_r2/output.parquet"

df = pd.read_parquet(input_path)

# Step 1: Remove exact duplicates, keeping the first occurrence
df = df.drop_duplicates(keep="first")

# Step 2: Remove duplicate emails, keeping the youngest registered_at date
df = df.sort_values(by="registered_at", ascending=False)
df = df.drop_duplicates(subset=["email"], keep="first")


# Step 3: Fuzzy duplicate detection
def normalize_name(name):
  if not isinstance(name, str):
    return ""
  name = name.lower()
  name = re.sub(
      r"\b(mr|mrs|ms|miss|dr|prof|sir|lady|herr|frau|dipl|-ing)\.?\b", "", name
  )
  name = re.sub(r"\b[a-z]\.\b", "", name)
  words = re.findall(r"[a-zA-Z]+", name)
  words = [w.lower() for w in words if len(w) > 1]
  return " ".join(sorted(words))


def normalize_email(email):
  if not isinstance(email, str):
    return ""
  email = email.lower().strip()
  if "@" in email:
    local, domain = email.split("@", 1)
    local = local.replace(".", "").replace("_", "")
    return local + "@" + domain
  return email


df = df.reset_index(drop=True)
df["norm_name"] = df["full_name"].apply(normalize_name)
df["norm_email"] = df["email"].apply(normalize_email)

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


norm_names = df["norm_name"].values
norm_emails = df["norm_email"].values

for i in range(n):
  for j in range(i + 1, n):
    name_match = (
        norm_names[i] == norm_names[j] and len(norm_names[i]) > 0
    ) or (
        SequenceMatcher(None, norm_names[i], norm_names[j]).quick_ratio() > 0.75
        and SequenceMatcher(None, norm_names[i], norm_names[j]).ratio() >= 0.8
    )

    email_match = (
        norm_emails[i] == norm_emails[j] and len(norm_emails[i]) > 0
    ) or (
        SequenceMatcher(None, norm_emails[i], norm_emails[j]).quick_ratio()
        > 0.75
        and SequenceMatcher(None, norm_emails[i], norm_emails[j]).ratio() >= 0.8
    )

    if name_match and email_match:
      union(i, j)

df["cluster"] = [find(i) for i in range(n)]

# Keep smallest customer_id per cluster
df = df.sort_values(by="customer_id", ascending=True)
df = df.drop_duplicates(subset=["cluster"], keep="first")

output_cols = ["customer_id", "full_name", "email", "country", "registered_at"]
df = df[output_cols]

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)