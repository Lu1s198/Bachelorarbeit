import pandas as pd
import numpy as np
import re

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r3/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df["customer_id"] = df["customer_id"].astype("int64")
df["full_name"] = df["full_name"].astype(str)
df["email"] = df["email"].astype(str)
df["country"] = df["country"].astype(str)
df["registered_at"] = df["registered_at"].astype(str)

titles = {
    "mr", "mrs", "ms", "miss", "dr", "prof", "professor", "sir", "madam",
    "herr", "frau", "mme", "mlle", "monsieur", "madame", "dott", "sig",
    "sr", "jr", "ii", "iii", "iv"
}

def normalize_name(name):
    if pd.isna(name):
        return ""
    n = name.lower()
    n = re.sub(r"[^a-z0-9\s]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    tokens = n.split(" ")
    tokens = [t for t in tokens if t not in titles]
    tokens = [t for t in tokens if len(t) > 1]
    tokens = sorted(tokens)
    return " ".join(tokens)

def normalize_email(email):
    if pd.isna(email):
        return ""
    e = email.strip().lower()
    if "@" in e:
        local, domain = e.split("@", 1)
    else:
        local, domain = e, ""
    local = local.replace(".", "")
    return local + "@" + domain

df["_name_key"] = df["full_name"].apply(normalize_name)
df["_email_key"] = df["email"].apply(normalize_email)

df = df.sort_values("customer_id")

df_dedup = df.drop_duplicates(subset=["_name_key", "_email_key"], keep="first")

result = df_dedup[["customer_id", "full_name", "email", "country", "registered_at"]].reset_index(drop=True)

result.to_parquet(output_path, index=False)