# Step-by-step ETL Pipeline for Customer Data Cleaning
# Sub-step 1: Read input CSV, strip leading/trailing whitespace from string columns, and replace missing values in 'country' with 'UNKNOWN'.
# Sub-step 2: Normalize the 'registered_at' column to ISO format YYYY-MM-DD handling mixed formats (ISO, German DD.MM.YYYY, US Month DD YYYY, Unix timestamps).
# Sub-step 3: Standardize the 'country' column to ISO-3166-1-alpha-2 codes (German/English names, abbreviations, 2/3 letter codes mapped to 2 letter ISO codes, unresolvable values set to 'UNKNOWN').
# Sub-step 4: Write the processed DataFrame to the specified Parquet output file location.

import os
import pandas as pd

# Define input and output file paths
input_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/google_v3_chain_of_thought_r2/output.parquet"

# --- STEP 1: Load Data & Clean String Whitespace / Missing Country Values ---
# Load CSV file
df = pd.read_csv(input_file, dtype=str)

# Ensure customer_id maintains integer type as in raw schema definition if needed, or parse clean text
# Strip leading and trailing whitespace from all text/string columns
for col in df.columns:
    df[col] = df[col].astype(str).str.strip()
    # Convert 'nan' or empty string representations back to actual NA / missing where appropriate
    df[col] = df[col].replace({'nan': None, 'None': None, '<NA>': None, '': None})

# Convert customer_id back to int64
if 'customer_id' in df.columns:
    df['customer_id'] = pd.to_numeric(df['customer_id'], errors='coerce').astype('int64')

# Replace missing values in 'country' with 'UNKNOWN'
df['country'] = df['country'].fillna('UNKNOWN')


# --- STEP 2: Normalize 'registered_at' to ISO Format YYYY-MM-DD ---
def parse_registered_at(val):
    if pd.isna(val) or val is None or str(val).strip() == '':
        return None
    val_str = str(val).strip()
    
    # 1. Check if value is a Unix timestamp (numeric, in seconds)
    try:
        num = float(val_str)
        # Check reasonable range for epoch timestamp in seconds (e.g. year 1973 to 2100)
        if num > 100000000:
            return pd.to_datetime(num, unit='s', utc=True).strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        pass

    # 2. Check German date format DD.MM.YYYY
    if '.' in val_str:
        try:
            dt = pd.to_datetime(val_str, format='%d.%m.%Y', errors='coerce')
            if pd.notna(dt):
                return dt.strftime('%Y-%m-%d')
        except Exception:
            pass

    # 3. Fallback to general pd.to_datetime parsing (handles ISO YYYY-MM-DD, US format 'Month DD YYYY', etc.)
    try:
        dt = pd.to_datetime(val_str, errors='coerce')
        if pd.notna(dt):
            return dt.strftime('%Y-%m-%d')
    except Exception:
        pass

    return val_str

df['registered_at'] = df['registered_at'].apply(parse_registered_at)


