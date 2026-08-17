import os
import re
import pandas as pd

input_dir = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/google_v1_zero_shot_r2/output.parquet"

customers_df = pd.read_csv(os.path.join(input_dir, "customers_raw.csv"))

for col in customers_df.select_dtypes(include=['object', 'string']).columns:
    customers_df[col] = customers_df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

country_map = {
    'DEUTSCHLAND': 'DE', 'GERMANY': 'DE', 'GER': 'DE', 'DEUTSHCLAND': 'DE', 'DE': 'DE', 'ALLEMAGNE': 'DE', 'DEUTSCHLANDS': 'DE',
    'OESTERREICH': 'AT', 'ÖSTERREICH': 'AT', 'AUSTRIA': 'AT', 'AUT': 'AT', 'AT': 'AT', 'AUTRICHE': 'AT',
    'SCHWEIZ': 'CH', 'SWITZERLAND': 'CH', 'CHE': 'CH', 'CH': 'CH', 'SUISSE': 'CH', 'SVIZZERA': 'CH',
    'FRANKREICH': 'FR', 'FRANCE': 'FR', 'FRA': 'FR', 'FR': 'FR',
    'ITALIEN': 'IT', 'ITALY': 'IT', 'ITA': 'IT', 'IT': 'IT', 'ITALIA': 'IT',
    'SPANIEN': 'ES', 'SPAIN': 'ES', 'ESP': 'ES', 'ES': 'ES', 'ESPAÑA': 'ES', 'ESPANA': 'ES',
    'GROSSBRITANNIEN': 'GB', 'UNITED KINGDOM': 'GB', 'UK': 'GB', 'GB': 'GB', 'GBR': 'GB', 'ENGLAND': 'GB',
    'VEREINIGTE STAATEN': 'US', 'UNITED STATES': 'US', 'USA': 'US', 'US': 'US',
    'NIEDERLANDE': 'NL', 'NETHERLANDS': 'NL', 'NL': 'NL', 'NLD': 'NL', 'NEDERLAND': 'NL',
    'POLEN': 'PL', 'POLAND': 'PL', 'PL': 'PL', 'POL': 'PL'
}

def map_country(val):
    if pd.isna(val):
        return 'UNKNOWN'
    val_str = str(val).strip()
    if not val_str or val_str.upper() in ('NAN', 'NONE', 'NULL', 'UNKNOWN'):
        return 'UNKNOWN'
    val_upper = val_str.upper()
    if val_upper in country_map:
        return country_map[val_upper]
    if 'DEUTSH' in val_upper or 'GERM' in val_upper or 'DEUTSCH' in val_upper:
        return 'DE'
    if 'OEST' in val_upper or 'ÖST' in val_upper or 'AUST' in val_upper:
        return 'AT'
    if 'SCHWEIZ' in val_upper or 'SWIT' in val_upper:
        return 'CH'
    if len(val_upper) == 2 and val_upper.isalpha():
        return val_upper
    return 'UNKNOWN'

customers_df['country_code'] = customers_df['country'].apply(map_country)

customers_df = customers_df.drop_duplicates(subset=['customer_id'], keep='first')

products_df = pd.read_csv(os.path.join(input_dir, "products_raw.csv"))

def clean_price(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    cleaned = re.sub(r'[^0-9.,]', '', val_str)
    if ',' in cleaned and '.' in cleaned:
        if cleaned.find(',') < cleaned.find('.'):
            cleaned = cleaned.replace(',', '')
        else:
            cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None

products_df['price_eur'] = products_df['price_eur'].apply(clean_price)

def clean_bool(val):
    if pd.isna(val):
        return False
    val_str = str(val).strip().lower()
    return val_str in ('true', '1', 't', 'yes', 'ja', 'wahr')

products_df['in_stock'] = products_df['in_stock'].apply(clean_bool)

orders_df = pd.read_csv(os.path.join(input_dir, "orders_raw.csv"))

merged_df = orders_df.merge(customers_df, on='customer_id', how='left')
merged_df = merged_df.merge(products_df, on='product_id', how='left')

merged_df['country_code'] = merged_df['country_code'].fillna('UNKNOWN')

merged_df['line_revenue'] = merged_df['quantity'] * merged_df['unit_price_eur']

agg_df = merged_df.groupby(['country_code', 'category'], as_index=False).agg(
    total_revenue_eur=('line_revenue', 'sum'),
    order_count=('order_id', 'count')
)

agg_df['total_revenue_eur'] = agg_df['total_revenue_eur'].round(2)
agg_df = agg_df.sort_values(by='total_revenue_eur', ascending=False).reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
agg_df.to_parquet(output_path, index=False)