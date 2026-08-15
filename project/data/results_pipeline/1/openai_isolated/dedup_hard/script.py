import os
import re
import unicodedata
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai_isolated/dedup_hard/output.parquet"

df = pd.read_parquet(input_path).copy()

for column in ["customer_id", "full_name", "email", "country", "registered_at"]:
    if column not in df.columns:
        df[column] = pd.NA

df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")

TITLE_TOKENS = {
    "mr", "mister", "mrs", "miss", "ms", "mx",
    "dr", "doctor", "prof", "professor",
    "herr", "frau", "frl", "fräulein",
    "sir", "dame", "lord", "lady",
    "rev", "reverend", "fr", "father",
    "ing", "dipl", "med", "phd", "md",
    "jr", "sr"
}

CHAR_REPLACEMENTS = str.maketrans({
    "ß": "ss",
    "ẞ": "ss",
    "æ": "ae",
    "Æ": "ae",
    "œ": "oe",
    "Œ": "oe",
    "ø": "o",
    "Ø": "o",
    "ð": "d",
    "Ð": "d",
    "þ": "th",
    "Þ": "th",
    "ł": "l",
    "Ł": "l",
})


def text_to_ascii(value):
    if value is None or pd.isna(value):
        return ""
    value = str(value).translate(CHAR_REPLACEMENTS)
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    return value.casefold()


def normalize_email(value):
    if value is None or pd.isna(value):
        return None
    email = text_to_ascii(value).strip().replace(" ", "")
    if email.count("@") != 1:
        return None
    local, domain = email.split("@", 1)
    if not local or not domain:
        return None
    local = local.replace(".", "")
    return local + "@" + domain


def normalize_name(value):
    text = text_to_ascii(value)
    tokens = re.findall(r"[a-z0-9]+", text)
    while tokens and tokens[0] in TITLE_TOKENS:
        tokens.pop(0)
    if not tokens:
        return {"tokens": (), "core": (), "compact": ""}
    core = tuple(token for token in tokens if len(token) > 1)
    if not core:
        core = tuple(tokens)
    compact = "".join(core)
    return {"tokens": tuple(tokens), "core": core, "compact": compact}


def levenshtein_distance(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            insertion = current[-1] + 1
            deletion = previous[j] + 1
            substitution = previous[j - 1] + (ca != cb)
            current.append(min(insertion, deletion, substitution))
        previous = current
    return previous[-1]


def similarity(a, b):
    if not a or not b:
        return 0.0
    maximum = max(len(a), len(b))
    return (maximum - levenshtein_distance(a, b)) / maximum


def names_match(name_a, name_b):
    compact_a = name_a["compact"]
    compact_b = name_b["compact"]

    if not compact_a or not compact_b:
        return False

    if compact_a == compact_b:
        return True

    core_a = name_a["core"]
    core_b = name_b["core"]

    if len(core_a) == 1 or len(core_b) == 1:
        return similarity(compact_a, compact_b) >= 0.88

    first_a, last_a = core_a[0], core_a[-1]
    first_b, last_b = core_b[0], core_b[-1]

    if first_a == first_b and last_a == last_b:
        return True

    full_similarity = similarity(compact_a, compact_b)
    first_similarity = similarity(first_a, first_b)
    last_similarity = similarity(last_a, last_b)

    if (
        full_similarity >= 0.82
        and first_similarity >= 0.65
        and last_similarity >= 0.75
    ):
        return True

    return False


n = len(df)
parent = np.arange(n, dtype=np.int64)
rank = np.zeros(n, dtype=np.int8)


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(a, b):
    root_a = find(a)
    root_b = find(b)
    if root_a == root_b:
        return
    if rank[root_a] < rank[root_b]:
        parent[root_a] = root_b
    elif rank[root_a] > rank[root_b]:
        parent[root_b] = root_a
    else:
        parent[root_b] = root_a
        rank[root_a] += 1


email_keys = [normalize_email(value) for value in df["email"].tolist()]
name_keys = [normalize_name(value) for value in df["full_name"].tolist()]

email_groups = {}
for position, email_key in enumerate(email_keys):
    if email_key is not None:
        email_groups.setdefault(email_key, []).append(position)

for positions in email_groups.values():
    if len(positions) < 2:
        continue
    for left_offset in range(len(positions) - 1):
        left = positions[left_offset]
        for right_offset in range(left_offset + 1, len(positions)):
            right = positions[right_offset]
            if names_match(name_keys[left], name_keys[right]):
                union(left, right)

cluster_members = {}
for position in range(n):
    root = find(position)
    cluster_members.setdefault(root, []).append(position)

selected_positions = []
customer_ids = df["customer_id"].tolist()

for members in cluster_members.values():
    def member_sort_key(pos):
        customer_id = customer_ids[pos]
        if pd.isna(customer_id):
            return (1, float("inf"), pos)
        return (0, int(customer_id), pos)

    selected_positions.append(min(members, key=member_sort_key))

result = df.iloc[selected_positions].copy()
result = result.sort_values(
    by="customer_id",
    kind="stable",
    na_position="last"
).reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)