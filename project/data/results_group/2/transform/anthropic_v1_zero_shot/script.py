import pandas as pd
import re

products_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
orders_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
customers_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/transform/anthropic_v1_zero_shot/output.parquet"

products = pd.read_csv(products_path)
orders = pd.read_csv(orders_path)
customers = pd.read_parquet(customers_path)

# Step 1: convert price_eur to float
def parse_price(val):
    if pd.isna(val):
        return None
    s = str(val)
    s = re.sub(r'[^0-9,.\-]', '', s)
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '')
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None

products['price_eur'] = products['price_eur'].apply(parse_price)

def parse_bool(val):
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    true_vals = {'ja', 'true', '1', 'yes', 'y', 'wahr'}
    false_vals = {'nein', 'false', '0', 'no', 'n', 'falsch'}
    if s in true_vals:
        return True
    if s in false_vals:
        return False
    return None

products['in_stock'] = products['in_stock'].apply(parse_bool)

# Step 2: calculate total_eur, order_year, order_month
orders['total_eur'] = orders['quantity'] * orders['unit_price_eur']

orders['ordered_at_parsed'] = pd.to_datetime(orders['ordered_at'], errors='coerce', utc=True)
orders['order_year'] = orders['ordered_at_parsed'].dt.year.astype('Int64')
orders['order_month'] = orders['ordered_at_parsed'].dt.month.astype('Int64')

# Step 3: join tables
customers['country_code'] = customers['country']

merged = orders.merge(customers, on='customer_id', how='inner')
merged = merged.merge(products, on='product_id', how='inner')

merged = merged.dropna(subset=['country_code', 'category'])
merged = merged[merged['country_code'].astype(str).str.strip() != '']
merged = merged[merged['category'].astype(str).str.strip() != '']

merged['revenue'] = merged['quantity'] * merged['unit_price_eur']

result = merged.groupby(['country_code', 'category'], as_index=False).agg(
    total_revenue_eur=('revenue', 'sum'),
    order_count=('order_id', 'count')
)

result = result.sort_values('total_revenue_eur', ascending=False).reset_index(drop=True)

result.to_parquet(output_path, index=False)