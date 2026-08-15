import os
import re
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/_reference/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google_isolated/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    'de': 'DE', 'deu': 'DE', 'ger': 'DE', 'germany': 'DE', 'deutschland': 'DE',
    'us': 'US', 'usa': 'US', 'united states': 'US', 'united states of america': 'US', 'vereinigte staaten': 'US', 'america': 'US',
    'gb': 'GB', 'uk': 'GB', 'gbr': 'GB', 'great britain': 'GB', 'grossbritannien': 'GB', 'großbritannien': 'GB', 'united kingdom': 'GB', 'england': 'GB',
    'fr': 'FR', 'fra': 'FR', 'france': 'FR', 'frankreich': 'FR',
    'it': 'IT', 'ita': 'IT', 'italy': 'IT', 'italien': 'IT',
    'es': 'ES', 'esp': 'ES', 'spain': 'ES', 'spanien': 'ES',
    'at': 'AT', 'aut': 'AT', 'austria': 'AT', 'österreich': 'AT', 'oesterreich': 'AT',
    'ch': 'CH', 'che': 'CH', 'switzerland': 'CH', 'schweiz': 'CH',
    'nl': 'NL', 'nld': 'NL', 'netherlands': 'NL', 'niederlande': 'NL', 'holland': 'NL',
    'be': 'BE', 'bel': 'BE', 'belgium': 'BE', 'belgien': 'BE',
    'pl': 'PL', 'pol': 'PL', 'poland': 'PL', 'polen': 'PL',
    'ca': 'CA', 'can': 'CA', 'canada': 'CA', 'kanada': 'CA',
    'au': 'AU', 'aus': 'AU', 'australia': 'AU', 'australien': 'AU',
    'cn': 'CN', 'chn': 'CN', 'china': 'CN',
    'jp': 'JP', 'jpn': 'JP', 'japan': 'JP',
    'in': 'IN', 'ind': 'IN', 'india': 'IN', 'indien': 'IN',
    'br': 'BR', 'bra': 'BR', 'brazil': 'BR', 'brasilien': 'BR',
    'ru': 'RU', 'rus': 'RU', 'russia': 'RU', 'russland': 'RU',
    'mx': 'MX', 'mex': 'MX', 'mexico': 'MX', 'mexiko': 'MX',
    'se': 'SE', 'swe': 'SE', 'sweden': 'SE', 'schweden': 'SE',
    'no': 'NO', 'nor': 'NO', 'norway': 'NO', 'norwegen': 'NO',
    'dk': 'DK', 'dnk': 'DK', 'denmark': 'DK', 'dänemark': 'DK', 'daenemark': 'DK',
    'fi': 'FI', 'fin': 'FI', 'finland': 'FI', 'finnland': 'FI',
    'pt': 'PT', 'prt': 'PT', 'portugal': 'PT',
    'gr': 'GR', 'grc': 'GR', 'greece': 'GR', 'griechenland': 'GR',
    'tr': 'TR', 'tur': 'TR', 'turkey': 'TR', 'türkei': 'TR', 'tuerkei': 'TR',
    'ie': 'IE', 'irl': 'IE', 'ireland': 'IE', 'irland': 'IE',
    'nz': 'NZ', 'nzl': 'NZ', 'new zealand': 'NZ', 'neuseeland': 'NZ',
    'za': 'ZA', 'zaf': 'ZA', 'south africa': 'ZA', 'südafrika': 'ZA', 'suedafrika': 'ZA',
    'ar': 'AR', 'arg': 'AR', 'argentina': 'AR', 'argentinien': 'AR',
    'cl': 'CL', 'chl': 'CL', 'chile': 'CL',
    'co': 'CO', 'col': 'CO', 'colombia': 'CO', 'kolumbien': 'CO',
    'cz': 'CZ', 'cze': 'CZ', 'czech republic': 'CZ', 'czechia': 'CZ', 'tschechien': 'CZ',
    'hu': 'HU', 'hun': 'HU', 'hungary': 'HU', 'ungarn': 'HU',
    'ro': 'RO', 'rou': 'RO', 'romania': 'RO', 'rumänien': 'RO', 'rumaenien': 'RO',
    'sk': 'SK', 'svk': 'SK', 'slovakia': 'SK', 'slowakei': 'SK',
    'si': 'SI', 'svn': 'SI', 'slovenia': 'SI', 'slowenien': 'SI',
    'hr': 'HR', 'hrv': 'HR', 'croatia': 'HR', 'kroatien': 'HR',
    'bg': 'BG', 'bgr': 'BG', 'bulgaria': 'BG', 'bulgarien': 'BG',
    'lu': 'LU', 'lux': 'LU', 'luxembourg': 'LU', 'luxemburg': 'LU',
    'li': 'LI', 'lie': 'LI', 'liechtenstein': 'LI',
    'is': 'IS', 'isl': 'IS', 'iceland': 'IS', 'island': 'IS',
    'ua': 'UA', 'ukr': 'UA', 'ukraine': 'UA',
    'kr': 'KR', 'kor': 'KR', 'south korea': 'KR', 'südkorea': 'KR', 'suedkorea': 'KR', 'korea': 'KR',
    'sg': 'SG', 'sgp': 'SG', 'singapore': 'SG', 'singapur': 'SG',
    'ae': 'AE', 'are': 'AE', 'uae': 'AE', 'united arab emirates': 'AE', 'vereinigte arabische emirate': 'AE',
    'sa': 'SA', 'sau': 'SA', 'saudi arabia': 'SA', 'saudi-arabien': 'SA',
    'eg': 'EG', 'egy': 'EG', 'egypt': 'EG', 'ägypten': 'EG', 'aegypten': 'EG',
    'th': 'TH', 'tha': 'TH', 'thailand': 'TH',
    'vn': 'VN', 'vnm': 'VN', 'vietnam': 'VN',
    'id': 'ID', 'idn': 'ID', 'indonesia': 'ID', 'indonesien': 'ID',
    'ph': 'PH', 'phl': 'PH', 'philippines': 'PH', 'philippinen': 'PH',
    'my': 'MY', 'mys': 'MY', 'malaysia': 'MY',
    'il': 'IL', 'isr': 'IL', 'israel': 'IL',
    'ee': 'EE', 'est': 'EE', 'estonia': 'EE', 'estland': 'EE',
    'lv': 'LV', 'lva': 'LV', 'latvia': 'LV', 'lettland': 'LV',
    'lt': 'LT', 'ltu': 'LT', 'lithuania': 'LT', 'litauen': 'LT',
    'cy': 'CY', 'cyp': 'CY', 'cyprus': 'CY', 'zypern': 'CY',
    'mt': 'MT', 'mlt': 'MT', 'malta': 'MT',
}

def clean_country(val):
    if pd.isna(val):
        return 'UNKNOWN'
    val_str = str(val).strip()
    if not val_str:
        return 'UNKNOWN'
    
    low = val_str.lower()
    if low in country_map:
        return country_map[low]
    
    cleaned = re.sub(r'[^a-zA-ZäöüÄÖÜß\s]', '', val_str).strip().lower()
    if cleaned in country_map:
        return country_map[cleaned]
    
    tokens = re.findall(r'[A-Za-z]{2,}', val_str)
    for token in tokens:
        t_low = token.lower()
        if t_low in country_map:
            return country_map[t_low]
            
    return 'UNKNOWN'

df['country'] = df['country'].apply(clean_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)