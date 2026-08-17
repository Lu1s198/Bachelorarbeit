import os
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd

input_path = Path(
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
)
output_path = Path(
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/dedup/openai_v1_zero_shot_r2/output.parquet"
)

if not input_path.exists():
    fallback_root = Path(
        r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
    )
    parquet_files = list(fallback_root.rglob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"Input file not found: {input_path}")
    input_path = parquet_files[0]

df = pd.read_parquet(input_path)

df = df.drop_duplicates(keep="first").copy()

df["_row_order"] = range(len(df))
df["_registered_sort"] = pd.to_datetime(df["registered_at"], errors="coerce")

df = (
    df.sort_values(
        by=["email", "_registered_sort", "_row_order"],
        ascending=[True, False, True],
        kind="mergesort",
        na_position="last",
    )
    .drop_duplicates(subset=["email"], keep="first")
    .sort_values("_row_order", kind="mergesort")
    .reset_index(drop=True)
)

title_tokens = {
    "mr", "mrs", "ms", "miss", "mx",
    "dr", "prof", "professor", "sir", "dame",
    "herr", "frau", "fr", "hr",
    "ing", "dipl", "med", "phd", "mba",
}

def normalize_text(value):
    if pd.isna(value):
        return ""
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.casefold()

def normalize_email(value):
    text = normalize_text(value).strip().replace(" ", "")
    if not text or text.count("@") != 1:
        return ""
    local, domain = text.split("@", 1)
    if not local or not domain:
        return ""
    local = local.replace(".", "")
    return f"{local}@{domain}"

def name_tokens(value):
    text = normalize_text(value)
    tokens = re.findall(r"[a-z0-9]+", text)
    tokens = [token for token in tokens if token not in title_tokens]
    return tokens

def normalized_name(value):
    tokens = name_tokens(value)
    tokens = [token for token in tokens if len(token) > 1]
    return " ".join(tokens)

def names_match(name_a, name_b):
    tokens_a = [t for t in name_tokens(name_a) if len(t) > 1]
    tokens_b = [t for t in name_tokens(name_b) if len(t) > 1]

    if not tokens_a or not tokens_b:
        return False

    norm_a = " ".join(tokens_a)
    norm_b = " ".join(tokens_b)

    if norm_a == norm_b:
        return True

    sorted_a = " ".join(sorted(tokens_a))
    sorted_b = " ".join(sorted(tokens_b))

    direct_ratio = SequenceMatcher(None, norm_a, norm_b).ratio()
    sorted_ratio = SequenceMatcher(None, sorted_a, sorted_b).ratio()

    first_ratio = SequenceMatcher(None, tokens_a[0], tokens_b[0]).ratio()
    last_ratio = SequenceMatcher(None, tokens_a[-1], tokens_b[-1]).ratio()

    if len(tokens_a) >= 2 and len(tokens_b) >= 2:
        if first_ratio >= 0.75 and last_ratio >= 0.80 and max(direct_ratio, sorted_ratio) >= 0.82:
            return True
        if max(direct_ratio, sorted_ratio) >= 0.92:
            return True
    else:
        if max(direct_ratio, sorted_ratio) >= 0.88:
            return True

    return False

class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        root_a = self.find(a)
        root_b = self.find(b)

        if root_a == root_b:
            return

        if self.rank[root_a] < self.rank[root_b]:
            root_a, root_b = root_b, root_a

        self.parent[root_b] = root_a

        if self.rank[root_a] == self.rank[root_b]:
            self.rank[root_a] += 1

df["_normalized_email"] = df["email"].map(normalize_email)
df["_normalized_name"] = df["full_name"].map(normalized_name)

union_find = UnionFind(len(df))

for _, group in df[df["_normalized_email"] != ""].groupby("_normalized_email", sort=False):
    indices = group.index.to_list()

    for pos_a in range(len(indices)):
        idx_a = indices[pos_a]
        name_a = df.at[idx_a, "full_name"]

        for pos_b in range(pos_a + 1, len(indices)):
            idx_b = indices[pos_b]
            name_b = df.at[idx_b, "full_name"]

            if names_match(name_a, name_b):
                union_find.union(idx_a, idx_b)

components = {}
for idx in df.index:
    root = union_find.find(idx)
    components.setdefault(root, []).append(idx)

kept_indices = []
for members in components.values():
    representative = min(
        members,
        key=lambda i: (df.at[i, "customer_id"], df.at[i, "_row_order"]),
    )
    kept_indices.append(representative)

result = (
    df.loc[kept_indices]
    .sort_values("_row_order", kind="mergesort")
    .drop(columns=["_row_order", "_registered_sort", "_normalized_email", "_normalized_name"])
    .reset_index(drop=True)
)

os.makedirs(output_path.parent, exist_ok=True)
result.to_parquet(output_path, index=False)