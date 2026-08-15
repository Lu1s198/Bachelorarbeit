import os
import re
import pandas as pd

input_path = r'C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet'
output_path = r'C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r4/dedup_hard/output.parquet'

df = pd.read_parquet(input_path)

TITLES = {
    'mr',
    'mrs',
    'ms',
    'miss',
    'dr',
    'prof',
    'sir',
    'madam',
    'herr',
    'frau',
    'drs',
    'ing',
    'phd',
    'dipl',
}


def normalize_email(email):
  if pd.isna(email) or not email:
    return ''
  email = str(email).strip().lower()
  if '@' in email:
    local, domain = email.split('@', 1)
    local = local.replace('.', '')
    return f'{local}@{domain}'
  return email


def clean_name(name):
  if pd.isna(name) or not name:
    return '', []
  name_str = str(name).lower()
  name_clean = re.sub(r'[^a-z0-9\s]', ' ', name_str)
  tokens = [t for t in name_clean.split() if t not in TITLES]
  tokens_no_initials = [t for t in tokens if len(t) > 1]
  if not tokens_no_initials:
    tokens_no_initials = tokens
  return ' '.join(tokens_no_initials), tokens_no_initials


def levenshtein(s1, s2):
  if len(s1) < len(s2):
    return levenshtein(s2, s1)
  if len(s2) == 0:
    return len(s1)
  previous_row = range(len(s2) + 1)
  for i, c1 in enumerate(s1):
    current_row = [i + 1]
    for j, c2 in enumerate(s2):
      insertions = previous_row[j + 1] + 1
      deletions = current_row[j] + 1
      substitutions = previous_row[j] + (c1 != c2)
      current_row.append(min(insertions, deletions, substitutions))
    previous_row = current_row
  return previous_row[-1]


def is_email_match(e1, e2):
  if not e1 or not e2:
    return False
  if e1 == e2:
    return True
  d = levenshtein(e1, e2)
  max_l = max(len(e1), len(e2))
  return d <= 2 and (d / max_l) <= 0.15


def is_name_match(n_str1, tokens1, n_str2, tokens2):
  if not n_str1 or not n_str2:
    return False
  if n_str1 == n_str2:
    return True

  d = levenshtein(n_str1, n_str2)
  max_l = max(len(n_str1), len(n_str2))
  if d <= 2 or (d / max_l) <= 0.20:
    return True

  if len(tokens1) >= 2 and len(tokens2) >= 2:
    first_d = levenshtein(tokens1[0], tokens2[0])
    last_d = levenshtein(tokens1[-1], tokens2[-1])
    if first_d <= 1 and last_d <= 1:
      return True

  return False


norm_emails = [normalize_email(e) for e in df['email']]
cleaned_names = [clean_name(n) for n in df['full_name']]
norm_name_strs = [cn[0] for cn in cleaned_names]
norm_name_tokens = [cn[1] for cn in cleaned_names]

n = len(df)


class UnionFind:

  def __init__(self, size):
    self.parent = list(range(size))

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


uf = UnionFind(n)

for i in range(n):
  for j in range(i + 1, n):
    if is_email_match(norm_emails[i], norm_emails[j]) and is_name_match(
        norm_name_strs[i],
        norm_name_tokens[i],
        norm_name_strs[j],
        norm_name_tokens[j],
    ):
      uf.union(i, j)

groups = {}
for i in range(n):
  root = uf.find(i)
  if root not in groups:
    groups[root] = []
  groups[root].append(i)

df['customer_id'] = pd.to_numeric(df['customer_id'])
keep_indices = []
for root, indices in groups.items():
  best_idx = min(indices, key=lambda idx: df.iloc[idx]['customer_id'])
  keep_indices.append(best_idx)

result_df = (
    df.iloc[keep_indices].sort_values('customer_id').reset_index(drop=True)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result_df.to_parquet(output_path, index=False)