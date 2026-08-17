import os
import re
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/google_v1_zero_shot_r2/output.parquet"

df = pd.read_csv(input_path, dtype={'customer_id': 'int64', 'full_name': 'str', 'email': 'str', 'country': 'str', 'registered_at': 'str'})

for col in df.columns:
    if df[col].dtype == 'object' or df[col].dtype == 'string':
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

df['country'] = df['country'].replace({'nan': None, 'NaN': None, 'None': None, '': None})
df['country'] = df['country'].fillna('UNKNOWN')

def normalize_date(val):
    if pd.isna(val) or val is None or str(val).strip() in ['', 'nan', 'None', 'NaN']:
        return None
    val_str = str(val).strip()
    
    if val_str.isdigit() or (val_str.replace('.', '', 1).isdigit() and len(val_str.split('.')[0]) in [9, 10, 11]):
        try:
            ts = float(val_str)
            dt = pd.to_datetime(ts, unit='s', errors='coerce')
            if pd.notna(dt):
                return dt.strftime('%Y-%m-%d')
        except Exception:
            pass

    if re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}', val_str):
        dt = pd.to_datetime(val_str, format='%d.%m.%Y', errors='coerce')
        if pd.notna(dt):
            return dt.strftime('%Y-%m-%d')

    dt = pd.to_datetime(val_str, errors='coerce')
    if pd.notna(dt):
        return dt.strftime('%Y-%m-%d')

    return None

df['registered_at'] = df['registered_at'].apply(normalize_date)

country_map = {
    'DE': 'DE', 'DEU': 'DE', 'GERMANY': 'DE', 'DEUTSCHLAND': 'DE', 'GER': 'DE',
    'AT': 'AT', 'AUT': 'AT', 'AUSTRIA': 'AT', 'ÖSTERREICH': 'AT', 'OESTERREICH': 'AT',
    'CH': 'CH', 'CHE': 'CH', 'SWITZERLAND': 'CH', 'SCHWEIZ': 'CH',
    'US': 'US', 'USA': 'US', 'UNITED STATES': 'US', 'UNITED STATES OF AMERICA': 'US', 'VEREINIGTE STAATEN': 'US', 'VEREINIGTE STAATEN VON AMERIKA': 'US',
    'GB': 'GB', 'GBR': 'GB', 'UK': 'GB', 'UNITED KINGDOM': 'GB', 'GREAT BRITAIN': 'GB', 'GROSSBRITANNIEN': 'GB',
    'FR': 'FR', 'FRA': 'FR', 'FRANCE': 'FR', 'FRANKREICH': 'FR',
    'IT': 'IT', 'ITA': 'IT', 'ITALY': 'IT', 'ITALIEN': 'IT',
    'ES': 'ES', 'ESP': 'ES', 'SPAIN': 'ES', 'SPANIEN': 'ES',
    'NL': 'NL', 'NLD': 'NL', 'NETHERLANDS': 'NL', 'NIEDERLANDE': 'NL', 'HOLLAND': 'NL',
    'BE': 'BE', 'BEL': 'BE', 'BELGIUM': 'BE', 'BELGIEN': 'BE',
    'PL': 'PL', 'POL': 'PL', 'POLAND': 'PL', 'POLEN': 'PL',
    'CA': 'CA', 'CAN': 'CA', 'CANADA': 'CA', 'KANADA': 'CA',
    'AU': 'AU', 'AUS': 'AU', 'AUSTRALIA': 'AU', 'AUSTRALIEN': 'AU',
    'CN': 'CN', 'CHN': 'CN', 'CHINA': 'CN',
    'JP': 'JP', 'JPN': 'JP', 'JAPAN': 'JP',
    'IN': 'IN', 'IND': 'IN', 'INDIA': 'IN', 'INDIEN': 'IN',
    'BR': 'BR', 'BRA': 'BR', 'BRAZIL': 'BR', 'BRASILIEN': 'BR',
    'RU': 'RU', 'RUS': 'RU', 'RUSSIA': 'RU', 'RUSSLAND': 'RU',
    'SE': 'SE', 'SWE': 'SE', 'SWEDEN': 'SE', 'SCHWEDEN': 'SE',
    'DK': 'DK', 'DNK': 'DK', 'DENMARK': 'DK', 'DÄNEMARK': 'DK', 'DAENEMARK': 'DK',
    'NO': 'NO', 'NOR': 'NO', 'NORWAY': 'NO', 'NORWEGEN': 'NO',
    'FI': 'FI', 'FIN': 'FI', 'FINLAND': 'FI', 'FINNLAND': 'FI',
    'PT': 'PT', 'PRT': 'PT', 'PORTUGAL': 'PT',
    'GR': 'GR', 'GRC': 'GR', 'GREECE': 'GR', 'GRIECHENLAND': 'GR',
    'IE': 'IE', 'IRL': 'IE', 'IRELAND': 'IE', 'IRLAND': 'IE',
    'TR': 'TR', 'TUR': 'TR', 'TURKEY': 'TR', 'TÜRKEI': 'TR', 'TUERKEI': 'TR',
    'MX': 'MX', 'MEX': 'MX', 'MEXICO': 'MX', 'MEXIKO': 'MX',
    'UNKNOWN': 'UNKNOWN'
}

def standardize_country(val):
    if pd.isna(val) or val is None:
        return 'UNKNOWN'
    val_clean = str(val).strip().upper()
    return country_map.get(val_clean, 'UNKNOWN')

df['country'] = df['country'].apply(standardize_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)