import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r2/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r2/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

mapping = {
    'de': 'DE', 'deu': 'DE', 'ger': 'DE', 'germany': 'DE', 'deutschland': 'DE', 'd': 'DE', 'bundesrepublik deutschland': 'DE',
    'at': 'AT', 'aut': 'AT', 'austria': 'AT', 'österreich': 'AT', 'oesterreich': 'AT', 'a': 'AT',
    'ch': 'CH', 'che': 'CH', 'sui': 'CH', 'switzerland': 'CH', 'schweiz': 'CH', 'suisse': 'CH', 'svizzera': 'CH',
    'us': 'US', 'usa': 'US', 'united states': 'US', 'united states of america': 'US', 'vereinigte staaten': 'US', 'vereinigte staaten von amerika': 'US',
    'gb': 'GB', 'gbr': 'GB', 'uk': 'GB', 'united kingdom': 'GB', 'great britain': 'GB', 'großbritannien': 'GB', 'grossbritannien': 'GB', 'england': 'GB',
    'fr': 'FR', 'fra': 'FR', 'france': 'FR', 'frankreich': 'FR',
    'it': 'IT', 'ita': 'IT', 'italy': 'IT', 'italien': 'IT',
    'es': 'ES', 'esp': 'ES', 'spain': 'ES', 'spanien': 'ES',
    'nl': 'NL', 'nld': 'NL', 'netherlands': 'NL', 'niederlande': 'NL', 'holland': 'NL',
    'be': 'BE', 'bel': 'BE', 'belgium': 'BE', 'belgien': 'BE',
    'pl': 'PL', 'pol': 'PL', 'poland': 'PL', 'polen': 'PL',
    'cz': 'CZ', 'cze': 'CZ', 'czech republic': 'CZ', 'czechia': 'CZ', 'tschechien': 'CZ', 'tschechische republik': 'CZ',
    'ca': 'CA', 'can': 'CA', 'canada': 'CA', 'kanada': 'CA',
    'au': 'AU', 'aus': 'AU', 'australia': 'AU', 'australien': 'AU',
    'cn': 'CN', 'chn': 'CN', 'china': 'CN', 'volksrepublik china': 'CN',
    'jp': 'JP', 'jpn': 'JP', 'japan': 'JP',
    'in': 'IN', 'ind': 'IN', 'india': 'IN', 'indien': 'IN',
    'br': 'BR', 'bra': 'BR', 'brazil': 'BR', 'brasilien': 'BR',
    'ru': 'RU', 'rus': 'RU', 'russia': 'RU', 'russland': 'RU', 'russian federation': 'RU',
    'tr': 'TR', 'tur': 'TR', 'turkey': 'TR', 'türkei': 'TR', 'tuerkei': 'TR',
    'se': 'SE', 'swe': 'SE', 'sweden': 'SE', 'schweden': 'SE',
    'no': 'NO', 'nor': 'NO', 'norway': 'NO', 'norwegen': 'NO',
    'dk': 'DK', 'dnk': 'DK', 'denmark': 'DK', 'dänemark': 'DK', 'daenemark': 'DK',
    'fi': 'FI', 'fin': 'FI', 'finland': 'FI', 'finnland': 'FI',
    'pt': 'PT', 'prt': 'PT', 'portugal': 'PT',
    'gr': 'GR', 'grc': 'GR', 'greece': 'GR', 'griechenland': 'GR',
    'ie': 'IE', 'irl': 'IE', 'ireland': 'IE', 'irland': 'IE',
    'lu': 'LU', 'lux': 'LU', 'luxembourg': 'LU', 'luxemburg': 'LU',
    'li': 'LI', 'lie': 'LI', 'liechtenstein': 'LI',
    'mx': 'MX', 'mex': 'MX', 'mexico': 'MX', 'mexiko': 'MX',
    'za': 'ZA', 'zaf': 'ZA', 'south africa': 'ZA', 'südafrika': 'ZA', 'suedafrika': 'ZA',
    'hr': 'HR', 'hrv': 'HR', 'croatia': 'HR', 'kroatien': 'HR',
    'hu': 'HU', 'hun': 'HU', 'hungary': 'HU', 'ungarn': 'HU',
    'ro': 'RO', 'rou': 'RO', 'romania': 'RO', 'rumänien': 'RO', 'rumaenien': 'RO',
    'bg': 'BG', 'bgr': 'BG', 'bulgaria': 'BG', 'bulgarien': 'BG',
    'sk': 'SK', 'svk': 'SK', 'slovakia': 'SK', 'slowakei': 'SK',
    'si': 'SI', 'svn': 'SI', 'slovenia': 'SI', 'slowenien': 'SI',
    'ua': 'UA', 'ukr': 'UA', 'ukraine': 'UA',
    'nz': 'NZ', 'nzl': 'NZ', 'new zealand': 'NZ', 'neuseeland': 'NZ',
    'ar': 'AR', 'arg': 'AR', 'argentina': 'AR', 'argentinien': 'AR',
    'cl': 'CL', 'chl': 'CL', 'chile': 'CL',
    'co': 'CO', 'col': 'CO', 'colombia': 'CO', 'kolumbien': 'CO',
    'eg': 'EG', 'egy': 'EG', 'egypt': 'EG', 'ägypten': 'EG', 'aegypten': 'EG',
    'il': 'IL', 'isr': 'IL', 'israel': 'IL',
    'kr': 'KR', 'kor': 'KR', 'south korea': 'KR', 'südkorea': 'KR', 'suedkorea': 'KR', 'korea': 'KR',
    'th': 'TH', 'tha': 'TH', 'thailand': 'TH',
    'vn': 'VN', 'vnm': 'VN', 'vietnam': 'VN',
    'id': 'ID', 'idn': 'ID', 'indonesia': 'ID', 'indonesien': 'ID',
    'my': 'MY', 'mys': 'MY', 'malaysia': 'MY',
    'sg': 'SG', 'sgp': 'SG', 'singapore': 'SG', 'singapur': 'SG',
    'ph': 'PH', 'phl': 'PH', 'philippines': 'PH', 'philippinen': 'PH',
    'ae': 'AE', 'are': 'AE', 'uae': 'AE', 'united arab emirates': 'AE', 'vereinigte arabische emirate': 'AE',
    'sa': 'SA', 'sau': 'SA', 'saudi arabia': 'SA', 'saudi-arabien': 'SA',
}

def clean_country(val):
    if pd.isna(val):
        return 'UNKNOWN'
    cleaned = str(val).strip().lower()
    return mapping.get(cleaned, 'UNKNOWN')

df['country'] = df['country'].apply(clean_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)