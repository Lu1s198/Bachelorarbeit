import pandas as pd
import numpy as np
import re

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r2/dedup_hard/output.parquet"

df = pd.read_parquet(input_path)

df['customer_id'] = df['customer_id'].astype('int64')
df['full_name'] = df['full_name'].astype(str)
df['email'] = df['email'].astype(str)
df['country'] = df['country'].astype(str)
df['registered_at'] = df['registered_at'].astype(str)

TITLES = {
    'mr', 'mr.', 'mrs', 'mrs.', 'ms', 'ms.', 'miss', 'dr', 'dr.',
    'prof', 'prof.', 'mx', 'mx.', 'sir', 'madam', 'herr', 'frau',
    'monsieur', 'madame', 'mademoiselle'
}

def normalize_name(name):
    if name is None:
        return ""
    s = str(name).strip().lower()
    s = re.sub(r'[.,]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    tokens = s.split(' ')
    tokens = [t for t in tokens if t not in TITLES]
    filtered = []
    for t in tokens:
        tt = t.strip()
        if len(tt) == 0:
            continue
        if len(tt) == 1:
            continue
        filtered.append(tt)
    return ' '.join(filtered)

def normalize_email(email):
    if email is None:
        return ""
    s = str(email).strip().lower()
    if '@' not in s:
        return s
    local, domain = s.split('@', 1)
    local = local.replace('.', '')
    local = local.split('+')[0]
    return local + '@' + domain

df['norm_name'] = df['full_name'].apply(normalize_name)
df['norm_email'] = df['email'].apply(normalize_email)

df['norm_name'] = df['norm_name'].astype(str)
df['norm_email'] = df['norm_email'].astype(str)

idx = df.groupby(['norm_name', 'norm_email'])['customer_id'].idxmin()

result = df.loc[idx, ['customer_id', 'full_name', 'email', 'country', 'registered_at']].reset_index(drop=True)

result = result.sort_values('customer_id').reset_index(drop=True)

result.to_parquet(output_path, index=False)