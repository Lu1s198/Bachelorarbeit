import difflib
import os
import re
import unicodedata
import pandas as pd


class DSU:

  def __init__(self, n):
    self.parent = list(range(n))

  def find(self, i):
    if self.parent[i] == i:
      return i
    self.parent[i] = self.find(self.parent[i])
    return self.parent[i]

  def union(self, i, j):
    root_i = self.find(i)
    root_j = self.find(j)
    if root_i != root_j:
      self.parent[root_i] = root_j


def remove_accents(input_str):
  nfkd_form = unicodedata.normalize("NFKD", str(input_str))
  return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def clean_email(email):
  if pd.isna(email) or not email:
    return ""
  email = remove_accents(str(email)).lower().strip()
  if "@" in email:
    local, domain = email.split("@", 1)
    local = local.split("+")[0]
    local = local.replace(".", "")
    return f"{local}@{domain}"
  return email


def clean_name(name):
  if pd.isna(name) or not name:
    return ""
  name = remove_accents(str(name)).lower().strip()
  name = re.sub(r"[^\w\s]", " ", name)
  titles = {
      "mr",
      "mrs",
      "ms",
      "miss",
      "dr",
      "prof",
      "professor",
      "sir",
      "lady",
      "herr",
      "frau",
      "doktor",
      "ing",
  }
  words = name.split()
  while words and words[0] in titles:
    words.pop(0)
  if not words:
    return ""
  filtered_words = []
  for i, w in enumerate(words):
    if len(w) == 1 and len(words) > 1:
      continue
    filtered_words.append(w)
  return " ".join(filtered_words)


input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/dedup_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

c_email = [clean_email(e) for e in df["email"]]
c_name = [clean_name(n) for n in df["full_name"]]
country = [
    "" if pd.isna(c) else str(c).lower().strip()
    for c in df.get("country", [""] * len(df))
]

n = len(df)
dsu = DSU(n)

email_map = {}
for i, e in enumerate(c_email):
  if e:
    if e in email_map:
      dsu.union(i, email_map[e])
    else:
      email_map[e] = i

name_map = {}
for i, name in enumerate(c_name):
  if name:
    if name in name_map:
      prev_i = name_map[name]
      if (
          not country[i]
          or not country[prev_i]
          or country[i] == country[prev_i]
      ):
        dsu.union(i, prev_i)
    else:
      name_map[name] = i

blocks = {}
for i in range(n):
  nm = c_name[i]
  cnt = country[i]
  key = (cnt, nm[0] if nm else "")
  blocks.setdefault(key, []).append(i)

for key, indices in blocks.items():
  m = len(indices)
  for idx1 in range(m):
    i = indices[idx1]
    for idx2 in range(idx1 + 1, m):
      j = indices[idx2]
      if dsu.find(i) == dsu.find(j):
        continue
      nm1, nm2 = c_name[i], c_name[j]
      if not nm1 or not nm2:
        continue
      ratio = difflib.SequenceMatcher(None, nm1, nm2).ratio()
      if ratio >= 0.82:
        dsu.union(i, j)

df["_group_id"] = [dsu.find(i) for i in range(n)]

df = df.sort_values(by="customer_id", ascending=True)
df = df.drop_duplicates(subset=["_group_id"], keep="first")
df = df.drop(columns=["_group_id"])

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)