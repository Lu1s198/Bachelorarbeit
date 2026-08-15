import os
import re
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/google_v1_zero_shot/output.parquet"

df = pd.read_csv(input_path, dtype=str)

if 'customer_id' in df.columns:
    df['customer_id'] = pd.to_numeric(df['customer_id'], errors='coerce').astype('int64')

text_cols = ['full_name', 'email', 'country', 'registered_at']
for col in text_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({'nan': None, 'None': None, '<NA>': None, '': None})

df['country'] = df['country'].fillna('UNKNOWN')

def parse_registered_at(val):
    if pd.isna(val) or val is None or str(val).strip() == '':
        return None
    s = str(val).strip()
    
    try:
        num = float(s)
        if num > 100000000:
            return pd.to_datetime(num, unit='s', utc=True).strftime('%Y-%m-%d')
    except ValueError:
        pass

    if re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}$', s):
        try:
            return pd.to_datetime(s, format='%d.%m.%Y').strftime('%Y-%m-%d')
        except Exception:
            pass

    try:
        dt = pd.to_datetime(s)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        pass

    return None

df['registered_at'] = df['registered_at'].apply(parse_registered_at)

country_map = {
    'DE': 'DE', 'DEU': 'DE', 'GERMANY': 'DE', 'DEUTSCHLAND': 'DE', 'GER': 'DE',
    'AT': 'AT', 'AUT': 'AT', 'AUSTRIA': 'AT', 'ÖSTERREICH': 'AT', 'OESTERREICH': 'AT',
    'CH': 'CH', 'CHE': 'CH', 'SWITZERLAND': 'CH', 'SCHWEIZ': 'CH',
    'US': 'US', 'USA': 'US', 'UNITED STATES': 'US', 'UNITED STATES OF AMERICA': 'US', 'VEREINIGTE STAATEN': 'US',
    'GB': 'GB', 'GBR': 'GB', 'UNITED KINGDOM': 'GB', 'UK': 'GB', 'GROSSBRITANNIEN': 'GB', 'GROßBRITANNIEN': 'GB',
    'FR': 'FR', 'FRA': 'FR', 'FRANCE': 'FR', 'FRANKREICH': 'FR',
    'IT': 'IT', 'ITA': 'IT', 'ITALY': 'IT', 'ITALIEN': 'IT',
    'ES': 'ES', 'ESP': 'ES', 'SPAIN': 'ES', 'SPANIEN': 'ES',
    'NL': 'NL', 'NLD': 'NL', 'NETHERLANDS': 'NL', 'NIEDERLANDE': 'NL',
    'BE': 'BE', 'BEL': 'BE', 'BELGIUM': 'BE', 'BELGIEN': 'BE',
    'PL': 'PL', 'POL': 'PL', 'POLAND': 'PL', 'POLEN': 'PL',
    'CZ': 'CZ', 'CZE': 'CZ', 'CZECH REPUBLIC': 'CZ', 'CZECHIA': 'CZ', 'TSCHECHIEN': 'CZ',
    'DK': 'DK', 'DNK': 'DK', 'DENMARK': 'DK', 'DÄNEMARK': 'DK',
    'SE': 'SE', 'SWE': 'SE', 'SWEDEN': 'SE', 'SCHWEDEN': 'SE',
    'NO': 'NO', 'NOR': 'NO', 'NORWAY': 'NO', 'NORWEGEN': 'NO',
    'FI': 'FI', 'FIN': 'FI', 'FINLAND': 'FI', 'FINNLAND': 'FI',
    'CA': 'CA', 'CAN': 'CA', 'CANADA': 'CA', 'KANADA': 'CA',
    'AU': 'AU', 'AUS': 'AU', 'AUSTRALIA': 'AU', 'AUSTRALIEN': 'AU',
    'JP': 'JP', 'JPN': 'JP', 'JAPAN': 'JP',
    'CN': 'CN', 'CHN': 'CN', 'CHINA': 'CN',
    'IN': 'IN', 'IND': 'IN', 'INDIA': 'IN', 'INDIEN': 'IN',
    'BR': 'BR', 'BRA': 'BR', 'BRAZIL': 'BR', 'BRASILIEN': 'BR',
    'RU': 'RU', 'RUS': 'RU', 'RUSSIA': 'RU', 'RUSSLAND': 'RU',
    'MX': 'MX', 'MEX': 'MX', 'MEXICO': 'MX', 'MEXIKO': 'MX',
    'PT': 'PT', 'PRT': 'PT', 'PORTUGAL': 'PT',
    'GR': 'GR', 'GRC': 'GR', 'GREECE': 'GR', 'GRIECHENLAND': 'GR',
    'IE': 'IE', 'IRL': 'IE', 'IRELAND': 'IE', 'IRLAND': 'IE',
    'TR': 'TR', 'TUR': 'TR', 'TURKEY': 'TR', 'TÜRKEI': 'TR',
}

def map_country(val):
    if pd.isna(val) or not val or val == 'UNKNOWN':
        return 'UNKNOWN'
    val_clean = str(val).strip().upper()
    if val_clean in country_map:
        return country_map[val_clean]
    try:
        import pycountry
        c = pycountry.countries.get(alpha_2=val_clean) or pycountry.countries.get(alpha_3=val_clean) or pycountry.countries.get(name=val_clean)
        if c:
            return c.alpha_2
        res = pycountry.countries.search_fuzzy(val_clean)
        if res:
            return res[0].alpha_2
    except Exception:
        pass
    return 'UNKNOWN'

df['country'] = df['country'].apply(map_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)