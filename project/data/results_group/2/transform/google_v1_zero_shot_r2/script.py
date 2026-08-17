import os
import pandas as pd

products_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
orders_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
customers_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/transform/google_v1_zero_shot_r2/output.parquet"

products = pd.read_csv(products_path)
orders = pd.read_csv(orders_path)
customers = pd.read_parquet(customers_path)

def clean_price(val):
    if pd.isna(val):
        return None
    val_str = str(val).replace('€', '').replace('EUR', '').strip()
    val_str = val_str.replace(',', '.')
    return float(val_str)

products['price_eur'] = products['price_eur'].apply(clean_price)

def clean_bool(val):
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in ['ja', 'true', '1', 'yes']:
        return True
    elif s in ['nein', 'false', '0', 'no']:
        return False
    return None

products['in_stock'] = products['in_stock'].apply(clean_bool).astype('boolean')

orders['total_eur'] = orders['quantity'] * orders['unit_price_eur']
ordered_dt = pd.to_datetime(orders['ordered_at'])
orders['order_year'] = ordered_dt.dt.year.astype('Int64')
orders['order_month'] = ordered_dt.dt.month.astype('Int64')

customers = customers.rename(columns={'country': 'country_code'})

merged = orders.merge(customers, on='customer_id', how='inner')
merged = merged.merge(products, on='product_id', how='inner')

merged = merged[merged['country_code'].notna() & (merged['country_code'].astype(str).str.strip() != '')]
merged = merged[merged['category'].notna() & (merged['category'].astype(str).str.strip() != '')]

agg = merged.groupby(['country_code', 'category'], as_index=False).agg(
    total_revenue_eur=('total_eur', 'sum'),
    order_count=('order_id', 'count')
)

agg = agg.sort_values(by='total_revenue_eur', ascending=False)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
agg.to_parquet(output_path, index=False)