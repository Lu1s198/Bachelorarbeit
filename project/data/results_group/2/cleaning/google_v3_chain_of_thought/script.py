# ETL Task Implementation using Pandas
# Step breakdown:
# 1. Read input data, strip leading/trailing whitespaces from text columns, and replace missing values in 'country' with 'UNKNOWN'.
# 2. Normalize 'registered_at' dates (mixed formats: ISO, German DD.MM.YYYY, US 'Month DD YYYY', Unix timestamps) to ISO YYYY-MM-DD format.
# 3. Standardize 'country' values to two-letter ISO 3166-1 alpha-2 codes (handling German/English names and abbreviations, falling back to 'UNKNOWN').
# 4. Save the cleaned dataframe to the target Parquet destination.

import os
import pandas as pd
from dateutil import parser

# Define file paths
input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/google_v3_chain_of_thought/output.parquet"

# Read input CSV file
df = pd.read_csv(input_path)

# --- Step 1: Strip whitespaces from text columns and fill missing country values ---
# Strip whitespace for all text/object columns while preserving actual null values
for col in df.select_dtypes(include=['object', 'string']).columns:
    df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

# Fill missing/empty country values with 'UNKNOWN'
df['country'] = df['country'].fillna('UNKNOWN')
df['country'] = df['country'].replace({'': 'UNKNOWN'})


# --- Step 2: Normalize registered_at to ISO YYYY-MM-DD format ---
def parse_to_iso_date(val):
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ['nan', 'none', 'null', 'nat', '']:
        return None

    # Check for Unix timestamp in seconds (numeric float or integer string)
    try:
        num_val = float(val_str)
        # Plausible Unix timestamp range in seconds (e.g. 1970 to 2100)
        if 0 < num_val < 4102444800 and not (len(val_str) == 8 and val_str.isdigit()):
            return pd.to_datetime(num_val, unit='s').strftime('%Y-%m-%d')
    except ValueError:
        pass

    # Handle German date format (DD.MM.YYYY) vs standard parsing
    is_german = '.' in val_str
    try:
        dt = pd.to_datetime(val_str, dayfirst=is_german)
        if not pd.isna(dt):
            return dt.strftime('%Y-%m-%d')
    except Exception:
        pass

    # Fallback parsing with dateutil parser
    try:
        dt = parser.parse(val_str)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return None

df['registered_at'] = df['registered_at'].apply(parse_to_iso_date)


# --- Step 3: Standardize country to 2-letter ISO 3166-1 alpha-2 codes ---
# Comprehensive mapping dictionary for common German and English names, abbreviations, and codes
COUNTRY_MAP = {
    # Germany
    'DE': 'DE', 'DEU': 'DE', 'GER': 'DE', 'GERMANY': 'DE', 'DEUTSCHLAND': 'DE', 'DEUTSCH': 'DE',
    # United States
    'US': 'US', 'USA': 'US', 'UNITED STATES': 'US', 'UNITED STATES OF AMERICA': 'US', 'VEREINIGTE STAATEN': 'US', 'AMERICA': 'US',
    # United Kingdom
    'GB': 'GB', 'GBR': 'GB', 'UK': 'GB', 'UNITED KINGDOM': 'GB', 'GREAT BRITAIN': 'GB', 'GROSSBRITANNIEN': 'GB', 'GROßBRITANNIEN': 'GB', 'ENGLAND': 'GB',
    # Austria
    'AT': 'AT', 'AUT': 'AT', 'AUSTRIA': 'AT', 'ÖSTERREICH': 'AT', 'OESTERREICH': 'AT',
    # Switzerland
    'CH': 'CH', 'CHE': 'CH', 'SWITZERLAND': 'CH', 'SCHWEIZ': 'CH',
    # France
    'FR': 'FR', 'FRA': 'FR', 'FRANCE': 'FR', 'FRANKREICH': 'FR',
    # Spain
    'ES': 'ES', 'ESP': 'ES', 'SPAIN': 'ES', 'SPANIEN': 'ES',
    # Italy
    'IT': 'IT', 'ITA': 'IT', 'ITALY': 'IT', 'ITALIEN': 'IT',
    # Netherlands
    'NL': 'NL', 'NLD': 'NL', 'NETHERLANDS': 'NL', 'NIEDERLANDE': 'NL', 'HOLLAND': 'NL',
    # Canada
    'CA': 'CA', 'CAN': 'CA', 'CANADA': 'CA', 'KANADA': 'CA',
    # Australia
    'AU': 'AU', 'AUS': 'AU', 'AUSTRALIA': 'AU', 'AUSTRALIEN': 'AU',
    # Poland
    'PL': 'PL', 'POL': 'PL', 'POLAND': 'PL', 'POLEN': 'PL',
    # Belgium
    'BE': 'BE', 'BEL': 'BE', 'BELGIUM': 'BE', 'BELGIEN': 'BE',
    # Sweden
    'SE': 'SE', 'SWE': 'SE', 'SWEDEN': 'SE', 'SCHWEDEN': 'SE',
    # Norway
    'NO': 'NO', 'NOR': 'NO', 'NORWAY': 'NO', 'NORWEGEN': 'NO',
    # Denmark
    'DK': 'DK', 'DNK': 'DK', 'DENMARK': 'DK', 'DÄNEMARK': 'DK', 'DAENEMARK': 'DK',
    # Finland
    'FI': 'FI', 'FIN': 'FI', 'FINLAND': 'FI', 'FINNLAND': 'FI',
    # Portugal
    'PT': 'PT', 'PRT': 'PT', 'PORTUGAL': 'PT',
    # Ireland
    'IE': 'IE', 'IRL': 'IE', 'IRELAND': 'IE', 'IRLAND': 'IE',
    # Russia
    'RU': 'RU', 'RUS': 'RU', 'RUSSIA': 'RU', 'RUSSLAND': 'RU',
    # China
    'CN': 'CN', 'CHN': 'CN', 'CHINA': 'CN',
    # Japan
    'JP': 'JP', 'JPN': 'JP', 'JAPAN': 'JP',
    # India
    'IN': 'IN', 'IND': 'IN', 'INDIA': 'IN', 'INDIEN': 'IN',
    # Brazil
    'BR': 'BR', 'BRA': 'BR', 'BRAZIL': 'BR', 'BRASILIEN': 'BR',
    # Mexico
    'MX': 'MX', 'MEX': 'MX', 'MEXICO': 'MX', 'MEXIKO': 'MX',
}

def standardize_country(val):
    if pd.isna(val) or val is None:
        return 'UNKNOWN'
    val_clean = str(val).strip().upper()
    if not val_clean or val_clean in ['UNKNOWN', 'NAN', 'NONE', 'NULL', 'N/A', 'NA', '?']:
        return 'UNKNOWN'
    
    # Lookup in custom mapping dictionary
    if val_clean in COUNTRY_MAP:
        return COUNTRY_MAP[val_clean]
    
    # Optional dynamic lookup using pycountry if available
    try:
        import pycountry
        c = pycountry.countries.get(alpha_2=val_clean) or pycountry.countries.get(alpha_3=val_clean) or pycountry.countries.get(name=val_clean)
        if c:
            return c.alpha_2
        matches = pycountry.countries.search_fuzzy(val_clean)
        if matches:
            return matches[0].alpha_2
    except Exception:
        pass

    return 'UNKNOWN'

df['country'] = df['country'].apply(standardize_country)

# Ensure parent directory exists and save output to Parquet
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)