# --- STEP 3: Standardize 'country' to ISO-3166-1-alpha-2 ---
# Comprehensive mapping for German & English country names, 3-letter codes, and abbreviations
COUNTRY_MAP = {
    'DEUTSCHLAND': 'DE', 'GERMANY': 'DE', 'DEU': 'DE', 'DE': 'DE', 'BRD': 'DE',
    'ÖSTERREICH': 'AT', 'OESTERREICH': 'AT', 'AUSTRIA': 'AT', 'AUT': 'AT', 'AT': 'AT',
    'SCHWEIZ': 'CH', 'SWITZERLAND': 'CH', 'CHE': 'CH', 'CH': 'CH',
    'VEREINIGTE STAATEN': 'US', 'UNITED STATES': 'US', 'UNITED STATES OF AMERICA': 'US', 'USA': 'US', 'US': 'US',
    'VEREINIGTES KÖNIGREICH': 'GB', 'UNITED KINGDOM': 'GB', 'GREAT BRITAIN': 'GB', 'GBR': 'GB', 'GB': 'GB', 'UK': 'GB',
    'FRANKREICH': 'FR', 'FRANCE': 'FR', 'FRA': 'FR', 'FR': 'FR',
    'ITALIEN': 'IT', 'ITALY': 'IT', 'ITA': 'IT', 'IT': 'IT',
    'SPANIEN': 'ES', 'SPAIN': 'ES', 'ESP': 'ES', 'ES': 'ES',
    'NIEDERLANDE': 'NL', 'NETHERLANDS': 'NL', 'HOLLAND': 'NL', 'NLD': 'NL', 'NL': 'NL',
    'POLEN': 'PL', 'POLAND': 'PL', 'POL': 'PL', 'PL': 'PL',
    'BELGIEN': 'BE', 'BELGIUM': 'BE', 'BEL': 'BE', 'BE': 'BE',
    'SCHWEDEN': 'SE', 'SWEDEN': 'SE', 'SWE': 'SE', 'SE': 'SE',
    'NORWEGEN': 'NO', 'NORWAY': 'NO', 'NOR': 'NO', 'NO': 'NO',
    'FINNLAND': 'FI', 'FINLAND': 'FI', 'FIN': 'FI', 'FI': 'FI',
    'DÄNEMARK': 'DK', 'DAENEMARK': 'DK', 'DENMARK': 'DK', 'DNK': 'DK', 'DK': 'DK',
    'IRLAND': 'IE', 'IRELAND': 'IE', 'IRL': 'IE', 'IE': 'IE',
    'PORTUGAL': 'PT', 'PRT': 'PT', 'PT': 'PT',
    'KANADA': 'CA', 'CANADA': 'CA', 'CAN': 'CA', 'CA': 'CA',
    'AUSTRALIEN': 'AU', 'AUSTRALIA': 'AU', 'AUS': 'AU', 'AU': 'AU',
    'CHINA': 'CN', 'CHN': 'CN', 'CN': 'CN',
    'JAPAN': 'JP', 'JPN': 'JP', 'JP': 'JP',
    'INDIEN': 'IN', 'INDIA': 'IN', 'IND': 'IN', 'IN': 'IN',
    'BRASILIEN': 'BR', 'BRAZIL': 'BR', 'BRA': 'BR', 'BR': 'BR',
    'RUSSLAND': 'RU', 'RUSSIA': 'RU', 'RUS': 'RU', 'RU': 'RU',
    'TÜRKEI': 'TR', 'TUERKEI': 'TR', 'TURKEY': 'TR', 'TUR': 'TR', 'TR': 'TR',
    'GRIECHENLAND': 'GR', 'GREECE': 'GR', 'GRC': 'GR', 'GR': 'GR',
    'TSCHECHIEN': 'CZ', 'TSCHECHISCHE REPUBLIK': 'CZ', 'CZECH REPUBLIC': 'CZ', 'CZECHIA': 'CZ', 'CZE': 'CZ', 'CZ': 'CZ',
    'UNGARN': 'HU', 'HUNGARY': 'HU', 'HUN': 'HU', 'HU': 'HU',
    'RUMÄNIEN': 'RO', 'RUMAENIEN': 'RO', 'ROMANIA': 'RO', 'ROU': 'RO', 'RO': 'RO'
}

# Optional dynamic pycountry support if available
try:
    import pycountry
    has_pycountry = True
except ImportError:
    has_pycountry = False

def standardize_country(val):
    if pd.isna(val) or val is None:
        return 'UNKNOWN'
    
    clean_val = str(val).strip().upper()
    if not clean_val or clean_val == 'UNKNOWN':
        return 'UNKNOWN'
    
    # Check explicit mapping dict first
    if clean_val in COUNTRY_MAP:
        return COUNTRY_MAP[clean_val]
    
    # Use pycountry lookup if available
    if has_pycountry:
        try:
            c = pycountry.countries.get(alpha_2=clean_val)
            if c:
                return c.alpha_2
        except Exception:
            pass
        try:
            c = pycountry.countries.get(alpha_3=clean_val)
            if c:
                return c.alpha_2
        except Exception:
            pass
        try:
            c = pycountry.countries.lookup(clean_val)
            if c:
                return c.alpha_2
        except Exception:
            pass

    # If 2 alpha characters and no other match, assume valid alpha-2 code
    if len(clean_val) == 2 and clean_val.isalpha():
        return clean_val

    return 'UNKNOWN'

df['country'] = df['country'].apply(standardize_country)


# --- STEP 4: Save Output to Parquet ---
# Create directory structure if it does not exist
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# Select and write required columns
output_cols = ['customer_id', 'full_name', 'email', 'country', 'registered_at']
df[output_cols].to_parquet(output_file, index=False)