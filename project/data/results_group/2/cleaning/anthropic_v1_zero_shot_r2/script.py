import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/anthropic_v1_zero_shot_r2/output.parquet"

df = pd.read_csv(input_path, dtype={'customer_id': 'int64'})

# Step 1: Trim whitespace in text columns, fill missing country with 'UNKNOWN'
text_cols = df.select_dtypes(include=['object']).columns.tolist()
for col in text_cols:
    df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

if 'country' in df.columns:
    df['country'] = df['country'].replace('', np.nan)
    if hasattr(pd, 'NA'):
        df['country'] = df['country'].where(df['country'].notna(), 'UNKNOWN')
    else:
        df['country'] = df['country'].fillna('UNKNOWN')
    df['country'] = df['country'].fillna('UNKNOWN')

# Step 2: Normalize registered_at to ISO format YYYY-MM-DD
def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == '' or s.lower() == 'nan':
        return None

    # Try Unix timestamp (numeric, seconds)
    if re.fullmatch(r'-?\d+(\.\d+)?', s):
        try:
            num = float(s)
            dt = datetime(1970, 1, 1) + timedelta(seconds=num)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            pass

    # Try ISO format YYYY-MM-DD
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return dt.strftime('%Y-%m-%d')
        except Exception:
            pass

    # Try German format TT.MM.JJJJ
    m = re.fullmatch(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', s)
    if m:
        try:
            dt = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            return dt.strftime('%Y-%m-%d')
        except Exception:
            pass

    # Try US format 'Month DD YYYY' (e.g. 'January 05 2020')
    for fmt in ('%B %d %Y', '%b %d %Y', '%B %d, %Y', '%b %d, %Y'):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            continue

    # Fallback: try pandas to_datetime
    try:
        dt = pd.to_datetime(s, errors='raise')
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return None

df['registered_at'] = df['registered_at'].apply(normalize_date)

# Step 3: Normalize country to ISO-3166-1 alpha-2 code
country_map = {
    # Germany
    'DE': 'DE', 'GER': 'DE', 'GERMANY': 'DE', 'DEUTSCHLAND': 'DE', 'ALLEMAGNE': 'DE',
    # Austria
    'AT': 'AT', 'AUT': 'AT', 'AUSTRIA': 'AT', 'OESTERREICH': 'AT', 'ÖSTERREICH': 'AT',
    # Switzerland
    'CH': 'CH', 'CHE': 'CH', 'SWITZERLAND': 'CH', 'SCHWEIZ': 'CH', 'SUISSE': 'CH',
    # USA
    'US': 'US', 'USA': 'US', 'UNITED STATES': 'US', 'UNITED STATES OF AMERICA': 'US',
    'VEREINIGTE STAATEN': 'US', 'AMERICA': 'US',
    # UK
    'UK': 'GB', 'GB': 'GB', 'GBR': 'GB', 'UNITED KINGDOM': 'GB', 'GROSSBRITANNIEN': 'GB',
    'GROßBRITANNIEN': 'GB', 'ENGLAND': 'GB', 'GREAT BRITAIN': 'GB',
    # France
    'FR': 'FR', 'FRA': 'FR', 'FRANCE': 'FR', 'FRANKREICH': 'FR',
    # Italy
    'IT': 'IT', 'ITA': 'IT', 'ITALY': 'IT', 'ITALIEN': 'IT', 'ITALIA': 'IT',
    # Spain
    'ES': 'ES', 'ESP': 'ES', 'SPAIN': 'ES', 'SPANIEN': 'ES', 'ESPANA': 'ES', 'ESPAÑA': 'ES',
    # Netherlands
    'NL': 'NL', 'NLD': 'NL', 'NETHERLANDS': 'NL', 'NIEDERLANDE': 'NL', 'HOLLAND': 'NL',
    # Belgium
    'BE': 'BE', 'BEL': 'BE', 'BELGIUM': 'BE', 'BELGIEN': 'BE',
    # Poland
    'PL': 'PL', 'POL': 'PL', 'POLAND': 'PL', 'POLEN': 'PL',
    # Portugal
    'PT': 'PT', 'PRT': 'PT', 'PORTUGAL': 'PT',
    # Sweden
    'SE': 'SE', 'SWE': 'SE', 'SWEDEN': 'SE', 'SCHWEDEN': 'SE',
    # Norway
    'NO': 'NO', 'NOR': 'NO', 'NORWAY': 'NO', 'NORWEGEN': 'NO',
    # Denmark
    'DK': 'DK', 'DNK': 'DK', 'DENMARK': 'DK', 'DAENEMARK': 'DK', 'DÄNEMARK': 'DK',
    # Finland
    'FI': 'FI', 'FIN': 'FI', 'FINLAND': 'FI', 'FINNLAND': 'FI',
    # Ireland
    'IE': 'IE', 'IRL': 'IE', 'IRELAND': 'IE', 'IRLAND': 'IE',
    # Luxembourg
    'LU': 'LU', 'LUX': 'LU', 'LUXEMBOURG': 'LU', 'LUXEMBURG': 'LU',
    # Czech Republic
    'CZ': 'CZ', 'CZE': 'CZ', 'CZECH REPUBLIC': 'CZ', 'TSCHECHIEN': 'CZ',
    # Greece
    'GR': 'GR', 'GRC': 'GR', 'GREECE': 'GR', 'GRIECHENLAND': 'GR',
    # Hungary
    'HU': 'HU', 'HUN': 'HU', 'HUNGARY': 'HU', 'UNGARN': 'HU',
    # Canada
    'CA': 'CA', 'CAN': 'CA', 'CANADA': 'CA', 'KANADA': 'CA',
    # Australia
    'AU': 'AU', 'AUS': 'AU', 'AUSTRALIA': 'AU', 'AUSTRALIEN': 'AU',
    # China
    'CN': 'CN', 'CHN': 'CN', 'CHINA': 'CN',
    # Japan
    'JP': 'JP', 'JPN': 'JP', 'JAPAN': 'JP',
    # India
    'IN': 'IN', 'IND': 'IN', 'INDIA': 'IN', 'INDIEN': 'IN',
    # Brazil
    'BR': 'BR', 'BRA': 'BR', 'BRAZIL': 'BR', 'BRASILIEN': 'BR',
    # Russia
    'RU': 'RU', 'RUS': 'RU', 'RUSSIA': 'RU', 'RUSSLAND': 'RU',
    # Turkey
    'TR': 'TR', 'TUR': 'TR', 'TURKEY': 'TR', 'TUERKEI': 'TR', 'TÜRKEI': 'TR',
    # Mexico
    'MX': 'MX', 'MEX': 'MX', 'MEXICO': 'MX', 'MEXIKO': 'MX',
    # South Korea
    'KR': 'KR', 'KOR': 'KR', 'SOUTH KOREA': 'KR', 'SUEDKOREA': 'KR', 'SÜDKOREA': 'KR',
    'UNKNOWN': 'UNKNOWN',
}

def normalize_country(val):
    if pd.isna(val):
        return 'UNKNOWN'
    s = str(val).strip().upper()
    if s == '' or s == 'NAN':
        return 'UNKNOWN'
    if s in country_map:
        return country_map[s]
    return 'UNKNOWN'

df['country'] = df['country'].apply(normalize_country)

df.to_parquet(output_path, index=False)